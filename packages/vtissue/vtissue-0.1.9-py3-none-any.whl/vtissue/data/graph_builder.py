import torch
from torch_geometric.data import Data
import numpy as np
import pandas as pd
from typing import Optional, Dict
from sklearn.neighbors import NearestNeighbors, radius_neighbors_graph
from .spatial import SpatialEncoder

class GraphBuilder:
    """
    Constructs PyG Data objects from AnnData.
    """
    def __init__(
        self, 
        spatial_encoder: SpatialEncoder,
        k_neighbors: int = 10,
        radius: Optional[float] = None,
        phenotype_map: Optional[Dict[str, int]] = None,
        phenotype_col: Optional[str] = None,
        algorithm: str = 'auto',
        n_jobs: int = -1,
        x_col: str = 'X_centroid',
        y_col: str = 'Y_centroid'
    ):
        self.spatial_encoder = spatial_encoder
        self.k_neighbors = k_neighbors
        self.radius = radius
        self.phenotype_map = phenotype_map
        self.phenotype_col = phenotype_col
        self.algorithm = algorithm
        self.n_jobs = n_jobs
        self.x_col = x_col
        self.y_col = y_col
        
    def build(self, adata, min_vals=None, max_vals=None) -> Data:
        """
        Build a graph from a single image AnnData.
        """
        # 1. Get coordinates
        if self.x_col in adata.obs and self.y_col in adata.obs:
            coords = adata.obs[[self.x_col, self.y_col]].values.astype(np.float32)
        else:
            # Fallback or error
            raise ValueError("AnnData must have X_centroid and Y_centroid in obs.")
            
        # 2. Spatial encoding
        if min_vals is not None and max_vals is not None:
            norm_coords, micron_coords = self.spatial_encoder.normalize_coords(coords, min_vals=min_vals, max_vals=max_vals)
        else:
            norm_coords, micron_coords = self.spatial_encoder.normalize_coords(coords)
        norm_coords_t = torch.tensor(norm_coords, dtype=torch.float32)
        coords_abs_t = torch.tensor(coords, dtype=torch.float32)
        spatial_enc = self.spatial_encoder.compute_fourier_features(norm_coords_t)
        
        # 3. Graph construction (Edges)
        # Use sklearn
        n_samples = micron_coords.shape[0]
        
        if self.radius is not None:
            # Radius graph
            # radius_neighbors_graph returns sparse matrix
            adj = radius_neighbors_graph(
                micron_coords, 
                radius=self.radius, 
                mode='connectivity', 
                include_self=False,
                n_jobs=self.n_jobs
            )
            # Convert to edge_index
            row, col = adj.nonzero()
            edge_index = torch.tensor(np.stack([row, col]), dtype=torch.long)
        else:
            # KNN graph
            # Adjust k if n_samples is small
            k = min(self.k_neighbors, n_samples - 1)
            if k < 1:
                # No edges
                edge_index = torch.empty((2, 0), dtype=torch.long)
            else:
                nbrs = NearestNeighbors(
                    n_neighbors=k+1, 
                    algorithm=self.algorithm, 
                    n_jobs=self.n_jobs
                ).fit(micron_coords)
                distances, indices = nbrs.kneighbors(micron_coords)
                
                # Drop the first column (self)
                indices = indices[:, 1:]
                
                # Construct edge_index
                # Source nodes: 0, 0, ..., 1, 1, ...
                sources = np.repeat(np.arange(n_samples), k)
                targets = indices.flatten()
                
                edge_index = torch.tensor(np.stack([sources, targets]), dtype=torch.long)
            
        # 4. Node features (sparse-aware)
        # Build observed coordinate list and values without densifying
        n_cells = adata.shape[0]
        n_genes = adata.shape[1]
        if 'mask' in adata.layers:
            mask_m = adata.layers['mask']
        else:
            mask_m = None
        # Observed coords from mask if available; otherwise from X nonzeros
        if mask_m is not None and hasattr(mask_m, 'tocoo'):
            mask_coo = mask_m.tocoo()
            obs_rows_np = mask_coo.row.astype(np.int64)
            obs_cols_np = mask_coo.col.astype(np.int64)
        else:
            # Fallback: use expression nonzeros
            X_m = adata.X.tocoo() if hasattr(adata.X, 'tocoo') else None
            if X_m is None:
                raise ValueError("Expected sparse AnnData.X or layers['mask'] for global mapping")
            obs_rows_np = X_m.row.astype(np.int64)
            obs_cols_np = X_m.col.astype(np.int64)
        # Gather values for observed coords from X (zeros included via mask)
        X_src = adata.X
        if hasattr(X_src, 'toarray') and not hasattr(X_src, '__getitem__'):
            # Very unusual; assume CSR/COO provides __getitem__
            X_src = adata.X
        # Vectorized lookup of values at (rows, cols)
        vals_np = np.asarray(X_src[obs_rows_np, obs_cols_np]).reshape(-1).astype(np.float32)
        obs_rows = torch.tensor(obs_rows_np, dtype=torch.long)
        obs_cols = torch.tensor(obs_cols_np, dtype=torch.long)
        obs_vals = torch.tensor(vals_np, dtype=torch.float32)
        obs_ptr = torch.tensor([0, obs_rows.numel()], dtype=torch.long)
            
        # Metadata
        phenotype = None
        if self.phenotype_map and self.phenotype_col and self.phenotype_col in adata.obs:
            p_vals = adata.obs[self.phenotype_col].astype(object).map(self.phenotype_map).fillna(-1).values
            phenotype = torch.tensor(p_vals, dtype=torch.long)
            
        # Construct Data object
        data = Data(
            edge_index=edge_index,
            pos=norm_coords_t,
            spatial_enc=spatial_enc
        )
        # Attach sparse observation info and shape
        data.obs_rows = obs_rows
        data.obs_cols = obs_cols
        data.obs_vals = obs_vals
        data.obs_ptr = obs_ptr
        data.n_nodes = int(n_cells)
        data.n_genes = int(n_genes)
        data.coords = coords_abs_t
        
        if phenotype is not None:
            data.phenotype = phenotype

        return data
