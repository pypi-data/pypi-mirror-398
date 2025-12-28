import numpy as np
import torch
from typing import Optional, Dict
from .spatial import SpatialEncoder

def _build_edge_index(micron_coords: np.ndarray, spatial_cfg: Dict) -> np.ndarray:
    from sklearn.neighbors import NearestNeighbors, radius_neighbors_graph
    n = micron_coords.shape[0]
    radius = spatial_cfg.get('radius', None)
    n_jobs = spatial_cfg.get('n_jobs', -1)
    if radius is not None:
        adj = radius_neighbors_graph(
            micron_coords,
            radius=radius,
            mode='connectivity',
            include_self=False,
            n_jobs=n_jobs
        )
        row, col = adj.nonzero()
        return np.stack([row, col])
    else:
        algorithm = spatial_cfg.get('algorithm', 'auto')
        k = int(spatial_cfg.get('k_neighbors', 10))
        k = max(1, min(k, n - 1)) if n > 1 else 0
        if k < 1:
            return np.empty((2, 0), dtype=np.int64)
        nbrs = NearestNeighbors(n_neighbors=k+1, algorithm=algorithm, n_jobs=n_jobs).fit(micron_coords)
        _, indices = nbrs.kneighbors(micron_coords)
        indices = indices[:, 1:]
        sources = np.repeat(np.arange(n), k)
        targets = indices.flatten()
        return np.stack([sources, targets])

def _score_vector(x: np.ndarray, edge_index: np.ndarray, method: str) -> float:
    if x.size == 0:
        return 0.0
    x = x.astype(np.float32)
    mu = float(x.mean())
    var = float(((x - mu) ** 2).sum())
    if var == 0.0:
        return 0.0
    if method == 'variance':
        return var / x.size
    src, dst = edge_index
    if src.size == 0:
        return 0.0
    w_sum = float(src.size)
    if method == 'moran':
        num = float(((x[src] - mu) * (x[dst] - mu)).sum())
        return (x.size / w_sum) * (num / var)
    elif method == 'geary':
        num = float(((x[src] - x[dst]) ** 2).sum())
        C = ((x.size - 1) / (2.0 * w_sum)) * (num / var)
        return 1.0 / (C + 1e-8)
    elif method == 'laplacian':
        num = float(((x[src] - x[dst]) ** 2).sum())
        rough = num / w_sum if w_sum > 0 else 0.0
        return 1.0 / (rough + 1e-8) if rough > 0 else 0.0
    else:
        return var / x.size

def compute_spatial_gene_weights(
    adata,
    image_id_col: str,
    x_col: str,
    y_col: str,
    spatial_config: Dict,
    method: str = 'moran',
) -> np.ndarray:
    image_ids = adata.obs[image_id_col].unique()
    mpp = spatial_config.get('default_mpp', 0.5)
    encoder = SpatialEncoder(mpp=mpp, n_fourier_freqs=spatial_config.get('n_fourier_freqs', 10))
    G = int(adata.shape[1])
    scores_sum = np.zeros(G, dtype=np.float64)
    counts = np.zeros(G, dtype=np.int64)
    for img_id in image_ids:
        mask = adata.obs[image_id_col] == img_id
        coords = adata.obs.loc[mask, [x_col, y_col]].values.astype(np.float32)
        norm_coords, micron_coords = encoder.normalize_coords(coords)
        edge_index = _build_edge_index(micron_coords, spatial_config)
        Xi = adata.X[mask.values]
        # Use global mask to skip genes not observed in this image
        observed_cols = None
        try:
            if 'mask' in adata.layers:
                Mi = adata.layers['mask'][mask.values]
                if hasattr(Mi, 'tocsc'):
                    nnz = Mi.tocsc().getnnz(axis=0)
                else:
                    nnz = np.count_nonzero(np.asarray(Mi), axis=0)
                observed_cols = np.where(nnz > 0)[0]
        except Exception:
            observed_cols = None
        if Xi.shape[0] < 2:
            continue
        # Compute per-gene score
        is_sparse = hasattr(Xi, 'tocsc')
        if is_sparse:
            Xi_c = Xi.tocsc()
        col_iter = (observed_cols if observed_cols is not None else range(G))
        for g in col_iter:
            if is_sparse:
                xg = Xi_c[:, g].toarray().ravel().astype(np.float32)
            else:
                xg = np.asarray(Xi[:, g], dtype=np.float32)
            s = _score_vector(xg, edge_index, method)
            scores_sum[g] += s
            counts[g] += 1
    # Aggregate across images
    scores = np.zeros(G, dtype=np.float32)
    valid = counts > 0
    if valid.any():
        scores[valid] = (scores_sum[valid] / counts[valid]).astype(np.float32)
    # Normalize to positive weights
    scores = np.clip(scores, a_min=0.0, a_max=None)
    total = float(scores.sum())
    if total == 0.0:
        # Default to uniform
        scores = np.ones(G, dtype=np.float32) / G
    else:
        scores = scores / total
    return scores
