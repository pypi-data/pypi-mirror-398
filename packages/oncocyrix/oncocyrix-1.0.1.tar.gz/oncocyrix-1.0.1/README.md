Single-Sample 10x scRNA-seq Pipeline (scpipeline)

A modular, production-ready Scanpy pipeline for processing and analyzing a single 10x Genomics single-cell RNA-seq sample.
This project is optimized for human cancer datasets, but works for any 10x scRNA-seq run.

Key Capabilities

10x matrix ingestion (MTX + barcodes + features)
Gene ID normalization (Ensembl → Symbol)
QC filtering (mitochondrial %, UMI counts, genes/cell)
Normalization, log1p, HVG selection
PCA, UMAP, t-SNE embeddings
Leiden clustering
Cell type annotation (CellTypist)
Cell-type marker discovery
Multi-database enrichment (GO, KEGG, Reactome, WikiPathways)

🔗 Final biological summaries
Cell Types → DEGs → Markers → Pathways

1. Project Structure
singlecell_pipeline/
│
├── config_cli.py            # CLI + global configuration
├── loader_10x.py            # 10x feature–barcode loading
├── gene_names.py            # Gene ID normalization logic
├── group_de.py              # DE tests, UMAP per group, compositions
├── markers.py               # Cell-type-specific marker detection
├── pathway_enrichment.py    # Enrichr/gseapy enrichment + semantic dedup
├── summary_ct_deg.py        # Summaries (DEGs → markers → pathways)
├── pipeline.py              # High-level Scanpy orchestration
└── main_single.py           # Entry point: single-sample pipeline run


Version: v1.0
A clean, modular codebase designed for clinical/translational scRNA-seq workflows.

2. Features in Detail
➤ 10x Data Loading

Auto-detects matrix.mtx[.gz], barcodes.tsv[.gz], features.tsv/genes.tsv

Handles sparse matrices efficiently

➤ Gene Name Normalization
Detects Ensembl IDs
Maps to HGNC gene symbols via mygene.info
Ensures uniqueness and consistency of adata.var_names

➤ Quality Control & Filtering
Calculates:
pct_counts_mt
n_genes_by_counts
total_counts
Filters:
<200 or >6000 genes
>15% mitochondrial reads
Genes expressed in <3 cells

➤ Normalization & HVG Selection
normalize_total
log1p
HVG selection (Seurat v3 flavor)

➤ Dimensionality Reduction
PCA (50 components)
UMAP
t-SNE (for n_cells < 50k)

➤ Clustering
Leiden clustering (resolution 0.5)
Cluster-level visualizations included

➤ Cell Type Annotation
Auto-detection from metadata OR
CellTypist ML classifier fallback
Generates UMAP/TSNE/pca plots colored by cell types

➤ Marker Gene Detection
Global markers
Per-cell-type markers
Rank plots, heatmaps, dotplots

➤ Pathway Enrichment
Databases supported via gseapy/Enrichr:
GO Biological Process
GO Molecular Function
GO Cellular Component
KEGG
Reactome
WikiPathways

Includes:
Semantic deduplication (MiniLM + FAISS)
Top pathway barplots
Combined enrichment tables

➤ Integrated Summary
Creates a comprehensive biological table linking:
Cell Type → DEGs → Marker Genes → Pathways

3. Usage
Run the pipeline
python main_single.py \
  --single-10x-dir "/path/to/10x_folder" \
  --single-sample-label TumorA \
  --single-group-label LUNG_CANCER


All results are saved to:
<10x_folder>/SC_RESULTS/


This includes:
QC plots
HVG tables
Embeddings (UMAP/t-SNE)
Clusters
Cell types
Marker gene tables
Enrichment results
Summary spreadsheets and text files

4. Intended Use Cases
Cancer single-cell analysis
Tumor microenvironment decomposition
Biomarker discovery
Translational/preclinical studies
ML based celltype prediction