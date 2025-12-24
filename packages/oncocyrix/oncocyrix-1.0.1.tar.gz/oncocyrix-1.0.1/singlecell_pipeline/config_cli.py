# config_cli.py
import argparse
from pathlib import Path
import logging
import sys

# =========================
# 1. CONFIG (SINGLE MODE ONLY)
# =========================

SINGLE_10X_DIR = Path(
    r"D:\AyassBio_Workspace_Downloads\SCANPY-SINGLECELL_PIPELINE\Cervical_cancer_sc_test\SINGLE_CELL_10X\singlecell_pipeline\sc_test_run\Normal_HPV–\GSM6360681_N_HPV_NEG_2"
)
SINGLE_SAMPLE_LABEL = "X_10"
SINGLE_GROUP_LABEL = "LUNG_CANCER"   # e.g. "CASE" / "CONTROL" or "TUMOR" / "NORMAL"

# SHORTER to avoid Excel 259-char path issues
OUTPUT_FOLDER_NAME = "SC_RESULTS"

# --- PATHWAY CLUSTERING CONTROL ---
DO_PATHWAY_CLUSTERING = True

# --- CLI OVERRIDES (single mode only) ---

parser = argparse.ArgumentParser(
    description="10x-only single-cell pipeline (single dataset)."
)
parser.add_argument("--single-10x-dir", type=str, help="Path to single 10x folder.")
parser.add_argument("--out-name", type=str, help="Custom output dir name.")
parser.add_argument("--no-pathway-clustering", action="store_true",
                    help="Disable pathway clustering/enrichment.")

# NEW ↓↓↓↓↓↓↓
parser.add_argument("--single-sample-label", type=str,
                    help="Sample label to store in obs['sample'].")
parser.add_argument("--single-group-label", type=str,
                    help="Group label to store in obs['group'] (e.g. CASE/CONTROL).")

# NOTE: parse_known_args so you can still extend CLI elsewhere if needed
args, _ = parser.parse_known_args()

if args.single_10x_dir is not None:
    SINGLE_10X_DIR = Path(args.single_10x_dir)

if args.out_name is not None:
    OUTPUT_FOLDER_NAME = args.out_name

if args.no_pathway_clustering:
    DO_PATHWAY_CLUSTERING = False

if args.single_sample_label is not None:
    SINGLE_SAMPLE_LABEL = args.single_sample_label

if args.single_group_label is not None:
    SINGLE_GROUP_LABEL = args.single_group_label

IN_DIR = SINGLE_10X_DIR
DATA_PATH = SINGLE_10X_DIR

COMBINED_OUT_DIR = IN_DIR / OUTPUT_FOLDER_NAME
COMBINED_OUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = COMBINED_OUT_DIR / "pipeline.log"

# ============= LOGGING =============
for h in logging.root.handlers[:]:
    logging.root.removeHandler(h)

logging.basicConfig(
    level=logging.INFO,
    format="(asctime)s\t[%(levelname)s]\t%(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger()

logger.info(f"Logging to file: {LOG_FILE}")
logger.info(f"IN_DIR: {IN_DIR}")
logger.info(f"DATA_PATH: {DATA_PATH}")
logger.info(f"COMBINED_OUT_DIR: {COMBINED_OUT_DIR}")

