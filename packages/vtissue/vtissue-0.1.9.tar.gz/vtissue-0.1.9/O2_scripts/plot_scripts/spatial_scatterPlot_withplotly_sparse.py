# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 13:18:25 2025

@author: aj

Modified on request:
- Avoids densifying the full expression matrix.
- Densifies only the requested columns from X / raw / layers.
"""

import anndata as ad
import pathlib
import matplotlib.pyplot as plt
import pandas as pd
import math
import numpy as np
import matplotlib.patches as mpatches
import os
import plotly.express as px
import plotly.io as pio

plt.rcParams['pdf.fonttype'] = 42
pio.renderers.default = 'browser'


def _get_expression_column(bdata, gene, layer=None):
    """
    Return a dense 1D numpy array for a single gene from:
    - bdata.X (default)
    - bdata.raw.X (if layer == 'raw')
    - bdata.layers[layer] (if a named layer)
    Only this column is densified; the full matrix remains sparse.
    """
    if layer is None:
        mat = bdata.X
        var_names = bdata.var_names
    elif layer == 'raw':
        if bdata.raw is None:
            raise ValueError("AnnData.raw is None but layer='raw' was requested.")
        mat = bdata.raw.X
        # Assumes raw.var_names align with bdata.var_names as in the original code.
        var_names = bdata.var_names
    else:
        if layer not in bdata.layers:
            raise KeyError(f"Layer '{layer}' not found in AnnData.layers")
        mat = bdata.layers[layer]
        var_names = bdata.var_names

    if gene not in var_names:
        raise KeyError(f"Gene '{gene}' not found in var_names for the selected layer.")

    gene_idx = var_names.get_loc(gene)

    # Handle sparse and dense cases
    if hasattr(mat, "toarray") or hasattr(mat, "tocsc") or hasattr(mat, "tocsr"):
        # Treat as sparse: slice one column and densify only that
        col = mat[:, gene_idx]
        if hasattr(col, "toarray"):
            col = col.toarray().ravel()
        else:
            col = np.asarray(col).ravel()
    else:
        # Dense numpy array
        col = np.asarray(mat[:, gene_idx]).ravel()

    return col


def spatial_scatterPlot(
    adata,
    colorBy,
    topLayer=None,
    x_coordinate='X_centroid',
    y_coordinate='Y_centroid',
    imageid='imageid',
    layer=None,
    subset=None,
    s=None,
    ncols=None,
    alpha=1,
    dpi=200,
    fontsize=None,
    plotLegend=True,
    cmap='RdBu_r',
    catCmap='tab20',
    vmin=None,
    vmax=None,
    customColors=None,
    figsize=(5, 5),
    invert_yaxis=True,
    saveDir=None,
    fileName='scimapScatterPlot.png',
    plot_tool='matplotlib',
    **kwargs,
):
    # Load the anndata object
    if isinstance(adata, str):
        adata = ad.read_h5ad(adata)
    else:
        adata = adata.copy()

    # Subset by image id if requested
    if subset is not None:
        if isinstance(subset, str):
            subset = [subset]
        if layer == 'raw':
            bdata = adata.copy()
            # Keep parity with original behavior: use raw.X as the working matrix
            bdata.X = adata.raw.X
            bdata = bdata[bdata.obs[imageid].isin(subset)]
        else:
            bdata = adata.copy()
            bdata = bdata[bdata.obs[imageid].isin(subset)]
    else:
        bdata = adata.copy()

    meta = bdata.obs

    if isinstance(topLayer, str):
        topLayer = [topLayer]

    if isinstance(colorBy, str):
        colorBy = [colorBy]

    # Build a dict of columns to color by, densifying only the requested genes
    colorColumns = {}
    for col in colorBy:
        if col in bdata.var_names:
            # Expression column from X / raw / layer
            col_vals = _get_expression_column(bdata, col, layer=layer)
            colorColumns[col] = pd.Series(col_vals, index=bdata.obs.index, name=col)
        elif col in meta.columns:
            # Metadata column
            colorColumns[col] = meta[col]
        else:
            raise KeyError(
                f"'{col}' not found in AnnData.var_names or AnnData.obs columns."
            )

    x = meta[x_coordinate]
    y = meta[y_coordinate]

    # Point size scaling
    n_panels = max(len(colorColumns), 1)
    if s is None:
        s = (10000 / bdata.shape[0]) / n_panels

    if plot_tool == 'matplotlib':
        def calculate_grid_dimensions(num_items, num_columns=None):
            if num_columns is None:
                num_rows_columns = int(math.ceil(math.sqrt(num_items)))
                return num_rows_columns, num_rows_columns
            else:
                num_rows = int(math.ceil(num_items / num_columns))
                return num_rows, num_columns

        nrows, ncols_calc = calculate_grid_dimensions(len(colorColumns), num_columns=ncols)
        fig, axs = plt.subplots(nrows=nrows, ncols=ncols_calc, figsize=figsize, dpi=dpi, constrained_layout=True)
        axs = axs.flatten() if isinstance(axs, np.ndarray) else [axs]

        cmap_cat = plt.get_cmap(catCmap)

        for i, (col, series) in enumerate(colorColumns.items()):
            ax = axs[i]
            if invert_yaxis:
                ax.invert_yaxis()

            values = series.values

            if series.dtype.kind in 'iufc':
                # Continuous / numeric
                scatter = ax.scatter(
                    x=x, y=y, c=values, cmap=cmap, s=s, vmin=vmin,
                    vmax=vmax, linewidths=0, alpha=alpha, **kwargs
                )
                if plotLegend:
                    cbar = plt.colorbar(scatter, ax=ax, pad=0)
                    cbar.ax.tick_params(labelsize=fontsize)
            else:
                # Categorical
                categories = pd.unique(series)
                colors = {
                    cat: customColors[cat] if (customColors is not None and cat in customColors)
                    else cmap_cat(i_cat)
                    for i_cat, cat in enumerate(categories)
                }

                categories_to_plot_last = [cat for cat in (topLayer or []) if cat in categories]
                categories_to_plot_first = [cat for cat in categories if cat not in categories_to_plot_last]

                for cat in categories_to_plot_first + categories_to_plot_last:
                    mask = (series == cat).values
                    ax.scatter(
                        x=x[mask], y=y[mask],
                        c=[colors[cat]], s=s, linewidths=0, alpha=alpha, **kwargs
                    )

                if plotLegend:
                    handles = [mpatches.Patch(color=colors[cat], label=cat) for cat in categories]
                    ax.legend(handles=handles, bbox_to_anchor=(1.0, 1.0),
                              loc='upper left', fontsize=fontsize)

            ax.set_title(col)
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_xticklabels([]); ax.set_yticklabels([])

        # Remove any unused axes
        for i in range(len(colorColumns), len(axs)):
            fig.delaxes(axs[i])

        #plt.tight_layout()
        if saveDir:
            os.makedirs(saveDir, exist_ok=True)
            full_path = os.path.join(saveDir, fileName)
            plt.savefig(full_path, dpi=dpi)
            plt.close()
            print(f"Saved plot to {full_path}")
        else:
            plt.show()

    elif plot_tool == 'plotly':
        for col, series in colorColumns.items():
            values = series.values
            df_plot = pd.DataFrame({
                'x': x.values,
                'y': y.values,
                'color': values
            })

            is_numeric = series.dtype.kind in 'iufc'

            fig = px.scatter(
                df_plot,
                x='x',
                y='y',
                color='color',
                opacity=alpha,
                color_continuous_scale=cmap if is_numeric else None,
                color_discrete_sequence=(
                    px.colors.qualitative.Set3 if not is_numeric else None
                ),
            )

            fig.update_traces(marker=dict(size=s))

            fig.update_layout(
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                    showline=False
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                    showline=False,
                    autorange='reversed'
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=10, r=10, t=10, b=10)
            )

            if saveDir:
                os.makedirs(saveDir, exist_ok=True)
                full_path = os.path.join(saveDir, fileName)
                if fileName.endswith('.html'):
                    fig.write_html(full_path)
                elif fileName.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.svg')):
                    fig.write_image(full_path)
                else:
                    raise ValueError(
                        "Unsupported file format for Plotly. Use .html, .png, .svg, etc."
                    )
                print(f"Saved plot to {full_path}")
            else:
                fig.show()
    else:
        raise ValueError("plot_tool must be 'matplotlib' or 'plotly'")
