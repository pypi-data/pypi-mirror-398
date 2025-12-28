import argparse
import math
import numpy as np
from umap import UMAP

def run_umap_large(
    X,
    n_components=2,
    n_neighbors=15,
    min_dist=0.1,
    metric="euclidean",
    train_frac=0.2,
    max_train_cells=None,
    batch_size=100_000,
    random_state=42,
):
    """
    X: np.ndarray, shape (n_cells, n_features)
    Returns: np.ndarray, shape (n_cells, n_components)
    """
    n_cells = X.shape[0]
    rng = np.random.default_rng(random_state)

    # choose training indices
    if max_train_cells is not None:
        n_train = min(max_train_cells, n_cells)
    else:
        n_train = int(n_cells * train_frac)
    n_train = max(n_train, 2 * n_neighbors)  # keep it sane

    train_idx = rng.choice(n_cells, size=n_train, replace=False)
    X_train = X[train_idx]

    # fit UMAP on subset
    umap_model = UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric=metric,
        random_state=random_state,
        verbose=True,
    )
    umap_model.fit(X_train)

    # transform all cells in batches
    embedding = np.zeros((n_cells, n_components), dtype=np.float32)
    n_batches = math.ceil(n_cells / batch_size)

    for b in range(n_batches):
        start = b * batch_size
        end = min((b + 1) * batch_size, n_cells)
        X_batch = X[start:end]
        embedding[start:end] = umap_model.transform(X_batch)
        print(f"Processed batch {b+1}/{n_batches} ({end-start} cells)")
    return embedding, umap_model, train_idx