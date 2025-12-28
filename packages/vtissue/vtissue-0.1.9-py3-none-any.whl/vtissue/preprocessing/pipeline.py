import anndata as ad
import pandas as pd
import re
from typing import List, Optional
from .gene_mapping import GlobalGeneMapper
from .normalization import normalize_expression, standardize_metadata
import numpy as np
import math
from typing import Union
import scipy.sparse as sp

def preprocess_dataset(
    adatas: List[ad.AnnData],
    gene_list_path: str,
    normalization_method: str = 'arcsinh',
    normalization_cofactor: float = 5.0
) -> ad.AnnData:
    """
    Preprocess and combine multiple AnnData objects into a single global AnnData.
    
    Args:
        adatas: List of AnnData objects (one per image or dataset).
        gene_list_path: Path to global gene list.
        normalization_method: Method for expression normalization.
        normalization_cofactor: Cofactor for arcsinh.
        
    Returns:
        combined_adata: Single AnnData with global gene space.
    """
    mapper = GlobalGeneMapper(gene_list_path)
    processed_adatas = []
    
    for i, adata in enumerate(adatas):
        # 1. Standardize metadata
        adata = standardize_metadata(adata)
        
        # 2. Normalize expression (panel-specific)
        # We normalize BEFORE mapping because we want the values to be comparable
        # assuming similar dynamic range across panels.
        adata = normalize_expression(
            adata, 
            method=normalization_method, 
            cofactor=normalization_cofactor
        )
        
        # 3. Map to global genes
        global_expr, mask, unmapped_genes = mapper.create_global_matrices(adata)
        
        # Log unmapped genes
        if len(unmapped_genes) > 0:
            img_id = str(adata.obs.get('imageid', ['Unknown'])[0]) if 'imageid' in adata.obs else "Unknown"
            print(f"[Gene Mapping] Image: {img_id} - Unmapped genes ({len(unmapped_genes)}): {unmapped_genes}")
        
        # 4. Create new AnnData in global space
        # We create a new AnnData where vars are the global genes
        new_adata = ad.AnnData(
            X=global_expr,
            obs=adata.obs.copy()
        )
        new_adata.layers['mask'] = mask
        new_adata.var_names = mapper.genes
        
        # Store unmapped genes in uns
        if 'vt_preprocess' not in new_adata.uns:
            new_adata.uns['vt_preprocess'] = {}
        new_adata.uns['vt_preprocess']['unmapped_genes'] = unmapped_genes
        
        # Preserve imageid uniqueness if needed? 
        # For now assume user handles it or we just concat.
        
        processed_adatas.append(new_adata)
        
    # 5. Concatenate
    if len(processed_adatas) == 0:
        raise ValueError("No AnnData objects provided.")
        
    combined_adata = ad.concat(processed_adatas, join='outer')
    
    # Ensure var_names are correct (concat might mess up if they are identical but it should be fine)
    combined_adata.var_names = mapper.genes
    
    return combined_adata

def preprocess_and_save(
    inputs: List[Union[ad.AnnData, str]],
    gene_list_path: str,
    output_path: str,
    input_layer: Optional[str] = None,
    normalization_method: Optional[str] = None,
    normalization_cofactor: float = 5.0,
    skip_mapping: bool = False
) -> str:
    mapper = GlobalGeneMapper(gene_list_path)
    processed_adatas = []
    total = len(inputs)
    for idx, item in enumerate(inputs, start=1):
        print(f"[{idx}/{total}] Loading: {item}")
        adata = ad.read_h5ad(item) if isinstance(item, str) else item
        print(f"[{idx}/{total}] Loaded shape: {adata.shape}")
        adata = standardize_metadata(adata)
        map_layer = input_layer
        if normalization_method:
            print(f"[{idx}/{total}] Normalizing: {normalization_method} (source={input_layer or 'X'})")
            if input_layer and input_layer in adata.layers:
                layer_mat = adata.layers[input_layer]
                try:
                    X_src = layer_mat.toarray() if hasattr(layer_mat, 'toarray') else layer_mat
                except Exception:
                    X_src = layer_mat
                prev_X = adata.X
                adata.X = X_src
                adata = normalize_expression(
                    adata,
                    method=normalization_method,
                    cofactor=normalization_cofactor
                )
                map_layer = None
            else:
                adata = normalize_expression(
                    adata,
                    method=normalization_method,
                    cofactor=normalization_cofactor
                )
                map_layer = None
        if skip_mapping:
            print(f"[{idx}/{total}] Skipping gene mapping; using layer: {map_layer or input_layer or 'X'}")
            if normalization_method:
                src = adata.X
            else:
                if input_layer and input_layer in adata.layers:
                    src = adata.layers[input_layer]
                else:
                    src = adata.X
            # Build sparse X_out from non-zero entries to ensure downstream sparse compatibility
            if hasattr(src, 'tocsr'):
                X_out = src.tocsr()
            else:
                try:
                    arr = np.asarray(src)
                    r, c = np.nonzero(arr)
                    if r.size > 0:
                        d = arr[r, c].astype(np.float32)
                        X_out = sp.coo_matrix((d, (r, c)), shape=adata.shape, dtype=np.float32).tocsr()
                    else:
                        X_out = sp.csr_matrix(adata.shape, dtype=np.float32)
                except Exception:
                    X_out = sp.csr_matrix(adata.shape, dtype=np.float32)
            # Create mask with the same sparsity pattern (1s where X_out has values)
            if X_out.nnz > 0:
                mask = X_out.copy()
                mask.data = np.ones_like(mask.data, dtype=np.float32)
            else:
                mask = sp.csr_matrix(adata.shape, dtype=np.float32)
            new_adata = ad.AnnData(
                X=X_out,
                obs=adata.obs.copy()
            )
            new_adata.layers['mask'] = mask
            new_adata.var_names = adata.var_names.copy()
            if adata.uns:
                new_adata.uns = adata.uns.copy()
            try:
                if 'vt_preprocess' not in new_adata.uns:
                    new_adata.uns['vt_preprocess'] = {}
                new_adata.uns['vt_preprocess']['skip_mapping'] = True
            except Exception:
                pass
            for lname in list(adata.layers.keys()):
                if lname == 'mask':
                    continue
                new_adata.layers[lname] = adata.layers[lname]
            if adata.obsm:
                new_adata.obsm = adata.obsm.copy()
        else:
            print(f"[{idx}/{total}] Mapping to global genes from layer: {map_layer or 'X'}")
            global_expr, mask, unmapped_genes = mapper.create_global_matrices(adata, layer=map_layer)
            
            if len(unmapped_genes) > 0:
                img_id = str(adata.obs.get('imageid', ['Unknown'])[0]) if 'imageid' in adata.obs else "Unknown"
                print(f"[Gene Mapping] Image: {img_id} - Unmapped genes ({len(unmapped_genes)}): {unmapped_genes}")
            
            new_adata = ad.AnnData(
                X=global_expr,
                obs=adata.obs.copy()
            )
            new_adata.layers['mask'] = mask
            new_adata.var_names = mapper.genes
            if adata.uns:
                new_adata.uns = adata.uns.copy()
            
            if 'vt_preprocess' not in new_adata.uns:
                new_adata.uns['vt_preprocess'] = {}
            new_adata.uns['vt_preprocess']['unmapped_genes'] = unmapped_genes
                
            for lname in list(adata.layers.keys()):
                if lname in ('global_expr', 'mask'):
                    continue
                print(f"[{idx}/{total}] Mapping layer: {lname}")
                expr_l, _mask_l, _ = mapper.create_global_matrices(adata, layer=lname)
                new_adata.layers[lname] = expr_l
            if adata.obsm:
                new_adata.obsm = adata.obsm.copy()
        processed_adatas.append(new_adata)
    if len(processed_adatas) == 0:
        raise ValueError("No inputs provided for preprocessing.")
    print("Concatenating preprocessed inputs...")
    combined_adata = ad.concat(processed_adatas, join='outer')
    if not skip_mapping:
        combined_adata.var_names = mapper.genes
    print(f"Saving combined AnnData to: {output_path}")
    combined_adata.write(output_path)
    return output_path

def assign_patches(adata: ad.AnnData, config: dict) -> None:
    cols = config.get('columns', {})
    image_col = cols.get('image_id', 'imageid')
    x_col = cols.get('x_centroid', 'X_centroid')
    y_col = cols.get('y_centroid', 'Y_centroid')
    patch_cfg = config.get('patching', {})
    if 'patch_id' not in adata.obs.columns:
        adata.obs['patch_id'] = ''
    else:
        try:
            adata.obs['patch_id'] = adata.obs['patch_id'].astype(str)
        except Exception:
            pass
    unique_images = sorted(adata.obs[image_col].astype(str).unique())

    # Check for name collisions after sanitization
    sanitized_map = {}
    seen_sanitized = set()
    collision_detected = False
    for val in unique_images:
        s = re.sub(r"[^A-Za-z0-9_\-]", "_", str(val))
        if s in seen_sanitized:
            collision_detected = True
        seen_sanitized.add(s)
        sanitized_map[val] = s

    for img_idx, img_id in enumerate(unique_images):
        mask_img = adata.obs[image_col].astype(str) == str(img_id)
        N = int(mask_img.sum())
        if N == 0:
            continue
        if not patch_cfg.get('enabled', False):
            adata.obs.loc[mask_img, 'patch_id'] = adata.obs.loc[mask_img, image_col].astype(str) + '_p0'
            continue
        xs = adata.obs.loc[mask_img, x_col].values
        ys = adata.obs.loc[mask_img, y_col].values
        x_min = float(xs.min()); x_max = float(xs.max())
        y_min = float(ys.min()); y_max = float(ys.max())
        grid = patch_cfg.get('grid_size', None)
        if grid and isinstance(grid, (list, tuple)) and len(grid) == 2:
            nx = int(grid[0]); ny = int(grid[1])
        else:
            max_cells_per_patch = max(1, int(patch_cfg.get('max_cells_per_patch', 50000)))
            n_target = max(1, math.ceil(N / max_cells_per_patch))
            nx = int(math.ceil(math.sqrt(n_target)))
            ny = int(math.ceil(n_target / max(1, nx)))
        x_edges = np.linspace(x_min, x_max, nx + 1)
        y_edges = np.linspace(y_min, y_max, ny + 1)
        ox = float(patch_cfg.get('overlap_fraction', 0.0))
        dx = (x_max - x_min) / max(1, nx)
        dy = (y_max - y_min) / max(1, ny)
        expand_x = 0.5 * ox * dx
        expand_y = 0.5 * ox * dy
        x_edges_exp = x_edges.copy(); y_edges_exp = y_edges.copy()
        x_edges_exp[0] -= expand_x; x_edges_exp[-1] += expand_x
        y_edges_exp[0] -= expand_y; y_edges_exp[-1] += expand_y
        ix = np.clip(np.digitize(xs, x_edges_exp, right=True) - 1, 0, nx - 1)
        iy = np.clip(np.digitize(ys, y_edges_exp, right=True) - 1, 0, ny - 1)
        
        # Use actual image ID (sanitized) for patch naming
        safe_id = sanitized_map[img_id]
        if collision_detected:
            # Fallback to index prefix if collision prevents unique naming
            safe_id = f"img{img_idx}_{safe_id}"
        patch_names = np.array([f"{safe_id}_p{int(a)}_{int(b)}" for a, b in zip(ix, iy)], dtype=object)
        
        # Assign safely using boolean mask to avoid issues with duplicate indices
        adata.obs.loc[mask_img, 'patch_id'] = patch_names
    if patch_cfg.get('enabled', False):
        assert adata.obs['patch_id'].isna().sum() == 0
