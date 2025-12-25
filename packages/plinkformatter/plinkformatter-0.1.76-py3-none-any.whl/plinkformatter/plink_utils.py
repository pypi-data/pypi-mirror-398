# plink_utils.py


from __future__ import annotations


import os
import sys
import subprocess
import logging
from typing import Optional, List


import numpy as np
import pandas as pd
from statistics import NormalDist


# --------------------------- Low-level runners --------------------------- #


def run_plink2(command: str) -> None:
    """
    Run a shell command invoking PLINK2 (or any plink-like CLI), capturing stdout/stderr.


    On non-zero exit, raise RuntimeError with stderr so callers fail fast.
    """
    logging.info("[plink_utils:run_plink2] %s", command)
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        logging.error(
            "[plink_utils:run_plink2] failed (code %d).\nSTDERR:\n%s\nSTDOUT:\n%s",
            result.returncode,
            stderr,
            stdout,
        )
        raise RuntimeError(
            f"PLINK command failed (exit {result.returncode}).\n"
            f"Command: {command}\n"
            f"STDERR:\n{stderr}\n"
            f"STDOUT:\n{stdout}"
        )
    logging.debug("[plink_utils:run_plink2] OK\n%s", (result.stdout or "").strip())


def run_cmd_list(cmd: List[str]) -> None:
    """
    Run a command without shell, capturing stdout/stderr. Raises on failure.
    """
    logging.info("[plink_utils:run_cmd_list] %s", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {r.returncode}).\n"
            f"Command: {' '.join(cmd)}\n"
            f"STDERR:\n{(r.stderr or '').strip()}\n"
            f"STDOUT:\n{(r.stdout or '').strip()}"
        )


# --------------------------- PLINK2 helpers (existing) --------------------------- #


def _create_sorted_pgen_from_pedmap(
    plink2_path: str,
    ped_path: str,
    map_path: str,
    temp_prefix: str,
) -> None:
    """
    Fallback for PLINK2 'split chromosome' errors:
      1) read PED/MAP
      2) --make-pgen --sort-vars
    """
    logging.info(
        "[plink_utils:_create_sorted_pgen_from_pedmap] ped=%s map=%s out=%s",
        ped_path,
        map_path,
        temp_prefix,
    )
    cmd = (
        f"{plink2_path} "
        f"--ped {ped_path} "
        f"--map {map_path} "
        f"--make-pgen --sort-vars "
        f"--out {temp_prefix}"
    )
    run_plink2(cmd)


def generate_bed_bim_fam(
    plink2_path: str,
    ped_file: str,
    map_file: str,
    output_prefix: str,
    relax_mind_threshold: bool = False,
    maf_threshold: Optional[float] = None,
    sample_keep_path: Optional[str] = None,
    autosomes_only: bool = False,
    reference_allele_path: Optional[str] = None,
) -> None:
    """
    PLINK2 path (kept for compatibility), but Hao uses PLINK1 in his pipeline.


    Generates BED/BIM/FAM from PED/MAP:
        plink2 --pedmap <prefix> --make-bed --geno 0.1 --mind 0.1 --out <prefix>
    """
    ped_expect = f"{output_prefix}.ped"
    map_expect = f"{output_prefix}.map"

    if not os.path.exists(ped_expect):
        raise FileNotFoundError(f"Missing PED for --pedmap: {ped_expect}")
    if not os.path.exists(map_expect):
        raise FileNotFoundError(f"Missing MAP for --pedmap: {map_expect}")

    mind = "" if relax_mind_threshold else "--mind 0.1"
    maf = f"--maf {maf_threshold}" if maf_threshold is not None else ""
    keep = f"--keep {sample_keep_path}" if sample_keep_path else ""
    chrflag = "--chr 1-19" if autosomes_only else ""
    ref = f"--reference-allele {reference_allele_path}" if reference_allele_path else ""

    logging.info(
        "[plink_utils:generate_bed_bim_fam] out=%s mind=%s maf=%s keep=%s chr=%s ref=%s",
        output_prefix,
        mind or "none",
        maf or "none",
        keep or "none",
        chrflag or "all",
        ref or "none",
    )

    try:
        pedmap_cmd = (
            f"{plink2_path} --pedmap {output_prefix} "
            f"--make-bed --geno 0.1 {mind} {maf} {keep} {chrflag} {ref} --out {output_prefix}"
        )
        run_plink2(pedmap_cmd)
    except RuntimeError:
        logging.warning(
            "[plink_utils:generate_bed_bim_fam] PLINK2 failed; fallback to make-pgen+sort-vars."
        )
        temp_prefix = f"{output_prefix}_sorted"
        _create_sorted_pgen_from_pedmap(
            plink2_path=plink2_path,
            ped_path=ped_expect,
            map_path=map_expect,
            temp_prefix=temp_prefix,
        )
        pfile_cmd = (
            f"{plink2_path} --pfile {temp_prefix} "
            f"--make-bed --geno 0.1 {mind} {maf} {keep} {chrflag} {ref} "
            f"--out {output_prefix}"
        )
        run_plink2(pfile_cmd)

    fam_expect = f"{output_prefix}.fam"
    if not os.path.exists(fam_expect):
        raise FileNotFoundError(f"PLINK2 finished but FAM not found: {fam_expect}")


def calculate_kinship_matrix(
    plink2_path: str,
    input_prefix: str,
    output_prefix: str,
    sample_keep_path: Optional[str] = None,
) -> None:
    """
    Create PLINK2 .rel kinship files:
        plink2 --bfile <input_prefix> --make-rel square --out <output_prefix>
    """
    keep = f"--keep {sample_keep_path}" if sample_keep_path else ""
    cmd = f"{plink2_path} --bfile {input_prefix} {keep} --make-rel square --out {output_prefix}"
    run_plink2(cmd)


def calculate_kinship_from_pedmap(
    plink2_path: str,
    pedmap_prefix: str,
    kin_prefix: str,
) -> None:
    """
    Compute kinship via PLINK2:
        plink2 --pedmap <prefix> --make-rel square --out <kin_prefix>
    with fallback to --bfile if pedmap fails.
    """
    try:
        cmd = f"{plink2_path} --pedmap {pedmap_prefix} --make-rel square --out {kin_prefix}"
        run_plink2(cmd)
        return
    except Exception as e:
        logging.warning(
            "[plink_utils:calculate_kinship_from_pedmap] --pedmap failed; fallback to --bfile. err=%s",
            str(e),
        )

    bed = pedmap_prefix + ".bed"
    bim = pedmap_prefix + ".bim"
    fam = pedmap_prefix + ".fam"
    if not (os.path.exists(bed) and os.path.exists(bim) and os.path.exists(fam)):
        raise RuntimeError(
            f"[plink_utils:calculate_kinship_from_pedmap] Missing BED/BIM/FAM for {pedmap_prefix!r}: "
            f"{bed}, {bim}, {fam}"
        )

    run_plink2(
        f"{plink2_path} --bfile {pedmap_prefix} --make-rel square --out {kin_prefix}"
    )


# --------------------------- PLINK1 helper (Hao-exact) --------------------------- #


def generate_bed_bim_fam_plink1(
    plink1_path: str,
    file_prefix: str,
    out_prefix: str,
    reference_allele_path: Optional[str] = None,
    geno: float = 0.1,
    mind: float = 0.1,
) -> None:
    """
    EXACT Hao bed step:


      plink --noweb -file <file_prefix> --geno 0.1 --mind 0.1 --make-bed
           --reference-allele <ref> --out <out_prefix>


    Requires:
      <file_prefix>.ped and <file_prefix>.map exist.
    """
    ped = file_prefix + ".ped"
    mp = file_prefix + ".map"
    if not os.path.exists(ped):
        raise FileNotFoundError(f"Missing PED for plink1 -file: {ped}")
    if not os.path.exists(mp):
        raise FileNotFoundError(f"Missing MAP for plink1 -file: {mp}")

    cmd = [
        plink1_path,
        "--noweb",
        "-file",
        file_prefix,
        "--geno",
        str(geno),
        "--mind",
        str(mind),
        "--make-bed",
    ]
    if reference_allele_path:
        cmd += ["--reference-allele", reference_allele_path]
    cmd += ["--out", out_prefix]

    run_cmd_list(cmd)

    fam = out_prefix + ".fam"
    if not os.path.exists(fam):
        raise FileNotFoundError(f"plink1 finished but FAM not found: {fam}")


# --------------------------- pylmm3 kinship helper --------------------------- #


def calculate_kinship_with_pylmm3(
    bfile_prefix: str,
    kin_output_path: Optional[str] = None,
    verbose: bool = True,
) -> None:
    """
    Mirror Hao:
        python pylmmKinship.py -v --bfile 45911.m 45911.m.kin


    We invoke:
        python -m pylmm3.scripts.pylmmKinship -v --bfile <bfile_prefix> <kin_output_path>
    """
    if kin_output_path is None:
        kin_output_path = bfile_prefix + ".kin"

    cmd = [sys.executable, "-m", "pylmm3.scripts.pylmmKinship"]
    if verbose:
        cmd.append("-v")
    cmd.extend(["--bfile", bfile_prefix, kin_output_path])

    logging.info("[plink_utils:calculate_kinship_with_pylmm3] %s", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"pylmm3 kinship failed (exit {r.returncode}).\n"
            f"Command: {' '.join(cmd)}\n"
            f"STDERR:\n{(r.stderr or '').strip()}\n"
            f"STDOUT:\n{(r.stdout or '').strip()}"
        )
    logging.info(
        "[plink_utils:calculate_kinship_with_pylmm3] wrote %s", kin_output_path
    )


# --------------------------- PHENO alignment + rankZ (critical) --------------------------- #


def _rz_transform(values: np.ndarray) -> np.ndarray:
    """
    R-equivalent:
      rankY = rank(y, ties.method="average", na.last="keep")
      rzT  = qnorm(rankY/(length(na.exclude(rankY))+1))
    """
    s = pd.to_numeric(pd.Series(values), errors="coerce").astype(float)
    mask = np.isfinite(s.to_numpy())
    out = np.full(s.shape[0], np.nan, dtype=float)
    if mask.sum() == 0:
        return out

    ranks = pd.Series(s.to_numpy()[mask]).rank(method="average").to_numpy()
    n = int(mask.sum())
    p = ranks / (n + 1.0)
    nd = NormalDist()
    out_vals = np.array([nd.inv_cdf(pi) for pi in p], dtype=float)
    out[mask] = out_vals
    return out


def align_pheno_to_fam_and_recompute_rankz(
    pheno_path: str,
    fam_path: str,
    out_path: Optional[str] = None,
    recompute_rankz: bool = True,
) -> None:
    """
    Force phenofile to match .fam sample set + order.
    Then recompute rankZ on the kept samples' 'value' column.


    Input pheno can be 4 cols or 5 cols. Output is always 5 cols:
      FID IID zscore value rankzonvalue
    """
    if out_path is None:
        out_path = pheno_path

    fam = pd.read_csv(fam_path, sep=r"\s+", header=None, engine="python").iloc[:, :2]
    fam.columns = ["FID", "IID"]

    phe = pd.read_csv(pheno_path, sep=r"\s+", header=None, engine="python")
    if phe.shape[1] == 4:
        phe.columns = ["FID", "IID", "zscore", "value"]
        phe["rankzonvalue"] = np.nan
    elif phe.shape[1] >= 5:
        phe = phe.iloc[:, :5].copy()
        phe.columns = ["FID", "IID", "zscore", "value", "rankzonvalue"]
    else:
        raise ValueError(f"Unexpected pheno columns: {phe.shape[1]} in {pheno_path}")

    phe_idx = phe.set_index(["FID", "IID"])
    out = fam.join(phe_idx, on=["FID", "IID"], how="left")

    missing = out["value"].isna().sum()
    if missing:
        raise ValueError(
            f"{missing} FAM samples missing from PHENO after alignment. "
            f"Example:\n{out[out['value'].isna()].head()}"
        )

    if recompute_rankz:
        out["rankzonvalue"] = _rz_transform(out["value"].to_numpy())

    out[["FID", "IID", "zscore", "value", "rankzonvalue"]].to_csv(
        out_path, sep=" ", header=False, index=False
    )


# --------------------------- Legacy helper retained (optional) --------------------------- #


def rewrite_pheno_ids_from_fam(pheno_path: str, fam_path: str, out_path: str) -> None:
    """
    Legacy: rewrite ONLY IID to match FAM IID for each FID group (strict 1:1 counts).
    Kept for backward compatibility. Prefer align_pheno_to_fam_and_recompute_rankz().
    """
    fam = pd.read_csv(
        fam_path,
        sep=r"\s+",
        header=None,
        names=["FID", "IID", "PID", "MID", "SEX", "PHE"],
        engine="python",
    )
    phe = pd.read_csv(
        pheno_path,
        sep=r"\s+",
        header=None,
        names=["FID", "IID", "zscore", "value"],
        engine="python",
    )

    out_chunks = []
    phe_groups = {k: g for k, g in phe.groupby("FID", sort=False)}
    for fid, fam_grp in fam.groupby("FID", sort=False):
        if fid not in phe_groups:
            raise ValueError(f"FID present in FAM but missing in PHENO: {fid}")

        phe_grp = phe_groups[fid].copy()
        if len(phe_grp) != len(fam_grp):
            raise ValueError(
                f"PHENO vs FAM row-count mismatch for FID={fid}: "
                f"pheno={len(phe_grp)} fam={len(fam_grp)}"
            )

        phe_grp = phe_grp.reset_index(drop=True)
        phe_grp["IID"] = fam_grp["IID"].reset_index(drop=True)
        out_chunks.append(phe_grp[["FID", "IID", "zscore", "value"]])

    out = pd.concat(out_chunks, axis=0)
    out.to_csv(out_path, sep=" ", header=False, index=False)
