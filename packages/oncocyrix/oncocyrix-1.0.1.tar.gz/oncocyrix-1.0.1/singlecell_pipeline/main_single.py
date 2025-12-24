# main_single.py
from .config_cli import (
    SINGLE_10X_DIR,
    SINGLE_SAMPLE_LABEL,
    SINGLE_GROUP_LABEL,
    COMBINED_OUT_DIR,
    logger,
)
from .loader_10x import load_10x_feature_barcode_matrix
from .pipeline import run_scanpy_pipeline


def main():
    adata_single_raw = load_10x_feature_barcode_matrix(SINGLE_10X_DIR)

    adata_single_raw.obs["sample"] = SINGLE_SAMPLE_LABEL
    if SINGLE_GROUP_LABEL is not None:
        adata_single_raw.obs["group"] = SINGLE_GROUP_LABEL

    run_scanpy_pipeline(
        adata_single_raw,
        COMBINED_OUT_DIR,
        analysis_name="single_dataset",
        batch_key=None,
        integration_method=None,
        do_groupwise_de=False,  # same as your original script
        do_dpt=False,
    )

    logger.info(
        "DONE — Full single-cell pipeline (10x-only, single dataset) finished with structured outputs."
    )


if __name__ == "__main__":
    main()
