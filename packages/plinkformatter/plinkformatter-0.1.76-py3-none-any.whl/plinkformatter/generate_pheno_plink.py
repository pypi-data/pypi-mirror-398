import os
import logging
import re
from typing import List, Optional, Union
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.csv as pv
import numpy as np
from joblib import Parallel, delayed

from plinkformatter.plink_utils import generate_bed_bim_fam, calculate_kinship_matrix
from plinkformatter.utils import validate_files_exist_and_not_empty
from plinkformatter.exceptions import PLINK2Error, PhenotypeMeasureError


# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def generate_map(df: pd.DataFrame, map_file: str) -> None:
    """
    Generates a PLINK-formatted .map file from the provided DataFrame.

    Args:
        df: DataFrame containing genotype information with at least the
            columns ['chr', 'rs', 'bp38'].
        map_file: Path to the output MAP file.

    Returns:
        None. The function writes the .map file to the specified location.
    """
    # Standardize column naming across datasets:
    df["chr"] = df["chr"].astype(str).str.replace("chr", "").str.upper()

    # Replace mitochondrial chromosome if present
    df["chr"] = df["chr"].replace({"M": "26", "MT": "26"})

    # Ensure missing 'rs' values are replaced with a combination of 'chr' and 'bp38'
    df["rs"] = df.apply(
        lambda row: (
            f"{row['chr']}_{row['bp38']}"
            if pd.isna(row["rs"]) or row["rs"] == ""
            else row["rs"]
        ),
        axis=1,
    )

    # Ensure no duplicates based on 'chr', 'rs', 'bp38'
    df = df.drop_duplicates(subset=["chr", "rs", "bp38"])

    # Prepare the map DataFrame with necessary columns and add cM column
    map_df = df[["chr", "rs", "bp38"]].copy()
    map_df.insert(2, "cM", 0)

    # Write to file
    map_df.to_csv(map_file, sep="\t", index=False, header=False)


def apply_transformation(df: pd.DataFrame, reference_col: str) -> pd.DataFrame:
    """
    Applies genotype transformation based on a reference column.

    Transformation rules:
    - If a cell matches the reference column value, set '1 1'.
    - If a cell is 'N', set '0 0'.
    - If a cell is 'H', set '1 2'.
    - Otherwise, set '2 2'.

    Args:
        df: DataFrame containing genotype data to transform.
        reference_col: The column name in df to be used as a reference for
            comparison.

    Returns:
        DataFrame: The transformed DataFrame.
    """
    df_transformed = df.copy()

    # Get the reference column values for comparison
    reference_values = df[reference_col]

    # Apply the condition where the value matches the reference column
    for col in df.columns:
        # If values match the reference column (b_6), set '1 1'
        df_transformed.loc[df[col] == reference_values, col] = "1 1"
        # Set '0 0' for 'N' values
        df_transformed.loc[df[col] == "N", col] = "0 0"
        # Set '1 2' for 'H' values
        df_transformed.loc[df[col] == "H", col] = "1 2"
        # For all other values, set '2 2'
        df_transformed.loc[
            (df[col] != reference_values) & (df[col] != "N") & (df[col] != "H"), col
        ] = "2 2"

    return df_transformed


def generate_ped(df: pd.DataFrame, ped_file: str) -> None:
    """
    Generates a PLINK-formatted .ped file from the given DataFrame.

    Args:
        df: DataFrame containing genotype data with at least an 'observed' column.
        ped_file: Path to the output PED file.

    Returns:
        None. The function writes the .ped file to the specified location.
    """
    # Standardize strain names
    df.columns = df.columns.str.replace(" ", "").str.upper()

    # Find observed column
    index = df.columns.get_loc("observed")
    ped_df = df.iloc[:, (index + 1) :].copy()

    # Rename "C57BL/6J" to "b_6"
    ped_df.rename(columns={"C57BL/6J": "b_6"}, inplace=True)

    # Reference column for comparison
    ref_column = "b_6"

    # Apply genotype transformation row-wise for each column
    ped_df = apply_transformation(ped_df, ref_column)

    # Rename "b_6" back to "C57BL/6J"
    ped_df.rename(columns={"b_6": "C57BL/6J"}, inplace=True)

    # Apply transpose
    ped_df = ped_df.T

    # Add necessary columns for PLINK format
    ped_df.insert(0, "FID", ped_df.index)
    ped_df.insert(1, "IID", ped_df["FID"])
    ped_df.insert(2, "PID", 0)
    ped_df.insert(3, "MID", 0)
    ped_df.insert(4, "SEX", 0)
    ped_df.insert(5, "PHE", -9)

    # Write to file
    ped_df.to_csv(ped_file, sep="\t", index=False, header=False)


def generate_ped_map(
    genotype_df: pd.DataFrame,
    ped_file: str,
    map_file: str,
    gen_map: bool = True,
    gen_ped: bool = True,
) -> None:
    """
    Generates both PLINK-formatted .ped and .map files from a genotype DataFrame.

    Args:
        genotype_df: DataFrame containing genotype data with columns ['chr', 'rs', 'bp38'].
        ped_file: Path to the output PED file.
        map_file: Path to the output MAP file.
        gen_map: Boolean indicating whether to generate the MAP file (default: True).
        gen_ped: Boolean indicating whether to generate the PED file (default: True).

    Returns:
        None. Writes the .ped and/or .map files to the specified locations.
    """
    # Filter DataFrame to exclude mitochondrial chromosomes
    df = genotype_df[genotype_df["chr"] != "M"].copy()

    # Ensure 'chr' and 'bp38' columns are strings for consistent processing
    df["chr"] = df["chr"].astype(str)
    df["bp38"] = df["bp38"].astype(str)

    # Replace missing or empty 'rs' values with concatenated 'chr' and 'bp38'
    df["rs"] = np.where(df["rs"] == "", df["chr"] + "_" + df["bp38"], df["rs"])

    # Drop duplicates based on 'chr', 'rs', and 'bp38' to ensure uniqueness
    df = df.drop_duplicates(subset=["chr", "rs", "bp38"])

    # Generate map file if requested
    if gen_map:
        generate_map(df, map_file)

    # Generate ped file if requested
    if gen_ped:
        generate_ped(df, ped_file)


def extract_pheno_measure(
    directory: str, measure_id: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Extracts phenotype measures from local CSV files in the given directory.

    Args:
        directory: Directory containing CSV files for each measure.
        measure_id: Optional list of measure IDs to extract. If None, no measures will be extracted.

    Returns:
        pd.DataFrame: Concatenated phenotype data from all measure files, or an empty DataFrame if no files are found.
    """
    if measure_id is None:
        measure_id = []

    dat_list = []
    for mid in measure_id:
        try:
            file_path = os.path.join(directory, f"{mid}.csv")
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                dat_list.append(df)
            else:
                print(f"File {file_path} does not exist.")
        except Exception as e:
            raise PhenotypeMeasureError(
                f"Error extracting phenotype for measure {mid}: {e}"
            )

    if not dat_list:
        return pd.DataFrame()

    dat_all = pd.concat(dat_list, ignore_index=True)
    dat_all["strain"] = dat_all["strain"].str.replace(" ", "")
    dat_all["strain"] = dat_all["strain"].apply(
        lambda x: re.sub(r".$", "", x) if x.startswith("CC") else x
    )

    return dat_all


def column_splitter(df: pd.DataFrame, split_index: int = 6) -> pd.DataFrame:
    """
    Splits columns in the DataFrame with the format "2 2" into two separate columns.

    Args:
        df: DataFrame with columns to be split.
        split_index: Index of the first column to split (default: 6).

    Returns:
        pd.DataFrame: DataFrame with split columns.
    """
    # Split the DataFrame into the initial columns and the columns that need splitting
    res = df.iloc[:, :split_index]
    sus = df.iloc[:, split_index:]

    # Create an empty list to store all new columns
    new_columns = []

    # Loop through each column in `sus` and split the values
    for x in sus.columns:
        split_cols = sus[x].str.split(" ", expand=True)
        # Append the split columns to the list
        new_columns.append(split_cols)

    # Concatenate the original columns and the new columns along axis 1
    new_res = pd.concat([res] + new_columns, axis=1)

    # Copy to de-fragment
    new_res = new_res.copy()

    new_res.columns = [i for i, _ in enumerate(new_res.columns)]

    return new_res


def column_splitter_vec(df: pd.DataFrame, split_index: int = 6) -> pd.DataFrame:
    """
    Vectorised version of `column_splitter`.
    Splits every genotype-pair cell like "2 2" into two columns and
    keeps the first `split_index` metadata columns untouched.
    """

    # --- metadata (first 6 cols) ---
    fixed = df.iloc[:, :split_index].to_numpy(dtype=object)

    # --- genotype pairs ---
    geno = df.iloc[:, split_index:].to_numpy(dtype="U3")  # "0 0", "1 2", …

    parts = np.char.partition(geno, " ")  # shape → (rows, pairs, 3)
    first = parts[..., 0]  # left allele
    second = parts[..., 2]  # right allele

    # interleave a1,a2,b1,b2,…  → exactly like the original loop
    rows, n_pairs = first.shape
    merged_pairs = np.empty((rows, n_pairs * 2), dtype=first.dtype)
    merged_pairs[:, 0::2] = first
    merged_pairs[:, 1::2] = second

    merged = np.concatenate([fixed, merged_pairs], axis=1)
    out = pd.DataFrame(merged)
    out.columns = pd.RangeIndex(out.shape[1])  # 0 … N-1
    return out


def read_pyarrow(path: str, delim="\t"):
    read_opts = pv.ReadOptions(
        autogenerate_column_names=True,  # no header in PED
        block_size=1 << 26,  # 64MB blocks; tweak up/down if needed
    )
    parse_opts = pv.ParseOptions(
        delimiter=delim,  # key: genotype *pairs* are tab-separated
        quote_char=False,
        newlines_in_values=False,
    )
    # Read EVERYTHING as string; don’t infer across 100k+ cols.
    convert_opts = pv.ConvertOptions(column_types={"*": pa.string()})
    # Stream reader to avoid holding everything at once
    reader = pv.open_csv(
        path,
        read_options=read_opts,
        parse_options=parse_opts,
        convert_options=convert_opts,
    )
    # Just collect to a single Arrow Table (if it fits memory)
    table = reader.read_all()
    df = table.to_pandas(split_blocks=True, self_destruct=True)
    logging.info("[read_pyarrow] PED read %s, df shape: %s.", path, df.shape)

    return df


def _to_arrow_table(df: pd.DataFrame) -> pa.Table:
    """Convert pandas → Arrow Table (no index)."""
    return pa.Table.from_pandas(df, preserve_index=False)


def _write_arrow(table: pa.Table, path: Union[str, Path], delimiter: bytes) -> None:
    """Generic Arrow-backed CSV writer with configurable delimiter."""
    opts = pv.WriteOptions(include_header=False, delimiter=delimiter)
    # Some pyarrow versions allow quoting_style
    if hasattr(opts, "quoting_style"):
        try:
            opts.quoting_style = "none"
        except Exception:
            pass
    pv.write_csv(table, str(path), write_options=opts)


def fast_write_space(df: pd.DataFrame, path: Union[str, Path]) -> None:
    """Write DataFrame as space-delimited CSV (no header, no index)."""
    _write_arrow(_to_arrow_table(df), path, delimiter=b" ")


def fast_write_tsv(df: pd.DataFrame, path: Union[str, Path]) -> None:
    """Write DataFrame as tab-delimited CSV (no header, no index)."""
    _write_arrow(_to_arrow_table(df), path, delimiter=b"\t")


def write_plink_files(
    measnum: int,
    pheno_ped: pd.DataFrame,
    map_df: pd.DataFrame,
    outdir: str,
    split_index: int = 6,
) -> None:
    """
    Write PED / MAP / PHENO files for a given measurement number.

    All dependencies (pheno_ped, map_df, outdir) are explicit parameters.
    """
    df = pheno_ped[pheno_ped["measnum"] == measnum]
    if df.empty:
        return

    def _do_sex(sex_flag: str) -> None:
        if sex_flag not in df["sex"].unique():
            return
        df_s = df[df["sex"] == sex_flag]

        # PHENO
        fast_write_space(
            df_s[["FID", "IID", "zscore", "value"]],
            os.path.join(outdir, f"{measnum}.{sex_flag}.pheno"),
        )

        # PED
        int_cols = [c for c in df_s.columns if isinstance(c, int)]
        allele_df = column_splitter_vec(df_s[int_cols], split_index=split_index)
        fast_write_space(
            allele_df,
            os.path.join(outdir, f"{measnum}.{sex_flag}.ped"),
        )

        # MAP
        fast_write_tsv(
            map_df,
            os.path.join(outdir, f"{measnum}.{sex_flag}.map"),
        )

    _do_sex("f")
    _do_sex("m")


def generate_pheno_plink(
    ped_file: str, map_file: str, pheno: pd.DataFrame, outdir: str, ncore: int
) -> pd.DataFrame:
    """
    Generates PLINK-formatted .ped, .map, and .pheno files for phenotype data, stratified by sex and measurement number.

    Args:
        ped_file: Path to the input PED file.
        map_file: Path to the input MAP file.
        pheno: DataFrame containing phenotype data with columns ['strain', 'sex', 'measnum', 'zscore', 'value'].
        outdir: Directory where output files will be saved.
        ncore: Number of cores to use for parallel processing.

    Returns:
        pheno_s: Processed phenotype data filtered and sorted by strain.
    """
    # Ensure the output directory exists
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Normalize strain names in phenotype data
    pheno["strain"] = pheno["strain"].str.replace(" ", "").str.upper()

    # Read map file
    map_df = pd.read_csv(map_file, header=None, sep="\t")
    map_df[1] = np.where(
        map_df[1] == ".",
        map_df[0].astype(str) + "_" + map_df[3].astype(str),
        map_df[1].astype(str),
    )
    logging.debug(
        "[generate_pheno_plink] MAP read %s, df shape: %s.", map_file, map_df.shape
    )
    logging.debug("[generate_pheno_plink] map file read and santized")

    # Read ped file
    ped_df = read_pyarrow(ped_file)
    ped_df.columns = range(ped_df.shape[1])

    meta_cols = [0, 1, 2, 3, 4, 5]
    ped_df[meta_cols] = ped_df[meta_cols].astype(str)

    ped_df[0] = ped_df[0].str.replace("?", "").str.replace(" ", "").str.upper()
    ped_df[1] = ped_df[1].str.replace("?", "").str.replace(" ", "").str.upper()
    logging.debug("[generate_pheno_plink] ped file read and santized")

    # Filter and arrange pheno data by strain
    pheno_s = pheno[(pheno["sex"].isin(["f", "m"])) & (pheno["strain"].isin(ped_df[0]))]
    pheno_s = pheno_s.sort_values(by="strain")
    logging.debug(
        "[generate_pheno_plink] Filtered and sorted phenotype data by strain."
    )

    # Count number of each strain
    pheno_n = pheno_s["strain"].value_counts().reset_index()
    pheno_n.columns = ["strain", "count"]
    pheno_n = pheno_n.sort_values(by="strain")
    logging.debug(
        "[generate_pheno_plink] Counted number of occurrences for each strain."
    )

    # Subset ped data
    ped_s = ped_df[ped_df[0].isin(pheno_s["strain"])]
    ped_s = ped_s.sort_values(by=0).reset_index(drop=True)

    assert (
        pheno_n["strain"].tolist() == ped_s[0].tolist()
    ), "Strain mismatch between pheno and ped data after sorting."
    logging.debug(
        "[generate_pheno_plink] Verified that strains in phenotype and PED data match."
    )

    # Uncount ped data by number of each strain
    pheno_ped_n = ped_s.loc[ped_s.index.repeat(pheno_n["count"].values)].reset_index(
        drop=True
    )
    logging.debug(
        "[generate_pheno_plink] Expanded PED data according to strain counts."
    )

    # Combine pheno_s and pheno_ped_n
    pheno_ped = pd.concat(
        [pheno_s.reset_index(drop=True), pheno_ped_n.reset_index(drop=True)], axis=1
    )
    pheno_ped[4] = np.where(pheno_ped["sex"] == "f", 2, 1)  # Set sex in ped file
    pheno_ped[5] = pheno_ped["zscore"]  # Set zscore as the phenotype column in ped file

    # Ensure FID and IID columns are present
    pheno_ped["FID"] = pheno_ped[0]
    pheno_ped["IID"] = pheno_ped[1]

    logging.debug(
        "[generate_pheno_plink] Combined phenotype data with PED data and set necessary columns."
    )

    # Write files for each measure
    Parallel(n_jobs=ncore)(
        delayed(write_plink_files)(
            measnum, pheno_ped=pheno_ped, map_df=map_df, outdir=outdir, split_index=6
        )
        for measnum in pheno_ped["measnum"].unique()
    )

    return pheno_s


def generate_pheno_plink_V0(
    ped_file: str, map_file: str, pheno: pd.DataFrame, outdir: str, ncore: int
) -> pd.DataFrame:
    """
    [deprecated] the newer version leverages faster file writing through pyarrow.

    Generates PLINK-formatted .ped, .map, and .pheno files for phenotype data, stratified by sex and measurement number.

    Args:
        ped_file: Path to the input PED file.
        map_file: Path to the input MAP file.
        pheno: DataFrame containing phenotype data with columns ['strain', 'sex', 'measnum', 'zscore', 'value'].
        outdir: Directory where output files will be saved.
        ncore: Number of cores to use for parallel processing.

    Returns:
        pheno_s: Processed phenotype data filtered and sorted by strain.
    """
    # Ensure the output directory exists
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Normalize strain names in phenotype data
    pheno["strain"] = pheno["strain"].str.replace(" ", "").str.upper()

    # Read map file
    map_df = pd.read_csv(map_file, header=None, sep="\t")
    map_df[1] = np.where(
        map_df[1] == ".",
        map_df[0].astype(str) + "_" + map_df[3].astype(str),
        map_df[1].astype(str),
    )
    logging.debug("map file read and santized")

    # Read ped file
    ped_df = read_pyarrow(ped_file)
    ped_df.columns = range(ped_df.shape[1])

    ped_df[0] = ped_df[0].str.replace("?", "").str.replace(" ", "").str.upper()
    ped_df[1] = ped_df[1].str.replace("?", "").str.replace(" ", "").str.upper()
    logging.debug("ped file read and santized")

    # Filter and arrange pheno data by strain
    pheno_s = pheno[(pheno["sex"].isin(["f", "m"])) & (pheno["strain"].isin(ped_df[0]))]
    pheno_s = pheno_s.sort_values(by="strain")
    logging.debug("Filtered and sorted phenotype data by strain.")

    # Count number of each strain
    pheno_n = pheno_s["strain"].value_counts().reset_index()
    pheno_n.columns = ["strain", "count"]
    pheno_n = pheno_n.sort_values(by="strain")
    logging.debug("Counted number of occurrences for each strain.")

    # Subset ped data
    ped_s = ped_df[ped_df[0].isin(pheno_s["strain"])]
    ped_s = ped_s.sort_values(by=0).reset_index(drop=True)

    assert (
        pheno_n["strain"].tolist() == ped_s[0].tolist()
    ), "Strain mismatch between pheno and ped data after sorting."
    logging.debug("Verified that strains in phenotype and PED data match.")

    # Uncount ped data by number of each strain
    pheno_ped_n = ped_s.loc[ped_s.index.repeat(pheno_n["count"].values)].reset_index(
        drop=True
    )
    logging.debug("Expanded PED data according to strain counts.")

    # Combine pheno_s and pheno_ped_n
    pheno_ped = pd.concat(
        [pheno_s.reset_index(drop=True), pheno_ped_n.reset_index(drop=True)], axis=1
    )
    pheno_ped[4] = np.where(pheno_ped["sex"] == "f", 2, 1)  # Set sex in ped file
    pheno_ped[5] = pheno_ped["zscore"]  # Set zscore as the phenotype column in ped file

    # Ensure FID and IID columns are present
    pheno_ped["FID"] = pheno_ped[0]
    pheno_ped["IID"] = pheno_ped[1]

    logging.debug("Combined phenotype data with PED data and set necessary columns.")

    # Write files for each measure
    def write_files(x):
        # TODO: create faster pyarrow version
        df = pheno_ped[pheno_ped["measnum"] == x]
        # Fix: remove iloc
        if "f" in df["sex"].unique():
            df_f = df[df["sex"] == "f"]

            # write pheno file
            df_f[["FID", "IID", "zscore", "value"]].to_csv(
                os.path.join(outdir, f"{x}.f.pheno"), sep=" ", index=False, header=False
            )

            # Fix:  I need only the integer indices
            indices = [x for x in df_f.columns if isinstance(x, (int))]
            df_f = df_f[indices]

            # Fix: need to split single columns into two columns: "2 2" -> 2 2
            df_f = column_splitter_vec(df_f)

            # Write rest of files in PLINK format
            df_f.to_csv(
                os.path.join(outdir, f"{x}.f.ped"), sep=" ", index=False, header=False
            )
            map_df.to_csv(
                os.path.join(outdir, f"{x}.f.map"), sep="\t", index=False, header=False
            )

        if "m" in df["sex"].unique():
            df_m = df[df["sex"] == "m"]

            # write pheno file
            df_m[["FID", "IID", "zscore", "value"]].to_csv(
                os.path.join(outdir, f"{x}.m.pheno"), sep=" ", index=False, header=False
            )

            # Fix:  I need only the integer indices
            indices = [x for x in df_m.columns if isinstance(x, (int))]
            df_m = df_m[indices]

            # Fix: need to split single columns into two columns: "2 2" -> 2 2
            df_m = column_splitter_vec(df_m)

            # Write rest of files in PLINK format
            df_m.to_csv(
                os.path.join(outdir, f"{x}.m.ped"), sep=" ", index=False, header=False
            )
            map_df.to_csv(
                os.path.join(outdir, f"{x}.m.map"), sep="\t", index=False, header=False
            )

    Parallel(n_jobs=ncore)(
        delayed(write_files)(x) for x in pheno_ped["measnum"].unique()
    )

    return pheno_s


def prepare_pylmm_inputs(
    ped_file: str,
    map_file: str,
    measure_id_directory: str,
    measure_ids: List,
    outdir: str,
    ncore: int,
    plink2_path: str,
    genotype_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Prepare the inputs required for running pylmm analysis.

    Args:
        ped_file: Path to the output PED file.
        map_file: Path to the output MAP file.
        measure_id_directory: Directory containing the measure csvs.
        measure_ids: List of measure ids.
        outdir: Output directory for generated files.
        ncore: Number of cores for parallel processing.
        plink2_path: Path to the PLINK2 executable.
        genotype_df [Optional]: DataFrame containing genotype data.  Can be supplied
            in the rare cases we want to regenerate the ped/ map files.
    """
    # Ensure the output directory exists
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    logging.debug("[prepare_pylmm_inputs] ensuring directory exists [complete]")
    # Default behavior is to assume ped/ map are already generated and reusable
    if genotype_df is not None:
        generate_ped_map(genotype_df, ped_file, map_file)

    # Step 1: Extract phenotype measures
    pheno = extract_pheno_measure(measure_id_directory, measure_ids)
    logging.debug("[prepare_pylmm_inputs] extract phenotype measures [complete]")
    # Step 2: Generate phenotype PLINK files
    generate_pheno_plink(ped_file, map_file, pheno, outdir, ncore)
    logging.debug("[prepare_pylmm_inputs] generate pheno plink [complete]")
    # Step 3: Generate BED/BIM/FAM files using PLINK2

    for measure_id in measure_ids:
        base_id = str(measure_id).split("_", 1)[0]  # "131063_BXD" -> "131063"
        for sex in ("f", "m"):
            ped_name = f"{base_id}.{sex}.ped"
            map_name = f"{base_id}.{sex}.map"

            measure_ped_file = os.path.join(outdir, ped_name)
            measure_map_file = os.path.join(outdir, map_name)
            output_prefix = os.path.join(outdir, f"{base_id}.{sex}")

            logging.debug(
                "[prepare_pylmm_inputs] Creating PLINK for: %s.%s (base_id=%s)",
                measure_id,
                sex,
                base_id,
            )

            if not os.path.exists(measure_ped_file):
                logging.debug(
                    "[prepare_pylmm_inputs] Data not available for sex: %s (missing %s)",
                    sex,
                    ped_name,
                )
                continue

            generate_bed_bim_fam(
                plink2_path, measure_ped_file, measure_map_file, output_prefix
            )
            logging.debug("[prepare_pylmm_inputs] bed bim fam [complete]")

            try:
                kin_prefix = os.path.join(outdir, f"{base_id}.{sex}.kin")
                calculate_kinship_matrix(plink2_path, output_prefix, kin_prefix)
                logging.debug("[prepare_pylmm_inputs] kinship [complete]")

                # Ensure the kinship matrix files are created and not empty
                validate_files_exist_and_not_empty(kin_prefix, ["rel", "rel.id"])
            except Exception as e:
                raise PLINK2Error(
                    f"Error in PLINK2 processing for measure {measure_id}.{sex}: {e}"
                )

    logging.debug("[prepare_pylmm_inputs] Directory contents: %s", os.listdir(outdir))


def prepare_pylmm_inputs_V0(
    ped_file: str,
    map_file: str,
    measure_id_directory: str,
    measure_ids: List,
    outdir: str,
    ncore: int,
    plink2_path: str,
    genotype_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    [deprecated] Prepare the inputs required for running pylmm analysis.

    Args:
        ped_file: Path to the output PED file.
        map_file: Path to the output MAP file.
        measure_id_directory: Directory containing the measure csvs.
        measure_ids: List of measure ids.
        outdir: Output directory for generated files.
        ncore: Number of cores for parallel processing.
        plink2_path: Path to the PLINK2 executable.
        genotype_df [Optional]: DataFrame containing genotype data.  Can be supplied
            in the rare cases we want to regenerate the ped/ map files.
    """
    # Ensure the output directory exists
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    logging.debug("[prepare_pylmm_inputs] ensuring directory exists [complete]")
    # Default behavior is to assume ped/ map are already generated and reusable
    if genotype_df is not None:
        generate_ped_map(genotype_df, ped_file, map_file)

    # Step 1: Extract phenotype measures
    pheno = extract_pheno_measure(measure_id_directory, measure_ids)
    logging.debug("[prepare_pylmm_inputs] extract phenotype measures [complete]")
    # Step 2: Generate phenotype PLINK files
    generate_pheno_plink(ped_file, map_file, pheno, outdir, ncore)
    logging.debug("[prepare_pylmm_inputs] generate pheno plink [complete]")
    # Step 3: Generate BED/BIM/FAM files using PLINK2

    # iterate over all ,measure id files in directory
    for measure_id in measure_ids:
        for sex in ("f", "m"):
            measure_ped_file = os.path.join(outdir, f"{measure_id}.{sex}.ped")
            measure_map_file = os.path.join(outdir, f"{measure_id}.{sex}.map")
            output_prefix = os.path.join(outdir, f"{measure_id}.{sex}")
            logging.debug(
                "[prepare_pylmm_inputs] Creating PLINK for: %s.%s", measure_id, sex
            )

            if not os.path.exists(measure_ped_file):
                logging.debug(
                    f"[prepare_pylmm_inputs] Data not available for sex: {sex}"
                )
                continue

            generate_bed_bim_fam(
                plink2_path, measure_ped_file, measure_map_file, output_prefix
            )

            logging.debug("[prepare_pylmm_inputs] bed bim fam [complete]")

            # Step 4: Calculate kinship matrix using PLINK2
            kin_prefix = os.path.join(outdir, f"{measure_id}.{sex}.kin")
            try:
                calculate_kinship_matrix(plink2_path, output_prefix, kin_prefix)
                logging.debug("[prepare_pylmm_inputs] kinship [complete]")

                # Ensure the kinship matrix files are created and not empty
                validate_files_exist_and_not_empty(kin_prefix, ["rel", "rel.id"])
            except Exception as e:
                raise PLINK2Error(
                    f"Error in PLINK2 processing for measure {measure_id}.{sex}: {e}"
                )

    logging.debug("[prepare_pylmm_inputs] Directory contents: %s", os.listdir(outdir))


def extract_pheno_measure_from_api(url="https://phenome.jax.org/", measure_id=None):
    """
    Extract phenotype based on measure id.
    (Python version of Hao's R function.)

    :param url: url of MPD. Default: "https://phenome.jax.org/"
    :param measure_id: measure ids

    :return: One dataframe for all phenotype measures.
    """
    raise NotImplementedError(
        "This function needs more testing in order to safely use it."
    )
    import requests
    from io import StringIO

    if measure_id is None:
        measure_id = []

    dat_list = []
    for mid in measure_id:
        try:
            response = requests.get(f"{url}api/pheno/animalvals/{mid}?csv=yes")
            if response.status_code == 200:
                csv_data = StringIO(response.text)
                df = pd.read_csv(csv_data)
                dat_list.append(df)
            else:
                print(
                    f"Failed to fetch data for measure ID {mid}: Status code {response.status_code}"
                )
        except Exception as e:
            print(f"Error fetching data for measure ID {mid}: {e}")

    if not dat_list:
        return pd.DataFrame()

    dat_all = pd.concat(dat_list, ignore_index=True)
    dat_all["strain"] = dat_all["strain"].str.replace(" ", "")
    dat_all["strain"] = dat_all["strain"].apply(
        lambda x: re.sub(r".$", "", x) if x.startswith("CC") else x
    )

    return dat_all
