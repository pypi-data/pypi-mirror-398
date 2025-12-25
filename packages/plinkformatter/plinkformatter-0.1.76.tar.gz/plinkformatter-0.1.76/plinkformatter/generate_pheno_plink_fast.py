# generate_pheno_plink_fast.py


from __future__ import annotations


import os
import math
import logging
from typing import Dict, List, Union, Optional, Tuple


import numpy as np
import pandas as pd
from statistics import NormalDist


from plinkformatter.plink_utils import (
    generate_bed_bim_fam,
    generate_bed_bim_fam_plink1,
    calculate_kinship_from_pedmap,
    calculate_kinship_with_pylmm3,
    align_pheno_to_fam_and_recompute_rankz,
)


from plinkformatter.generate_pheno_plink import extract_pheno_measure


MIN_SAMPLES_FOR_KINSHIP: int = 50


def _norm_id(x) -> str:
    s = str(x).strip()
    if s == "":
        return s
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
        return ("%.10g" % f).rstrip()
    except Exception:
        if s.endswith(".0"):
            s = s[:-2]
        return s


def rz_transform(values: Union[pd.Series, np.ndarray, List[float]]) -> np.ndarray:
    """
    Match Hao's R:
      rankY = rank(y, ties.method="average", na.last="keep")
      rzT  = qnorm(rankY/(length(na.exclude(rankY))+1))
    """
    arr = pd.Series(values, copy=False)
    v = pd.to_numeric(arr, errors="coerce").astype(float)
    mask = np.isfinite(v.to_numpy())
    out = np.full(v.shape[0], np.nan, dtype=float)

    if mask.sum() == 0:
        return out

    ranks = pd.Series(v.to_numpy()[mask]).rank(method="average").to_numpy()
    n = int(mask.sum())
    p = ranks / (n + 1.0)

    nd = NormalDist()
    out_vals = np.array([nd.inv_cdf(pi) for pi in p], dtype=float)
    out[mask] = out_vals
    return out


# ----------------------------- NON-DO PATH ----------------------------- #
def generate_pheno_plink_fast_non_do(
    ped_file: str,
    map_file: str,
    pheno: pd.DataFrame,
    outdir: str,
) -> pd.DataFrame:
    """
    NON-DO matches Hao with correct ordering:
      - Iterate through pheno in original order (like left_join)
      - Maintain streaming approach
      - FID = strain, IID = paste0(strain,"_",animal_id)
    """
    os.makedirs(outdir, exist_ok=True)
    if pheno is None or pheno.empty:
        return pd.DataFrame()


    # Pre-process pheno
    ph = pheno.copy()
    ph["strain"] = ph["strain"].astype(str).str.replace(" ", "", regex=False)
    ph = ph[ph["sex"].isin(["f", "m"])].copy()
    
    # Process map file
    map_df = pd.read_csv(map_file, header=None, sep=r"\s+", engine="python")
    map_df[1] = np.where(
        map_df[1].astype(str) == ".",
        map_df[0].astype(str) + "_" + map_df[3].astype(str),
        map_df[1].astype(str),
    )


    # Build strain->offset index and cache genotypes
    strain_offsets = {}
    strain_genotypes = {}
    
    with open(ped_file, "rb") as f:
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            
            decoded = line.decode(errors="replace").rstrip("\n")
            parts = decoded.split("\t")
            if len(parts) <= 6:
                parts = decoded.split()
            if len(parts) < 7:
                continue
                
            strain = parts[0].replace("?", "").replace(" ", "").upper()
            if strain not in strain_offsets:
                strain_offsets[strain] = pos
                
                # Parse and cache genotypes
                geno_fields = parts[6:]
                if any(" " in gp for gp in geno_fields):
                    # Split genotype pairs
                    geno_tokens = []
                    for gp in geno_fields:
                        a_b = gp.split()
                        if len(a_b) == 2:
                            geno_tokens.extend(a_b)
                        else:
                            geno_tokens.append(gp)
                else:
                    geno_tokens = geno_fields
                
                strain_genotypes[strain] = " ".join(geno_tokens)


    # Filter pheno to strains in PED
    ph = ph[ph["strain"].isin(strain_offsets.keys())].copy()
    if ph.empty:
        return ph


    # Process each measurement and sex
    for (measnum, sex), group_df in ph.groupby(["measnum", "sex"], sort=False):
        measnum = int(measnum)
        sex = str(sex)
        
        # CRITICAL: Use the group as-is, don't sort or reorder
        # This matches Hao's left_join which preserves pheno order
        group_df = group_df.copy()
        
        # Compute rankz for this group
        group_df["rankzonvalue"] = rz_transform(group_df["value"].to_numpy())
        
        # Write files
        map_out = os.path.join(outdir, f"{measnum}.{sex}.map")
        ped_out = os.path.join(outdir, f"{measnum}.{sex}.ped")
        phe_out = os.path.join(outdir, f"{measnum}.{sex}.pheno")
        
        map_df.to_csv(map_out, sep="\t", index=False, header=False)
        
        with open(ped_out, "w", encoding="utf-8") as f_ped, \
             open(phe_out, "w", encoding="utf-8") as f_ph:
            
            # Iterate in EXACT order of group_df (matches left_join)
            for idx, row in group_df.iterrows():
                strain = row["strain"]
                aid = _norm_id(row["animal_id"])
                iid = f"{strain}_{aid}"
                
                # Get cached genotypes
                if strain not in strain_genotypes:
                    # Read from file if not cached
                    with open(ped_file, "rb") as fp:
                        fp.seek(strain_offsets[strain])
                        raw = fp.readline().decode(errors="replace").rstrip("\n")
                    parts = raw.split("\t")
                    if len(parts) <= 6:
                        parts = raw.split()
                    geno_fields = parts[6:]
                    if any(" " in gp for gp in geno_fields):
                        geno_tokens = []
                        for gp in geno_fields:
                            a_b = gp.split()
                            if len(a_b) == 2:
                                geno_tokens.extend(a_b)
                            else:
                                geno_tokens.append(gp)
                    else:
                        geno_tokens = geno_fields
                    strain_genotypes[strain] = " ".join(geno_tokens)
                
                # Prepare values
                z = row.get("zscore", np.nan)
                v = row.get("value", np.nan)
                rz = row.get("rankzonvalue", np.nan)
                
                z = float(z) if np.isfinite(pd.to_numeric(z, errors="coerce")) else np.nan
                v = float(v) if np.isfinite(pd.to_numeric(v, errors="coerce")) else np.nan
                rz = float(rz) if np.isfinite(pd.to_numeric(rz, errors="coerce")) else np.nan
                
                # Write PED line
                sex_code = "2" if sex == "f" else "1"
                phe_code = f"{rz}" if math.isfinite(rz) else "-9"
                meta = [strain, iid, "0", "0", sex_code, phe_code]
                f_ped.write(" ".join(meta + [strain_genotypes[strain]]) + "\n")
                
                # Write PHENO line
                f_ph.write(
                    f"{strain} {iid} "
                    f"{(z if math.isfinite(z) else -9)} "
                    f"{(v if math.isfinite(v) else -9)} "
                    f"{(rz if math.isfinite(rz) else -9)}\n"
                )


    return ph


def generate_pheno_plink_fast_non_do_deprecated(
    ped_file: str,
    map_file: str,
    pheno: pd.DataFrame,
    outdir: str,
) -> pd.DataFrame:
    """
    [deprecated] not matching Hao's kinship exactly
    NON-DO matches Hao:
      - join by strain
      - FID = strain
      - IID = paste0(strain,"_",animal_id)
      - .pheno: FID IID zscore value rankzonvalue
      - .ped PHE uses rankzonvalue (Hao's current pylmm use-case)
      - supports both:
         * old PED tabbed genotype-pairs
         * new PED whitespace allele-per-column
    """
    os.makedirs(outdir, exist_ok=True)
    if pheno is None or pheno.empty:
        return pd.DataFrame()

    need = ("strain", "sex", "measnum", "value", "animal_id")
    missing = [c for c in need if c not in pheno.columns]
    if missing:
        raise ValueError(
            f"[NON_DO] pheno missing required columns: {missing} (need {list(need)})"
        )

    ph = pheno.copy()
    ph["strain"] = ph["strain"].astype(str).str.replace(" ", "", regex=False)
    ph = ph[ph["sex"].isin(["f", "m"])].copy()
    if ph.empty:
        return ph

    # MAP sanitize (Hao: "." -> chr_bp)
    map_df = pd.read_csv(map_file, header=None, sep=r"\s+", engine="python")
    map_df[1] = np.where(
        map_df[1].astype(str) == ".",
        map_df[0].astype(str) + "_" + map_df[3].astype(str),
        map_df[1].astype(str),
    )

    if "zscore" not in ph.columns:
        ph["zscore"] = np.nan

    # Build strain -> byte offset index from reference PED
    ped_offsets: Dict[str, int] = {}
    with open(ped_file, "rb") as f:
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            first_tab = line.find(b"\t")
            fid_bytes = line.strip().split()[0] if first_tab <= 0 else line[:first_tab]
            name = fid_bytes.decode(errors="replace").replace("?", "").replace(" ", "")
            if name and name not in ped_offsets:
                ped_offsets[name] = pos

    ped_strains = set(ped_offsets.keys())
    ph = ph[ph["strain"].isin(ped_strains)].reset_index(drop=True)
    if ph.empty:
        return ph

    for (measnum, sex), df in ph.groupby(["measnum", "sex"], sort=False):
        measnum = int(measnum)
        sex = str(sex)

        map_out = os.path.join(outdir, f"{measnum}.{sex}.map")
        map_df.to_csv(map_out, sep="\t", index=False, header=False)

        ped_out = os.path.join(outdir, f"{measnum}.{sex}.ped")
        phe_out = os.path.join(outdir, f"{measnum}.{sex}.pheno")

        df = df.reset_index(drop=True)
        df = df.copy()
        df["rankzonvalue"] = rz_transform(df["value"].to_numpy())

        with open(ped_out, "w", encoding="utf-8") as f_ped, open(
            phe_out, "w", encoding="utf-8"
        ) as f_ph:
            for strain, sdf in df.groupby("strain", sort=False):
                with open(ped_file, "rb") as fp:
                    fp.seek(ped_offsets[strain])
                    raw = fp.readline().decode(errors="replace").rstrip("\n")

                parts = raw.split("\t")
                if len(parts) <= 6:
                    parts = raw.split()
                if len(parts) < 7:
                    raise ValueError(
                        "Malformed PED: need >=7 columns (6 meta + genotypes)"
                    )

                geno_fields = parts[6:]
                needs_split = any(" " in gp for gp in geno_fields)

                if needs_split:
                    geno_tokens: List[str] = []
                    for gp in geno_fields:
                        a_b = gp.split()
                        if len(a_b) != 2:
                            raise ValueError(
                                f"Genotype pair not splitable into two alleles: {gp!r}"
                            )
                        geno_tokens.extend(a_b)
                else:
                    geno_tokens = geno_fields

                for _, r in sdf.iterrows():
                    aid = _norm_id(r["animal_id"])
                    iid = f"{strain}_{aid}"

                    z = r.get("zscore", np.nan)
                    v = r.get("value", np.nan)
                    rz = r.get("rankzonvalue", np.nan)

                    z = (
                        float(z)
                        if np.isfinite(pd.to_numeric(z, errors="coerce"))
                        else np.nan
                    )
                    v = (
                        float(v)
                        if np.isfinite(pd.to_numeric(v, errors="coerce"))
                        else np.nan
                    )
                    rz = (
                        float(rz)
                        if np.isfinite(pd.to_numeric(rz, errors="coerce"))
                        else np.nan
                    )

                    sex_code = "2" if sex == "f" else "1"
                    phe_code = f"{rz}" if math.isfinite(rz) else "-9"

                    meta = [strain, iid, "0", "0", sex_code, phe_code]
                    f_ped.write(" ".join(meta + geno_tokens) + "\n")

                    f_ph.write(
                        f"{strain} {iid} "
                        f"{(z if math.isfinite(z) else -9)} "
                        f"{(v if math.isfinite(v) else -9)} "
                        f"{(rz if math.isfinite(rz) else -9)}\n"
                    )

        logging.info(f"[NON_DO] wrote {ped_out}, {map_out}, {phe_out}")

    return ph


# ------------------------------- DO PATH ------------------------------- #


def generate_pheno_plink_fast_do(
    ped_file: str,
    map_file: str,
    pheno: pd.DataFrame,
    outdir: str,
) -> pd.DataFrame:
    """
    DO matches Hao in spirit, writing 5-col pheno including rankzonvalue.
    """
    os.makedirs(outdir, exist_ok=True)
    if pheno is None or pheno.empty:
        return pd.DataFrame()

    need = ("strain", "sex", "measnum", "value", "animal_id")
    missing = [c for c in need if c not in pheno.columns]
    if missing:
        raise ValueError(
            f"[DO] pheno missing required columns: {missing} (need {list(need)})"
        )

    ph = pheno.copy()
    ph["strain"] = ph["strain"].astype(str).str.replace(" ", "", regex=False)
    ph = ph[ph["sex"].isin(["f", "m"])].copy()
    ph["animal_id_norm"] = ph["animal_id"].map(_norm_id)
    ph = ph[ph["animal_id_norm"].notna() & (ph["animal_id_norm"] != "")].copy()
    if ph.empty:
        return ph

    map_df = pd.read_csv(map_file, header=None, sep=r"\s+", engine="python")
    map_df[1] = np.where(
        map_df[1].astype(str) == ".",
        map_df[0].astype(str) + "_" + map_df[3].astype(str),
        map_df[1].astype(str),
    )

    if "zscore" not in ph.columns:
        ph["zscore"] = np.nan

    per_group_maps: Dict[Tuple[int, str], Dict[str, tuple]] = {}
    global_ids: set[str] = set()

    for (meas, sex), g in ph.groupby(["measnum", "sex"], sort=False):
        meas = int(meas)
        sex = str(sex)
        g = g.drop_duplicates(subset=["animal_id_norm"], keep="first").copy()
        g["rankzonvalue"] = rz_transform(g["value"].to_numpy())

        m: Dict[str, tuple] = {}
        for _, r in g.iterrows():
            aid = r["animal_id_norm"]
            z = pd.to_numeric(r.get("zscore", np.nan), errors="coerce")
            v = pd.to_numeric(r.get("value", np.nan), errors="coerce")
            rz = pd.to_numeric(r.get("rankzonvalue", np.nan), errors="coerce")
            m[aid] = (
                float(z) if np.isfinite(z) else np.nan,
                float(v) if np.isfinite(v) else np.nan,
                float(rz) if np.isfinite(rz) else np.nan,
                sex,
            )
            global_ids.add(aid)

        if m:
            per_group_maps[(meas, sex)] = m

    if not per_group_maps:
        return ph

    group_handles: Dict[Tuple[int, str], dict] = {}
    for (meas, sex), aid_map in per_group_maps.items():
        map_out = os.path.join(outdir, f"{meas}.{sex}.map")
        ped_out = os.path.join(outdir, f"{meas}.{sex}.ped")
        phe_out = os.path.join(outdir, f"{meas}.{sex}.pheno")
        map_df.to_csv(map_out, sep="\t", index=False, header=False)

        group_handles[(meas, sex)] = {
            "aid_map": aid_map,
            "ped_path": ped_out,
            "phe_path": phe_out,
            "ped_file": open(ped_out, "w", encoding="utf-8"),
            "phe_file": open(phe_out, "w", encoding="utf-8"),
            "wrote_any": False,
        }

    try:
        with open(ped_file, "r", encoding="utf-8", errors="replace") as fped:
            for raw in fped:
                if not raw.strip():
                    continue
                parts = raw.rstrip("\n").split()
                if len(parts) < 7:
                    continue

                V1, V2 = parts[0], parts[1]
                V1n = _norm_id(V1)
                if V1n not in global_ids:
                    continue

                for (meas, sex), info in group_handles.items():
                    if V1n not in info["aid_map"]:
                        continue
                    z, v, rz, sx = info["aid_map"][V1n]
                    meta = parts[:6]
                    meta[4] = "2" if sx == "f" else "1"
                    meta[5] = f"{rz}" if math.isfinite(rz) else "-9"
                    info["ped_file"].write(" ".join(meta + parts[6:]) + "\n")
                    info["phe_file"].write(
                        f"{V1} {V2} "
                        f"{(z if math.isfinite(z) else -9)} "
                        f"{(v if math.isfinite(v) else -9)} "
                        f"{(rz if math.isfinite(rz) else -9)}\n"
                    )
                    info["wrote_any"] = True
    finally:
        for info in group_handles.values():
            info["ped_file"].close()
            info["phe_file"].close()

    if not any(info["wrote_any"] for info in group_handles.values()):
        raise ValueError(
            "[DO] wrote zero rows; no overlap between animal_id and DO PED V1."
        )

    return ph


# ------------------------------- WRAPPER ------------------------------- #


def generate_pheno_plink_fast(
    ped_file: str,
    map_file: str,
    pheno: pd.DataFrame,
    outdir: str,
    ncore: int = 1,
    *,
    panel_type: str = "NON_DO",
) -> pd.DataFrame:
    if pheno is None or pheno.empty:
        os.makedirs(outdir, exist_ok=True)
        return pd.DataFrame()

    pt = (panel_type or "NON_DO").upper()
    if pt == "DO":
        logging.info("[generate_pheno_plink_fast] using DO panel_type")
        return generate_pheno_plink_fast_do(ped_file, map_file, pheno, outdir)

    logging.info("[generate_pheno_plink_fast] panel_type=%r => NON-DO path", panel_type)
    return generate_pheno_plink_fast_non_do(ped_file, map_file, pheno, outdir)


# ----------------------------- Orchestrator ---------------------------- #


def fast_prepare_pylmm_inputs(
    ped_file: str,
    map_file: str,
    measure_id_directory: str,
    measure_ids: List,
    outdir: str,
    ncore: int,
    plink_path: str,
    *,
    panel_type: str = "NON_DO",
    ped_pheno_field: str = "rankzonvalue",  # kept for compatibility; rankzonvalue is what you want
    maf_threshold: Union[float, None] = None,
    reference_allele_path: Optional[str] = None,
    kinship_via_pylmm3: bool = True,
    use_plink2: Optional[bool] = False,  # default to False to prefer PLINK1 if available
) -> None:
    """
    Pipeline:
      1) extract pheno rows
      2) write per-measure per-sex .ped/.map/.pheno (5-col pheno)
      3) make .bed/.bim/.fam
         - if plink1_path provided: use Hao-exact PLINK1 command
         - else: fall back to existing PLINK2 implementation
      4) align .pheno to .fam (subset + order) AND recompute rankZ on kept samples
      5) kinship:
         - pylmm3 .kin (Hao) OR plink2 --make-rel square
    """
    os.makedirs(outdir, exist_ok=True)

    pheno = extract_pheno_measure(measure_id_directory, measure_ids)
    if pheno is None or pheno.empty:
        logging.info(
            "[fast_prepare_pylmm_inputs] no phenotype rows extracted; nothing to do."
        )
        return

    used = generate_pheno_plink_fast(
        ped_file=ped_file,
        map_file=map_file,
        pheno=pheno,
        outdir=outdir,
        ncore=ncore,
        panel_type=panel_type,
    )
    if used is None or used.empty:
        logging.info(
            "[fast_prepare_pylmm_inputs] no usable phenotypes after PED/MAP intersection; nothing to do."
        )
        return

    for measure_id in measure_ids:
        base_id = str(measure_id).split("_", 1)[0]
        for sex in ("f", "m"):
            ped_path = os.path.join(outdir, f"{base_id}.{sex}.ped")
            map_path = os.path.join(outdir, f"{base_id}.{sex}.map")
            pheno_path = os.path.join(outdir, f"{base_id}.{sex}.pheno")
            out_prefix = os.path.join(outdir, f"{base_id}.{sex}")

            if not (
                os.path.exists(ped_path)
                and os.path.exists(map_path)
                and os.path.exists(pheno_path)
            ):
                continue

            # quick pre-check only
            try:
                with open(pheno_path, "r", encoding="utf-8") as f_ph:
                    n_samples_pre = sum(1 for _ in f_ph)
            except OSError:
                n_samples_pre = 0

            if n_samples_pre < MIN_SAMPLES_FOR_KINSHIP:
                logging.info(
                    "[fast_prepare_pylmm_inputs] skipping %s.%s: n_samples=%d < %d",
                    base_id,
                    sex,
                    n_samples_pre,
                    MIN_SAMPLES_FOR_KINSHIP,
                )
                continue

            # BED/BIM/FAM
            if use_plink2:
                logging.info(
                    "[fast_prepare_pylmm_inputs] PLINK2 bed step for %s.%s",
                    base_id,
                    sex,
                )
                generate_bed_bim_fam(
                    plink2_path=plink_path,
                    ped_file=ped_path,
                    map_file=map_path,
                    output_prefix=out_prefix,
                    relax_mind_threshold=False,
                    maf_threshold=maf_threshold,
                    sample_keep_path=None,
                    autosomes_only=False,
                    reference_allele_path=reference_allele_path,
                )
            else:
                logging.info(
                    "[fast_prepare_pylmm_inputs] PLINK1 bed step for %s.%s",
                    base_id,
                    sex,
                )
                generate_bed_bim_fam_plink1(
                    plink1_path=plink_path,
                    file_prefix=out_prefix,  # .ped/.map prefix you wrote
                    out_prefix=out_prefix,  # .bed/.bim/.fam prefix to write
                    reference_allele_path=reference_allele_path,
                    geno=0.1,
                    mind=0.1,
                )

            # Critical: make .pheno match .fam exactly, and recompute rankZ on kept samples
            fam_path = out_prefix + ".fam"
            align_pheno_to_fam_and_recompute_rankz(
                pheno_path=pheno_path,
                fam_path=fam_path,
                out_path=pheno_path,
                recompute_rankz=True,
            )

            # Kinship
            if kinship_via_pylmm3:
                logging.info(
                    "[fast_prepare_pylmm_inputs] kinship via pylmm3 for %s.%s",
                    base_id,
                    sex,
                )
                calculate_kinship_with_pylmm3(bfile_prefix=out_prefix)
            else:
                logging.info(
                    "[fast_prepare_pylmm_inputs] kinship via PLINK2 for %s.%s",
                    base_id,
                    sex,
                )
                calculate_kinship_from_pedmap(
                    plink2_path=plink2_path,
                    pedmap_prefix=out_prefix,
                    kin_prefix=os.path.join(outdir, f"{base_id}.{sex}.kin"),
                )
