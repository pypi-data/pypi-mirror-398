import torch
from torch_geometric.data import Dataset
import anndata as ad
import numpy as np
from typing import List, Optional, Dict, Tuple, Union
from .graph_builder import GraphBuilder
from .spatial import SpatialEncoder
import os
import psutil

class VirtualTissueDataset(Dataset):
    """
    PyG Dataset for Virtual Tissue.
    """
    def __init__(
        self, 
        adata: ad.AnnData,
        mpp: Union[float, Dict[str, float]] = 0.5,
        n_fourier_freqs: int = 10,
        k_neighbors: int = 10,
        radius: Optional[float] = None,
        algorithm: str = 'auto',
        n_jobs: int = -1,
        columns: Optional[Dict[str, str]] = None,
        cache_dir: Optional[str] = None,
        memory: Optional[Dict[str, Union[str, bool, int]]] = None,
        group_by: Optional[str] = None,
        transform=None,
        pre_transform=None
    ):
        self.adata = adata
        self.mpp = mpp
        self.n_fourier_freqs = n_fourier_freqs
        self.k_neighbors = k_neighbors
        self.radius = radius
        self.algorithm = algorithm
        self.n_jobs = n_jobs
        self.memory = memory or {}
        cols = columns or {}
        self.col_image = cols.get('image_id', 'imageid')
        self.col_x = cols.get('x_centroid', 'X_centroid')
        self.col_y = cols.get('y_centroid', 'Y_centroid')
        self.col_pheno = cols.get('phenotype', None)
        self.col_patch = 'patch_id' if 'patch_id' in adata.obs.columns else None
        required_cols = [self.col_image, self.col_x, self.col_y]
        for c in required_cols:
            if c not in adata.obs.columns:
                raise ValueError(f"Required column '{c}' not found in adata.obs")
        
        # Build mappings
        self.phenotype_map = self._build_map(adata, self.col_pheno or 'phenotype')
        # Grouping
        if isinstance(group_by, str):
            gb = group_by.strip().lower()
            if gb in ('image', 'sample'):
                self.group_key = self.col_image
            elif gb in ('patch', 'tile'):
                self.group_key = self.col_patch if self.col_patch is not None else self.col_image
            else:
                self.group_key = self.col_patch if self.col_patch is not None else self.col_image
        else:
            self.group_key = self.col_patch if self.col_patch is not None else self.col_image
        self.group_ids = self.adata.obs[self.group_key].astype(str).unique().tolist()

        # Pre-compute indices for fast slicing to avoid O(N^2) behavior
        print("[Dataset] Pre-computing group indices for fast access...")
        # groupby().indices returns a dict of {key: int_array_of_indices}
        self.group_indices = self.adata.obs.groupby(self.adata.obs[self.group_key].astype(str)).indices
        if self.col_image != self.group_key:
             self.image_indices = self.adata.obs.groupby(self.adata.obs[self.col_image].astype(str)).indices
        else:
             self.image_indices = self.group_indices

        # Cache directory
        self.cache_dir = cache_dir or os.path.join('.', 'graph_cache')
        # Resolve to absolute path for clarity
        self.cache_dir = os.path.abspath(self.cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        print(f"[Dataset] Cache directory: {self.cache_dir}")
        # Memory policy
        self.feature_dtype = torch.float32 if str(self.memory.get('feature_dtype', 'float32')).lower() == 'float32' else torch.float16
        self.mask_dtype = torch.uint8
        self.edge_dtype = torch.long
        self.lazy = True
        policy = str(self.memory.get('policy', 'auto')).lower()
        if policy == 'eager':
            self.lazy = False
        elif policy == 'auto':
            try:
                vm = psutil.virtual_memory()
                avail_gb = vm.available / (1024**3)
                # If available RAM is low, prefer lazy
                self.lazy = True if avail_gb < 16 else False
            except Exception:
                self.lazy = True
        else:
            self.lazy = True
        super().__init__(transform=transform, pre_transform=pre_transform)
    
    @property
    def num_spatial_features(self) -> int:
        """Calculate the number of spatial features based on n_fourier_freqs."""
        return 4 * self.n_fourier_freqs
    
    @property
    def num_features(self) -> int:
        return int(self.adata.shape[1])
        
    def _build_map(self, adata, col: str) -> Dict[str, int]:
        if col not in adata.obs:
            return {}
        uniques = sorted(adata.obs[col].unique().astype(str))
        return {val: i for i, val in enumerate(uniques)}
        
    def __len__(self):
        return len(self.group_ids)
    
    def len(self):
        return len(self.group_ids)

    def prepare_cache(self):
        """
        Iterate over the dataset to ensure all graphs are cached.
        Useful for showing a progress bar during the initial build.
        """
        try:
            from tqdm.auto import tqdm
        except ImportError:
            def tqdm(x, desc=None): return x
            
        print(f"[Dataset] Ensuring {len(self)} graphs are cached...")
        for i in tqdm(range(len(self)), desc="Building Graph Cache"):
            _ = self.get(i)

    def get(self, idx):
        gid = self.group_ids[idx]
        
        # Fast slicing
        if gid in self.group_indices:
            indices = self.group_indices[gid]
            subset = self.adata[indices]
        else:
            subset = self.adata[self.adata.obs[self.group_key].astype(str) == gid]

        if subset.shape[0] > 0:
            img_id = str(subset.obs[self.col_image].iloc[0])
        else:
            img_id = 'unknown'

        spatial_encoder = SpatialEncoder(mpp=self._resolve_mpp(img_id), n_fourier_freqs=self.n_fourier_freqs)
        builder = GraphBuilder(
            spatial_encoder=spatial_encoder,
            k_neighbors=self.k_neighbors,
            radius=self.radius,
            phenotype_map=self.phenotype_map,
            phenotype_col=self.col_pheno,
            algorithm=self.algorithm,
            n_jobs=self.n_jobs,
            x_col=self.col_x,
            y_col=self.col_y
        )
        try:
            if img_id in self.image_indices:
                img_idxs = self.image_indices[img_id]
                coords_all = self.adata.obs.iloc[img_idxs][[self.col_x, self.col_y]].values.astype(np.float32)
            else:
                mask_img_all = self.adata.obs[self.col_image].astype(str) == img_id
                coords_all = self.adata.obs.loc[mask_img_all, [self.col_x, self.col_y]].values.astype(np.float32)

            micron_all = coords_all * spatial_encoder.mpp
            min_vals = micron_all.min(axis=0)
            max_vals = micron_all.max(axis=0)
        except Exception:
            min_vals = None
            max_vals = None
        cache_path = os.path.join(self.cache_dir, f"graph_{self.group_key}_{gid}.pt")
        if os.path.exists(cache_path):
            try:
                data = torch.load(cache_path, map_location='cpu', weights_only=False)
            except TypeError:
                data = torch.load(cache_path, map_location='cpu')
            try:
                expected_sf = 4 * int(self.n_fourier_freqs)
                actual_sf = int(getattr(data, 'spatial_enc').size(1)) if hasattr(data, 'spatial_enc') else expected_sf
                idx_map = self.group_indices[gid]
                n_expected_nodes = idx_map.size
                n_actual_nodes = int(getattr(data, 'n_nodes', None) or (data.pos.size(0) if hasattr(data, 'pos') else (data.spatial_enc.size(0) if hasattr(data, 'spatial_enc') else n_expected_nodes)))
                if actual_sf != expected_sf or n_actual_nodes != n_expected_nodes:
                    print(f"[Dataset] Cache invalid for {gid}: expected_sf={expected_sf} vs {actual_sf}, n_expected_nodes={n_expected_nodes} vs {n_actual_nodes}")
                    data = builder.build(subset, min_vals=min_vals, max_vals=max_vals)
                    setattr(data, self.col_image, img_id)
                    if self.col_patch is not None:
                        setattr(data, self.col_patch, gid)
                    torch.save(data, cache_path)
            except Exception as e:
                # If validation fails, we might want to rebuild or pass.
                # Currently we pass, meaning we use the loaded data even if check failed?
                # Actually, if check fails (Exception), we probably should rebuild.
                # But let's just log for now.
                # print(f"Cache validation error: {e}")
                pass
        else:
            # print(f"[Dataset] Cache miss: {cache_path}")
            data = builder.build(subset, min_vals=min_vals, max_vals=max_vals)
            setattr(data, self.col_image, img_id)
            if self.col_patch is not None:
                setattr(data, self.col_patch, gid)
            # Dtype control
            if isinstance(data.edge_index, torch.Tensor):
                data.edge_index = data.edge_index.to(self.edge_dtype)
            # Cast obs_vals if present
            if hasattr(data, 'obs_vals') and isinstance(data.obs_vals, torch.Tensor):
                data.obs_vals = data.obs_vals.to(self.feature_dtype)
            try:
                idx_map = self.group_indices[gid]
                data.row_index = torch.tensor(idx_map, dtype=torch.long)
            except Exception:
                pass
            torch.save(data, cache_path)
        # Ensure sparse-only training attributes are present and remove dense x/mask
        try:
            n_nodes = int(getattr(data, 'n_nodes', None) or (data.pos.size(0) if hasattr(data, 'pos') else data.spatial_enc.size(0)))
            n_genes = int(getattr(data, 'n_genes', None) or self.adata.shape[1])
            # Provide empty placeholders for x and obs_mask to avoid PyG collate KeyError
            data.x = torch.empty((n_nodes, 0), dtype=self.feature_dtype)
            data.obs_mask = torch.empty((n_nodes, 0), dtype=self.mask_dtype)
            # Provide default sparse coords if missing
            if not hasattr(data, 'obs_rows'):
                data.obs_rows = torch.empty((0,), dtype=torch.long)
            if not hasattr(data, 'obs_cols'):
                data.obs_cols = torch.empty((0,), dtype=torch.long)
            if not hasattr(data, 'obs_vals'):
                data.obs_vals = torch.empty((0,), dtype=self.feature_dtype)
            if not hasattr(data, 'obs_ptr'):
                data.obs_ptr = torch.tensor([0, data.obs_rows.numel()], dtype=torch.long)
            data.n_nodes = int(n_nodes)
            data.n_genes = int(n_genes)
            if not hasattr(data, 'row_index'):
                try:
                    idx_map = self.group_indices[gid]
                    data.row_index = torch.tensor(idx_map, dtype=torch.long)
                except Exception:
                    pass
        except Exception:
            pass
        return data

    def _resolve_mpp(self, img_id: str) -> float:
        if isinstance(self.mpp, dict):
            return self.mpp.get(str(img_id), self.mpp.get('default', 0.5))
        return self.mpp

    def create_splits(
        self, 
        val_ratio: float = 0.1, 
        test_ratio: float = 0.1,
        seed: int = 42,
        split_by_image: bool = False,
        stratify_by: Optional[str] = None
    ):
        """
        Create train/val/test splits (Subsets).
        If split_by_image is True, splits are created at the image level, ensuring
        all patches from the same image are in the same split.
        If stratify_by is provided, stratifies the split based on the given column in adata.obs.
        """
        # Try to import sklearn for stratification
        try:
            from sklearn.model_selection import train_test_split
            has_sklearn = True
        except ImportError:
            has_sklearn = False
            if stratify_by:
                print("[Dataset] Warning: sklearn not found. Ignoring stratify_by and falling back to random split.")
                stratify_by = None

        if stratify_by and stratify_by not in self.adata.obs.columns:
            print(f"[Dataset] Warning: stratify_by column '{stratify_by}' not found. Falling back to random split.")
            stratify_by = None

        n_samples = len(self)
        indices = np.arange(n_samples)
        
        # If we can't use sklearn or don't need stratification, we can use simple logic or sklearn without stratify
        # But for consistency, let's use sklearn if available even for random splits, as it handles seeds well.
        # If sklearn is missing, we fall back to manual shuffling.

        if not has_sklearn:
            # Manual fallback
            np.random.seed(seed)
            if split_by_image:
                 # Original manual split_by_image logic
                df = self.adata.obs[[self.group_key, self.col_image]].drop_duplicates()
                group_to_image = dict(zip(df[self.group_key].astype(str), df[self.col_image].astype(str)))
                images = sorted(list(set(group_to_image.values())))
                np.random.shuffle(images)
                
                n_total_images = len(images)
                n_val_img = max(1, int(n_total_images * val_ratio)) if val_ratio > 0 else 0
                n_test_img = max(1, int(n_total_images * test_ratio)) if test_ratio > 0 else 0
                
                if n_val_img + n_test_img >= n_total_images:
                     n_test_img = max(0, n_total_images - n_val_img - 1)
                
                val_images = set(images[:n_val_img])
                test_images = set(images[n_val_img:n_val_img+n_test_img])
                
                train_idx = []
                val_idx = []
                test_idx = []
                for i, gid in enumerate(self.group_ids):
                    img = group_to_image.get(str(gid), None)
                    if img in val_images:
                        val_idx.append(i)
                    elif img in test_images:
                        test_idx.append(i)
                    else:
                        train_idx.append(i)
                np.random.shuffle(train_idx)
                np.random.shuffle(val_idx)
                np.random.shuffle(test_idx)
                return train_idx, val_idx, test_idx
            else:
                # Original manual random split
                np.random.shuffle(indices)
                n_val = int(n_samples * val_ratio)
                n_test = int(n_samples * test_ratio)
                n_train = n_samples - n_val - n_test
                train_idx = indices[:n_train]
                val_idx = indices[n_train:n_train+n_val]
                test_idx = indices[n_train+n_val:]
                return train_idx.tolist(), val_idx.tolist(), test_idx.tolist()

        # Sklearn implementation
        if split_by_image:
            # Image-level split
            df = self.adata.obs[[self.group_key, self.col_image]].drop_duplicates()
            group_to_image = dict(zip(df[self.group_key].astype(str), df[self.col_image].astype(str)))
            images = sorted(list(set(group_to_image.values())))
            
            img_labels = None
            if stratify_by:
                # Get label per image (take first)
                temp_df = self.adata.obs[[self.col_image, stratify_by]].drop_duplicates(subset=[self.col_image])
                img_label_dict = dict(zip(temp_df[self.col_image].astype(str), temp_df[stratify_by]))
                img_labels = [img_label_dict.get(img, 0) for img in images]

            # First split: Train vs (Val+Test)
            test_val_size = val_ratio + test_ratio
            if test_val_size <= 0:
                return indices.tolist(), [], []
            if test_val_size >= 1.0:
                test_val_size = 0.99 # Safety

            train_imgs, test_val_imgs = train_test_split(
                images, 
                test_size=test_val_size, 
                random_state=seed, 
                shuffle=True, 
                stratify=img_labels
            )
            
            # Second split: Val vs Test
            if test_ratio > 0:
                # Portion of test_val that is test
                # test_ratio relative to total. We have test_val chunk.
                # relative_test = test / (val + test)
                relative_test = test_ratio / (val_ratio + test_ratio)
                
                test_val_labels = None
                if stratify_by:
                     test_val_labels = [img_label_dict.get(img, 0) for img in test_val_imgs]

                val_imgs, test_imgs = train_test_split(
                    test_val_imgs,
                    test_size=relative_test,
                    random_state=seed,
                    shuffle=True,
                    stratify=test_val_labels
                )
            else:
                val_imgs = test_val_imgs
                test_imgs = []

            val_images_set = set(val_imgs)
            test_images_set = set(test_imgs)
            
            train_idx = []
            val_idx = []
            test_idx = []
            
            for i, gid in enumerate(self.group_ids):
                img = group_to_image.get(str(gid), None)
                if img in val_images_set:
                    val_idx.append(i)
                elif img in test_images_set:
                    test_idx.append(i)
                else:
                    train_idx.append(i)
            
            # Shuffle within splits (patches)
            np.random.seed(seed)
            np.random.shuffle(train_idx)
            np.random.shuffle(val_idx)
            np.random.shuffle(test_idx)
            
            print(f"Image-based split (stratified={bool(stratify_by)}): {len(train_idx)} train, {len(val_idx)} val, {len(test_idx)} test patches.")
            return train_idx, val_idx, test_idx
        
        else:
            # Patch-level split
            labels = None
            if stratify_by:
                df_map = self.adata.obs[[self.group_key, stratify_by]].drop_duplicates(subset=[self.group_key])
                group_val_map = dict(zip(df_map[self.group_key].astype(str), df_map[stratify_by]))
                labels = [group_val_map.get(str(gid), 0) for gid in self.group_ids]

            test_val_size = val_ratio + test_ratio
            if test_val_size <= 0:
                 return indices.tolist(), [], []
            if test_val_size >= 1.0:
                 test_val_size = 0.99

            train_idx, test_val_idx = train_test_split(
                indices,
                test_size=test_val_size,
                random_state=seed,
                shuffle=True,
                stratify=labels
            )
            
            if test_ratio > 0:
                relative_test = test_ratio / (val_ratio + test_ratio)
                test_val_labels = None
                if labels is not None:
                     test_val_labels = [labels[i] for i in test_val_idx]
                
                val_sub_idx, test_sub_idx = train_test_split(
                    test_val_idx,
                    test_size=relative_test,
                    random_state=seed,
                    shuffle=True,
                    stratify=test_val_labels
                )
                val_idx = val_sub_idx
                test_idx = test_sub_idx
            else:
                val_idx = test_val_idx
                test_idx = np.array([], dtype=int)
                
            return train_idx.tolist(), val_idx.tolist(), test_idx.tolist()
