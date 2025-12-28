#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import importlib.util

# Headless-safe for Slurm / servers
import matplotlib
matplotlib.use("Agg")  # must be set before pyplot is imported anywhere

import anndata as ad


def import_from_path(module_path: str, module_name: str):
    """Dynamically import a Python module from a file path."""
    module_path = os.path.abspath(module_path)
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Module path not found: {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for module: {module_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_csv_list(s: str):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def main():
    p = argparse.ArgumentParser(
        description="Read .h5ad -> run UMAP on adata.obsm embedding -> save UMAP + spatial scatter PNGs."
    )

    # I/O
    p.add_argument("--h5ad", required=True, help="Path to input .h5ad")
    p.add_argument("--outdir", required=True, help="Output directory for PNGs")

    # Paths to helper scripts
    p.add_argument("--umap-tool", required=True, help="Path to umap_tool.py (provides run_umap_large)")
    p.add_argument("--umap-plot", required=True, help="Path to umap_plot.py (provides umap plotting function)")
    p.add_argument(
        "--spatial-plot",
        required=True,
        help="Path to spatial_scatterPlot_withplotly_sparse.py (provides spatial_scatterPlot)",
    )

    # Data keys
    p.add_argument("--emb-key", default="vt_node_emb", help="Key in adata.obsm for input embedding")
    p.add_argument("--umap-key", default="umap", help="Key in adata.obsm to store UMAP coords")

    # UMAP plot params
    p.add_argument("--umap-color", default="phenotype", help="obs column (or gene) to color UMAP by")
    p.add_argument("--umap-s", type=float, default=0.1, help="UMAP scatter point size")
    p.add_argument("--umap-figsize", default="5,5", help="UMAP figsize as 'W,H'")
    p.add_argument("--umap-filename", default="umap.png", help="UMAP output filename")

    # Spatial plot params (genes passed via CLI)
    p.add_argument(
        "--spatial-genes",
        default="SOX10,ITGAX,CD3D",
        help="Comma-separated genes (or obs fields) to plot in spatial scatter",
    )
    p.add_argument("--spatial-layer", default="vt_expr_pred", help="Layer to use for gene coloring")
    p.add_argument("--spatial-s", type=float, default=0.5, help="Spatial scatter point size")
    p.add_argument("--spatial-figsize", default="5,5", help="Spatial figsize as 'W,H'")
    p.add_argument("--spatial-vmax", default="None", help="Numeric vmax or 'None'")
    p.add_argument("--spatial-filename", default="spatial_scatter.png", help="Spatial output filename")

    args = p.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # ---- Dynamic imports of your helper scripts ----
    umap_tool_mod = import_from_path(args.umap_tool, "umap_tool_mod")
    umap_plot_mod = import_from_path(args.umap_plot, "umap_plot_mod")
    spatial_plot_mod = import_from_path(args.spatial_plot, "spatial_plot_mod")

    if not hasattr(umap_tool_mod, "run_umap_large"):
        raise AttributeError("umap_tool.py must define: run_umap_large")
    if not hasattr(umap_plot_mod, "umap"):
        raise AttributeError("umap_plot.py must define: umap")
    if not hasattr(spatial_plot_mod, "spatial_scatterPlot"):
        raise AttributeError("spatial_scatterPlot_withplotly_sparse.py must define: spatial_scatterPlot")

    run_umap_large = umap_tool_mod.run_umap_large
    umap = umap_plot_mod.umap
    spatial_scatterPlot = spatial_plot_mod.spatial_scatterPlot

    # ---- Load data ----
    adata = ad.read_h5ad(args.h5ad)
    if args.emb_key not in adata.obsm:
        raise KeyError(f"Missing adata.obsm['{args.emb_key}'].")

    # ---- Run UMAP ----
    embedding, umap_model, train_idx = run_umap_large(adata.obsm[args.emb_key])

    bdata = adata.copy()
    bdata.obsm[args.umap_key] = embedding

    # ---- Save UMAP plot ----
    umap_w, umap_h = [float(x) for x in args.umap_figsize.split(",")]
    umap(
        bdata,
        color=args.umap_color,
        s=args.umap_s,
        figsize=(umap_w, umap_h),
        label=args.umap_key,
        saveDir=args.outdir,
        fileName=args.umap_filename,
    )

    # ---- Save Spatial plot ----
    spatial_w, spatial_h = [float(x) for x in args.spatial_figsize.split(",")]
    spatial_genes = parse_csv_list(args.spatial_genes)

    vmax = None
    if str(args.spatial_vmax).lower() not in ("none", "", "null"):
        vmax = float(args.spatial_vmax)

    spatial_scatterPlot(
        adata=bdata,
        colorBy=spatial_genes,
        s=args.spatial_s,
        layer=args.spatial_layer,
        vmax=vmax,
        figsize=(spatial_w, spatial_h),
        saveDir=args.outdir,
        fileName=args.spatial_filename,
        plot_tool="matplotlib",  # ensures PNG save without needing plotly export deps
    )

    print("Saved:")
    print("  ", os.path.join(args.outdir, args.umap_filename))
    print("  ", os.path.join(args.outdir, args.spatial_filename))


if __name__ == "__main__":
    main()
