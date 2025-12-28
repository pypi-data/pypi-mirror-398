#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
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


def is_noneish(x) -> bool:
    if x is None:
        return True
    if isinstance(x, str) and x.strip().lower() in ("", "none", "null"):
        return True
    return False


def safe_slug(x: str, max_len: int = 120) -> str:
    """Make a filesystem-safe token for filenames."""
    x = str(x).strip()
    x = re.sub(r"\s+", "_", x)
    x = re.sub(r"[^A-Za-z0-9._-]+", "-", x)
    x = re.sub(r"-{2,}", "-", x).strip("-")
    return x[:max_len] if len(x) > max_len else x


def apply_template(filename_template: str, imageid: str) -> str:
    """Apply {imageid} template if present; otherwise return as-is."""
    if "{imageid}" in filename_template:
        return filename_template.format(imageid=imageid)
    return filename_template


def main():
    p = argparse.ArgumentParser(
        description="Read .h5ad -> run UMAP on adata.obsm embedding -> save UMAP + spatial scatter PNGs per imageid."
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
    p.add_argument("--imageid-col", default="imageid", help="obs column defining sample/image IDs")

    # UMAP plot params
    p.add_argument(
        "--umap-color",
        default="",
        help="obs column (or gene) to color UMAP by. Default: no coloring (plain scatter).",
    )
    p.add_argument("--umap-s", type=float, default=0.1, help="UMAP scatter point size")
    p.add_argument("--umap-figsize", default="5,5", help="UMAP figsize as 'W,H'")
    p.add_argument(
        "--umap-filename",
        default="umap_{imageid}.png",
        help="UMAP output filename (supports {imageid})",
    )

    # Spatial plot params (genes passed via CLI)
    p.add_argument(
        "--spatial-genes",
        default="SOX10,ITGAX,CD3D",
        help="Comma-separated genes (or obs fields) to plot in spatial scatter (default: expression-like features)",
    )
    p.add_argument("--spatial-layer", default="vt_expr_pred", help="Layer to use for gene coloring")
    p.add_argument("--spatial-s", type=float, default=0.5, help="Spatial scatter point size")
    p.add_argument("--spatial-figsize", default="5,5", help="Spatial figsize as 'W,H'")
    p.add_argument("--spatial-vmax", default="None", help="Numeric vmax or 'None'")
    p.add_argument(
        "--spatial-filename",
        default="spatial_{imageid}.png",
        help="Spatial output filename (supports {imageid})",
    )

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

    # ---- Run UMAP once (global) ----
    embedding, umap_model, train_idx = run_umap_large(adata.obsm[args.emb_key])

    bdata = adata.copy()
    bdata.obsm[args.umap_key] = embedding

    # Determine image IDs
    if args.imageid_col in bdata.obs.columns:
        image_ids = list(bdata.obs[args.imageid_col].astype(str).unique())
    else:
        image_ids = ["all"]
        print(f"[WARN] obs column '{args.imageid_col}' not found; plotting a single set for the full AnnData.")

    # Shared params
    umap_w, umap_h = [float(x) for x in args.umap_figsize.split(",")]
    spatial_w, spatial_h = [float(x) for x in args.spatial_figsize.split(",")]
    spatial_genes = parse_csv_list(args.spatial_genes)

    vmax = None
    if not is_noneish(args.spatial_vmax):
        vmax = float(args.spatial_vmax)

    umap_color = None if is_noneish(args.umap_color) else args.umap_color

    saved = []

    # ---- Plot per imageid ----
    multiple = len(image_ids) > 1

    for imageid in image_ids:
        if imageid == "all" and args.imageid_col not in bdata.obs.columns:
            vdata = bdata
        else:
            mask = bdata.obs[args.imageid_col].astype(str) == str(imageid)
            vdata = bdata[mask].copy()

        slug = safe_slug(imageid)

        umap_fname = apply_template(args.umap_filename, slug)
        spatial_fname = apply_template(args.spatial_filename, slug)

        # If user removed {imageid} but there are multiple images, prefix to avoid overwriting
        if multiple and "{imageid}" not in args.umap_filename:
            umap_fname = f"{slug}__{umap_fname}"
        if multiple and "{imageid}" not in args.spatial_filename:
            spatial_fname = f"{slug}__{spatial_fname}"

        # ---- Save UMAP plot ----
        umap(
            vdata,
            color=umap_color,  # default None => plain scatter
            s=args.umap_s,
            figsize=(umap_w, umap_h),
            label=args.umap_key,
            saveDir=args.outdir,
            fileName=umap_fname,
        )

        # ---- Save Spatial plot ----
        spatial_scatterPlot(
            adata=vdata,
            colorBy=spatial_genes,       # default expression-like genes list
            s=args.spatial_s,
            layer=args.spatial_layer,    # default vt_expr_pred
            vmax=vmax,
            figsize=(spatial_w, spatial_h),
            saveDir=args.outdir,
            fileName=spatial_fname,
            plot_tool="matplotlib",  # ensures PNG save without needing plotly export deps
        )

        saved.append((umap_fname, spatial_fname))

    print("Saved:")
    for u, s in saved:
        print("  ", os.path.join(args.outdir, u))
        print("  ", os.path.join(args.outdir, s))


if __name__ == "__main__":
    main()
