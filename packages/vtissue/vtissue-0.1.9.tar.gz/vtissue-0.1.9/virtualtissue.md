# Project Draft: Self-Supervised Graph Transformer for Virtual Tissue Perturbation Modeling

(working draft – to be iteratively refined)

## 1. Scientific Motivation

Understanding how cellular ecosystems reorganize in response to perturbations is a central question in cancer biology, immunology, and tissue systems science. Experimental perturbations—such as cytokine stimulation, ligand blockade, CRISPR deletion, or cell-type depletion—are limited in human tissues, destructive, and often not feasible across many perturbation conditions. A computationally learned **virtual tissue** provides an alternative framework to probe mechanisms.

This project develops a **self-supervised graph transformer** that learns the organizational principles of tissues from multiplexed imaging or spatial omics. Each cell is modeled as a graph node with expression, spatial context, and optional phenotype, and cell–cell proximity defines edges. The model learns latent tissue structure through masking strategies and multi-task reconstruction, enabling:

* Simulation of **gene-expression perturbations** in selected cell types or regions.
* In silico **disruption of cell–cell interactions** (e.g., antigen presentation, immune checkpoints).
* **Cell-type ablations** to study compensatory reorganization.
* **Spatially localized perturbations** that mimic microenvironmental niches.

The final objective is a biologically grounded **digital twin** that generates mechanistic hypotheses about tissue remodeling under diverse perturbations.

## 2. Data Requirements

All data are represented using AnnData. `adata.X` (or a user-defined layer) stores panel-specific expression. `adata.obs` stores cell-level metadata including `imageid`, `X_centroid`, `Y_centroid`, `sample_type`, and `phenotype`.

### 2.4 Cell type labels and unknowns

Cell type labels are treated as an optional, potentially noisy supervision signal. The `phenotype` column in `adata.obs` may contain:

* well-defined cell types (e.g., `CD8 T cell`, `cDC1`, `Tumor cell`),
* the special value `Unknown` for cells that cannot be typed confidently (e.g., panel-limited),
* the special value `No_label` for cells where no annotation has been attempted or is available.

As part of the package, we automatically detect `Unknown` and `No_label`:

* Cells with `phenotype` equal to `Unknown` or `No_label` are **excluded from the supervised cell-type loss** and treated as unlabeled for the classifier head.
* All other distinct values in `phenotype` are treated as supervised classes.

In the input node features, `phenotype` is encoded as a learned embedding:

* Known cell types each receive their own embedding vector.
* `Unknown` and `No_label` each receive their own dedicated embedding token, so the model is aware that these cells are present but not reliably labeled.

This design allows unknown or uncertain cells to participate fully in the self-supervised objectives while avoiding contamination of the supervised cell-type signal.

In practice, if an image or dataset has **no cell-type annotations at all** (as is common in published multiplexed datasets), all cells from that source should be assigned the value `No_label`. The preprocessing pipeline will automatically detect this and treat the entire image as unlabeled for the supervised cell-type head, while still including all cells in every self-supervised objective. This ensures that missing annotations never degrade the supervised classifier, but unlabeled cells still contribute fully to learning spatial and expression structure.

Because different imaging panels measure different sets of markers, all samples are mapped to a shared global gene or marker list. Each cell obtains:

* A sparse global expression vector of size G (on the order of twenty thousand genes).
* A binary observation mask indicating which genes were measured, provided as a layer called `mask`.

Unmeasured genes remain zeros in the sparse matrix. This enables cross-panel pretraining and integration with RNA-based methods.

For each image (identified by `imageid`), a graph is constructed:

* Nodes: cells
* Edges: spatial k nearest neighbors and or radius-based adjacency
* Node features: projected global expression, mask, optional cell-type embedding, spatial encodings, and optional panel or sample embeddings.

### 2.5 Additional metadata: sample_type, patient_id, batch, and other covariates

Certain metadata fields such as `sample_type`, `patient_id`, `batch`, anatomical site, or clinical grouping contain important contextual information about the tissue. These variables are handled through **metadata embeddings** and optional **supervised objectives**.

### 2.5.1 Recommended optional standardized columns

To support consistent processing across heterogeneous published datasets, the preprocessing pipeline will automatically look for the following **optional but recommended** fields in `adata.obs`:

* `sample_type` — broad biological or clinical class (e.g., tumor, normal, inflamed, non_inflamed).
* `tissue_type` — anatomical or histological category (e.g., skin, lymph node, liver, melanoma, carcinoma).
* `disease` — high-level disease label (e.g., melanoma, CRC, breast cancer).
* `disease_subtype` — finer subclassification (e.g., BRAF-mutant melanoma, acral melanoma, MSI-H CRC).

These fields, if present, are converted into **metadata embeddings** and concatenated to each cell’s node feature vector. If absent, they are simply ignored.

### 2.5.2 How sample_type is used as an input feature

* The value in `adata.obs['sample_type']` (e.g., `tumor`, `stroma`, `inflamed`, `non_inflamed`, `primary`, `metastatic`) is converted to an **embedding vector**.
* This embedding is concatenated into each cell’s node feature, giving each cell awareness of the tissue context it belongs to.
* Embeddings allow the model to learn differences in tissue organization across sample classes without rigidly enforcing categorical rules.

### 2.5.3 How metadata fields can be used in supervised objectives (optional)

* A **tissue-level classification head** can use the global token to predict metadata such as `sample_type`, `tissue_type`, `disease`, or `disease_subtype`.
* Only samples with valid labels contribute to these optional losses.
* These additional objectives help the global embedding capture biologically meaningful global structure.

### 2.5.4 Why metadata embeddings are useful

* They help the model disambiguate spatial or expression patterns that differ systematically across biological contexts.
* They allow the model to harmonize across datasets, batches, panels, and experimental conditions.
* They support both global and local reasoning during perturbation simulation.

In summary, metadata such as `sample_type`, `tissue_type`, `disease`, and `disease_subtype` can be seamlessly incorporated as optional conditioning signals and supervised targets, enabling richer context-aware modeling of tissue structure. `sample_type` are used both as **input conditioning signals** (via embeddings) and optionally as **supervised targets** via a global tissue-level head. This supports richer, context-aware learning of tissue structure.

### 2.1 Spatial coordinates, units, and normalization

The raw coordinates `X_centroid` and `Y_centroid` are typically in pixel units and depend on image size, crop position, and imaging resolution. To make geometry comparable across images and instruments, we standardize coordinates in two steps.

1. Conversion from pixels to microns using an `mpp` parameter (microns per pixel):

   * During preprocessing, the user supplies `mpp` for each image or dataset.
   * Physical coordinates are computed as:

     * `x_um = X_centroid * mpp`
     * `y_um = Y_centroid * mpp`

2. Per image normalization:

   * For each `imageid`, we compute the minimum and maximum of `x_um` and `y_um` and rescale to the unit interval:

     * `x_norm = (x_um - x_min) / (x_max - x_min)`
     * `y_norm = (y_um - y_min) / (y_max - y_min)`
   * Optionally, we standardize across all images to zero mean and unit variance before feeding into the model.

### 2.2 Spatial encodings for nodes

Transformers do not natively understand geometry. We therefore convert normalized coordinates into spatial encoding vectors that are concatenated to the node features.

For each cell we use:

* Normalized coordinates: `x_norm` and `y_norm`.
* Fourier style positional encodings: sinusoidal functions of `x_norm` and `y_norm` at multiple frequencies to capture both local and global structure.

These spatial encodings are concatenated with the expression and mask features to form the final node representation.

### 2.3 Spatial encodings for edges

For each edge between cells u and v we compute:

* Euclidean distance in normalized or micron space.
* Angle between the two cells, represented as sine and cosine of the angle.
* Optional distance bins, such as near, intermediate, and far.

These edge-level spatial features are used as attention biases in the graph transformer so that nearby cells exert stronger influence than distant cells when appropriate.

## 3. Model Architecture

### 3.1 Local and global representations

The graph transformer produces **two complementary levels of representation** to capture tissue organization at different biological scales.

#### **Local node-level representation**

Each cell receives a latent embedding (z_i^{local}) derived from:

* its own expression profile,
* its spatial encodings,
* the phenotypic embedding (if available), and
* information aggregated from its immediate neighbors via multi-head attention.

This embedding captures:

* local microenvironments (e.g., T cell adjacent to DC),
* short-range signaling structure,
* cell–cell interaction motifs, and
* neighborhood phenotypic composition.

These **local embeddings** are used for:

* masked expression prediction,
* cell-type prediction,
* reconstructing local graph structure,
* quantifying perturbations at the cell or neighborhood level.

#### **Global graph-level representation**

To capture whole-tissue structure, we introduce a **learned global token** (analogous to a [CLS] token in NLP) that attends to all nodes and receives attention from all nodes.

This produces a **global embedding** (z^{global}) that summarizes:

* the overall immune or stromal landscape,
* tumor architecture and spatial gradients,
* global cellular diversity,
* large-scale organization (tumor core vs invasive front vs stroma).

The global token enables:

* global tissue classification (e.g., inflamed vs non-inflamed),
* harmonization across datasets,
* comparing whole-tissue latent states before and after perturbation,
* conditioning perturbation simulations on global tissue context.

Together, (z_i^{local}) and (z^{global}) allow the model to reason at fine-grained and whole-tissue scales simultaneously.

---

The model is a graph transformer with an encoder and decoder backbone.

The model is a graph transformer with an encoder and decoder backbone.

**Encoder:**

* Multi-head attention over nodes using spatially aware attention biases.
* Inputs include global expression projection, mask, cell-type embedding (optional), and spatial encodings.

**Latent space:**

* Dense representation of each cell capturing local and global tissue structure.

**Decoder:**

* Reconstructs the **full input tissue graph** at the level of cells, conditioned on the learned latent representation.
* Concretely, for each cell, the decoder predicts:

  * the expression profile in the global gene space (for all genes with `obs_mask = 1`),
  * the cell-type label if supervised (when a phenotype is available), and
  * optionally local adjacency structure.
* Spatial coordinates themselves are not predicted; the decoder is evaluated under the original geometry (same set of cells, same (x, y) positions). Thus, “reconstruction of the image” means reconstructing the per-cell feature fields (expression and phenotype) over the fixed spatial layout.

For practical use, the reconstruction head will return, for each cell in an image:

* the original coordinates `(x_um, y_um)` (or their normalized equivalents),
* the reconstructed expression vector in the global gene space,
* the reconstructed or predicted cell-type label (if the cell-type head is active),
  so that users can directly generate spatial scatter plots and compare original vs reconstructed expression or phenotypes over identical coordinates.

**Heads:**

* Masked expression reconstruction
* Optional cell-type prediction
* Optional adjacency reconstruction
* Optional tissue or sample label prediction

This architecture supports flexible self-supervision and modular perturbation modeling.

The model is a **graph transformer** with an encoder–decoder backbone.

**Encoder:**

* Multi-head attention over nodes using spatially aware attention biases.
* Inputs include global expression projection, mask, cell-type embedding (optional), and spatial encodings.

**Latent space:**

* Dense representation of each cell capturing local and global tissue structure.

**Decoder:**

* Reconstructs masked expressions, optionally reconstructs adjacency.

**Heads:**

* Masked expression reconstruction
* Optional cell-type prediction
* Optional adjacency reconstruction
* Optional tissue/sample label prediction

This architecture supports flexible self-supervision and modular perturbation modeling.

## 4. Masking Strategies

Self-supervision uses several masking strategies, always respecting true missingness (`obs_mask`). Loss is computed only for genes with `obs_mask = 1`.

**Expression masking:** Randomly mask 10–50% of measured genes; model predicts true expression.

**Edge masking:** Randomly or selectively drop edges; model learns robust neighborhood reasoning.

**Node-type masking:** If cell types exist, mask labels and predict them.

**Spatial masking:** Mask contiguous spatial regions (circles/patches) to force context-based inference.

## 5. Loss Functions

Total loss combines multiple objectives:

```
L_total = λ1 * L_expr_mask
        + λ2 * L_reconstruction
        + λ3 * L_celltype (optional)
        + λ4 * L_edge (optional)
        + λ5 * L_label (optional)
```

**L_expr_mask:** MSE for masked genes where obs_mask = 1.

**L_reconstruction:** Measures how well the decoder recovers the original tissue graph at the cell level. This includes:

* reconstruction of the per-cell expression vector in the global gene space for all genes with `obs_mask = 1`, and
* optionally reconstruction of cell-type labels and local adjacency.

Spatial coordinates are held fixed and not reconstructed; the focus is on reconstructing the **same tissue with the same spatial organization but with recovered expression profiles and, when present, cell-type labels.**

**L_celltype:** Cross entropy for predicting masked phenotypes.

**L_edge:** Binary cross-entropy for adjacency reconstruction.

**L_label:** Optional supervised tissue-level objective.

## 6. Training Protocol

Training proceeds over random graph crops of ~3–10k cells.

For each batch:

1. Apply masking.
2. Encode masked graph.
3. Decode to reconstruct masked items.
4. Compute losses and update weights.

Training runs 50–200 epochs depending on dataset size. Graph mini-batching ensures scalability to millions of cells.

## 7. Validation

Validation includes:

**Reconstruction-based:**

* Expression MSE
* KNN neighborhood preservation
* Adjacency overlap (if reconstructed)

**Biological validation:**

* UMAP/t-SNE of latent embeddings showing emergent structure.
* Separation of tumor vs stroma regions.
* Coherent immune spatial gradients.
* Attention patterns matching known interactions (e.g., DC–T cell contacts).

## 8. Perturbation Engine

The trained model acts as a digital twin.

**Gene-level perturbation:** Modify expression in selected cells and propagate through encoder.

**Interaction knockout:** Remove edges encoding interactions (e.g., antigen presentation) and compute new latent state.

**Cell-type ablation:** Remove nodes of a specific phenotype and recompute latent embeddings.

**Spatial perturbation:** Apply changes only within user-defined regions (e.g., tumor margin).

## 9. Quantification of Perturbation Effects

We quantify perturbation effects via:

* Latent distance shifts: ||Z_pert − Z_base||₂
* Neighborhood composition changes
* Edge gain/loss counts
* Local density redistribution
* Pseudo-spatial trajectories in latent space

These metrics reveal how perturbations reorganize tissue structure.

## 10. Implementation Plan for the Postdoc

**Modules:**

* Preprocessing tools for AnnData → graph conversion
* Global feature mapping utilities
* Graph construction module
* Graph transformer encoder/decoder
* Masking engine
* Loss functions
* Training loop
* Perturbation engine
* Latent analysis tools
* Visualization utilities

**Dependencies:** PyTorch, PyTorch Geometric, Scanpy, AnnData, UMAP-learn, networkx, einops

**Milestones:**

1. Global mapping + AnnData pipeline
2. Graph construction + loaders
3. Encoder–decoder prototype
4. Masking + loss integration
5. Validation suite
6. Perturbation engine
7. Final documentation

---

## 11. Software Package Design and Workflow

The ultimate goal is to deliver this framework as a modular Python package that is usable both from Jupyter notebooks and via a command-line interface (CLI). Development will proceed in stages, corresponding to the main functional components of the pipeline.

### 11.1 Preprocessing module

**Goal:** Starting from one or more AnnData objects (each corresponding to a panel or dataset), produce a single consolidated AnnData with harmonized structure, global gene mapping, and standardized metadata.

**Responsibilities:**

* Normalize panel-specific expression (e.g., arcsinh / log1p / z-score) and store in `adata.X` or `adata.layers["expr_norm"]`.
* Map panel markers to the global gene universe and create:

  * `adata.layers["global_expr"]` — sparse `(n_cells, G)` matrix,
  * `adata.layers["mask"]` — sparse `(n_cells, G)` binary mask.
* Standardize metadata columns (`phenotype`, `sample_type`, `tissue_type`, `disease`, `disease_subtype`, `imageid`), filling missing phenotypes with `No_label`.
* Combine multiple AnnData objects into one master `adata_all` with unique `imageid` values.

**Interface:**

* Python API: functions such as `normalize_panel`, `map_to_global_genes`, `add_metadata_defaults`, `combine_anndatas`.
* CLI entry point (e.g. `vt-preprocess`) that:

  * reads a list of `.h5ad` files and a gene-universe list,
  * performs the above steps with progress bars,
  * writes a consolidated `combined_preprocessed.h5ad`.

### 11.2 Data preparation for pre-training

**Goal:** Convert the consolidated AnnData into graph-ready data structures with spatial encodings and well-defined train/validation/test splits.

**Responsibilities:**

* Convert pixel coordinates to microns using an `mpp` parameter and store `x_um`, `y_um`.
* Per-image normalization to `x_norm`, `y_norm` and computation of node-level spatial encodings (including Fourier features).
* Construct graph splits at the **image level**:

  * assign each `imageid` to train, validation, or test,
  * stratify splits by metadata such as `sample_type` and presence of `phenotype`.
* Provide PyTorch / PyG datasets that:

  * build graphs from `imageid` subsets,
  * construct node and edge features on the fly.

**Interface:**

* Python API in `dataprep.spatial`, `dataprep.splits`, and `dataprep.dataset`.
* CLI entry point (e.g. `vt-dataprep`) that:

  * reads the consolidated AnnData,
  * adds spatial encodings using a user-specified `mpp`,
  * generates and saves a split definition (e.g., `splits.yaml`).

### 11.3 Model building

**Goal:** Implement the graph transformer encoder–decoder, masking strategies, and multi-task heads as modular PyTorch components, configured via a YAML file.

**Responsibilities:**

* Define the encoder, decoder, local/global representations, and global token.
* Implement masking strategies (expression, edge, node-type, spatial) that respect the `mask` layer.
* Implement loss functions (`L_expr_mask`, `L_reconstruction`, `L_celltype`, `L_edge`, `L_label`).
* Provide a factory function `build_model(config, gene_universe_size, n_celltypes, ...)` that instantiates the full model from configuration.

**Interface:**

* Python modules under `model/`:

  * `modules.py`, `masking.py`, `losses.py`, `factory.py`.
* YAML configuration controlling:

  * architecture parameters (`d_model`, `n_heads`, `n_layers`, `n_fourier_freqs`),
  * which heads are active,
  * loss weights.
* Optional CLI command (e.g. `vt-model-summary`) to print model details for a given config.

### 11.4 Model training

**Goal:** Provide a reusable training loop that supports both scripted training and interactive experimentation.

**Responsibilities:**

* Training and validation loops with:

  * CUDA/CPU detection and clear reporting,
  * `tqdm` progress bars for batches and epochs,
  * checkpointing of model weights and training state,
  * logging of training and validation metrics.
* Integration with the masking engine and multi-task losses.

**Interface:**

* Python API: `train_model(config, data, splits, output_dir)` in `training/train.py`.
* CLI entry point (e.g. `vt-train`) that:

  * takes a config YAML,
  * paths to data and splits,
  * an output directory for checkpoints and logs.

### 11.5 Model validation

**Goal:** Evaluate whether the trained model has learned faithful tissue representations at the cell level and in latent space.

**Responsibilities:**

* Reconstruction evaluation:

  * run encoder–decoder on held-out images,
  * export per-cell tables containing coordinates, original expression, reconstructed expression, original and predicted phenotype,
  * compute reconstruction metrics (MSE per marker, correlations, phenotype confusion matrices).
* Latent evaluation:

  * compute UMAP or other low-dimensional embeddings of local and global representations,
  * visualize clustering by `phenotype`, `sample_type`, and other metadata.

**Interface:**

* Python modules under `evaluation/`: `reconstruction.py`, `viz_spatial.py`, `metrics.py`.
* CLI entry point (e.g. `vt-validate-recon`) for running reconstruction checks on specified `imageid`s.

### 11.6 Perturbation engine

**Goal:** Provide a programmatic interface for in silico perturbations on held-out tissues using the trained virtual tissue model.

**Responsibilities:**

* Implement perturbation primitives:

  * gene expression modulation for selected genes and cell types,
  * cell-type ablation (removal of specific phenotypes),
  * interaction knockouts (edge removal according to user-specified interaction rules),
  * spatially localized perturbations restricted to user-defined regions.
* For each perturbation scenario:

  * clone the input graph,
  * apply perturbation,
  * run forward pass to obtain new local and global embeddings,
  * quantify changes using the perturbation metrics defined in Section 9.

**Interface:**

* Python modules under `perturbation/`: `perturb_engine.py`, `scenarios.py`.
* CLI entry point (e.g. `vt-perturb`) that:

  * loads a trained model and data,
  * applies a perturbation scenario described in a YAML file,
  * writes out perturbed embeddings, summary metrics, and any requested visualizations.

### 11.7 Cross-cutting design principles

* **Modularity:** Core logic (preprocessing, data prep, model, training, perturbation) is implemented in importable Python modules; CLIs are thin wrappers.
* **Dual notebook/CLI compatibility:** Every major step (preprocessing, training, validation, perturbation) exposes both a function-level API and a CLI command.
* **Transparency:** Verbose logging and progress bars document the exact steps performed, including device selection (CPU vs CUDA).
* **Extensibility:** New masking strategies, model variants, or perturbation types should be addable by extending the relevant modules without altering the package-wide API.

This software design plan provides a clear roadmap for implementing the virtual tissue model as a robust, user-facing Python package that supports end-to-end workflows from raw AnnData inputs to trained models and perturbation experiments.

& "C:\Users\aj\.conda\envs\vtissue\python.exe" examples/synthetic_tests/comprehensive_gps_test/run_training.py

& "C:\Users\aj\.conda\envs\vtissue\python.exe" examples/synthetic_tests/comprehensive_gps_test/visualize_comprehensive_results.py --noval

& "C:\Users\aj\.conda\envs\vtissue\python.exe" examples/synthetic_tests/local_niche_test/run_test.py 

& "C:\Users\aj\.conda\envs\vtissue\python.exe" examples/synthetic_tests/local_niche_test/visualize_results.py