import argparse
import yaml
import pandas as pd
import os
import torch
import torch.optim as optim
from torch_geometric.loader import DataLoader
import anndata as ad
from vtissue.preprocessing.pipeline import preprocess_dataset, assign_patches
from vtissue.preprocessing.gene_mapping import GlobalGeneMapper
from vtissue.data.dataset import VirtualTissueDataset
from vtissue.model.transformer import VirtualTissueModel
from vtissue.model.masking import MaskingEngine
from vtissue.model.losses import VirtualTissueLoss
from vtissue.training.trainer import Trainer
from vtissue.training.trainer import load_checkpoint
from vtissue.data.spatial_weights import compute_spatial_gene_weights

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run(config_path):
    config = load_config(config_path)
    
    # 1. Load Data
    print(f"Loading data from {config['data']['input_anndata']}...")
    adata = ad.read_h5ad(config['data']['input_anndata'])
    
    # Ensure unique observation names
    if not adata.obs_names.is_unique:
        print("Warning: Observation names are not unique. Making them unique.")
        adata.obs_names_make_unique()
    
    # 1.5 Input is assumed preprocessed (X = global expression, layers['mask'] present)

    # Require mask; X must contain global expression
    if 'mask' not in adata.layers:
        raise ValueError(
            "Missing required layer 'mask' in AnnData. "
            "Please run preprocessing to map panels to the global gene list and build the mask before training."
        )
        
    # 1.8 Patching
    patch_cfg = config.get('patching', {})
    if patch_cfg.get('enabled', False):
        try:
            assign_patches(adata, config)
        except Exception as e:
            print(f"assign_patches failed: {e}")
            if config.get('debug', False):
                raise
    # 1.9 Spatial gene weights (optional)
    loss_cfg = config.get('loss', {})
    spatial_weight_lambda = loss_cfg.get('spatial_weight_lambda', 0.0)
    spatial_weight_method = loss_cfg.get('spatial_weight_method', 'moran')
    spatial_weights = None
    if spatial_weight_lambda and spatial_weight_lambda > 0.0:
        print(f"Computing spatial gene weights using method={spatial_weight_method}...")
        cols_cfg = config['columns']
        spatial_cfg = config['spatial']
        spatial_weights = compute_spatial_gene_weights(
            adata=adata,
            image_id_col=cols_cfg['image_id'],
            x_col=cols_cfg['x_centroid'],
            y_col=cols_cfg['y_centroid'],
            spatial_config=spatial_cfg,
            method=spatial_weight_method,
        )
        print("Spatial gene weights computed.")

    if config['data'].get('save_modified_anndata', True):
        out_dir = config['data']['output_dir']
        os.makedirs(out_dir, exist_ok=True)
        in_name = os.path.basename(config['data']['input_anndata'])
        stem, _ = os.path.splitext(in_name)
        out_path = os.path.join(out_dir, f"{stem}_vtissue.h5ad")
        print(f"Saving modified AnnData to {out_path}...")
        adata.write(out_path)
        print("Saved modified AnnData.")

    # 2. Dataset
    print("Creating Graph Dataset...")
    # Parse MPP map
    mpp_config = config['spatial'].get('mpp_map', {})
    default_mpp = config['spatial'].get('default_mpp', 0.5)
    mpp_map = {'default': default_mpp}
    if mpp_config:
        mpp_map.update(mpp_config)
        
    cache_dir = config['data'].get('cache_dir')
    if not cache_dir:
        cache_dir = os.path.join(config['data']['output_dir'], 'graph_cache')
        print(f"[RunTraining] 'cache_dir' not set. Defaulting to: {cache_dir}")
        print(f"[RunTraining] Tip: Set 'cache_dir' explicitly in config to reuse graphs across experiments.")
    print(f"[RunTraining] Using cache_dir: {cache_dir}")

    dataset = VirtualTissueDataset(
        adata=adata,
        mpp=mpp_map,
        n_fourier_freqs=config['spatial'].get('n_fourier_freqs', 10),
        k_neighbors=config['spatial'].get('k_neighbors', 10),
        radius=config['spatial'].get('radius', None),
        algorithm=config['spatial'].get('algorithm', 'auto'),
        n_jobs=config['spatial'].get('n_jobs', -1),
        columns=config.get('columns', {}),
        cache_dir=cache_dir,
        memory=config.get('memory', {'policy': 'auto', 'feature_dtype': 'float32'}),
        group_by=str(config.get('data', {}).get('group_by', '') or '')
    )
    
    # Pre-cache graphs with progress bar
    dataset.prepare_cache()
    
    # Check if we should stop after cache creation
    if bool(config.get('data', {}).get('stop_after_cache', False)):
        print("Graph cache created successfully. Stopping as requested by 'stop_after_cache'.")
        return

    # Split
    train_idx, val_idx, test_idx = dataset.create_splits(
        val_ratio=config['training']['val_split'],
        test_ratio=config['training']['test_split'],
        seed=config['training']['seed'],
        split_by_image=bool(config['training'].get('split_by_image', False)),
        stratify_by=config['training'].get('stratify_by', None)
    )
    from torch.utils.data import Subset
    train_subset = Subset(dataset, train_idx)
    val_subset = Subset(dataset, val_idx)
    test_subset = Subset(dataset, test_idx)
    print(f"Data split: {len(train_subset)} train, {len(val_subset)} val, {len(test_subset)} test graphs.")
    train_loader = DataLoader(train_subset, batch_size=config['training']['batch_size'], shuffle=True)
    val_loader = DataLoader(val_subset, batch_size=config['training']['batch_size'], shuffle=False)
    
    # 3. Model
    print("Initializing Model...")
    n_genes = dataset.num_features
    
    n_phenotypes = 0
    if 'phenotype' in config['columns'] and config['columns']['phenotype'] in adata.obs:
        n_phenotypes = len(adata.obs[config['columns']['phenotype']].unique())
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Leakage classifier class counts
    cols_cfg = config['columns']
    img_col = cols_cfg.get('image_id', 'imageid')
    n_image_classes = int(len(adata.obs[img_col].astype(str).unique()))
    n_patch_classes = 0
    if 'patch_id' in adata.obs.columns:
        n_patch_classes = int(len(adata.obs['patch_id'].astype(str).unique()))

    leak_root = config.get('training', {}).get('leakage', {})
    leak_cls_cfg = leak_root.get('leakage_classifier', {'enabled': False, 'target': 'patch', 'lambda': 0.0})
    leak_enabled = bool(leak_cls_cfg.get('enabled', False))
    leak_target = str(leak_cls_cfg.get('target', 'patch'))

    model = VirtualTissueModel(
        n_genes=n_genes,
        d_model=config['model']['d_model'],
        n_heads=config['model']['n_heads'],
        n_layers=config['model']['n_layers'],
        n_spatial_features=dataset.num_spatial_features,
        n_phenotypes=n_phenotypes,
        dropout=config['model']['dropout'],
        n_global_tokens=config['model'].get('n_global_tokens', 8),
        n_global_tokens_global=config['model'].get('n_global_tokens_global', None),
        n_global_tokens_local=config['model'].get('n_global_tokens_local', None),
        center_on_graph=bool(config.get('training', {}).get('center_on_graph', False)),
        n_patch_classes=n_patch_classes if leak_enabled and leak_target == 'patch' else 0,
        n_image_classes=n_image_classes if leak_enabled and leak_target == 'image' else 0
    ).to(device)

    # Print model parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model initialized with {total_params:,} total parameters ({trainable_params:,} trainable).")

    try:
        ph_map = getattr(dataset, 'phenotype_map', None)
        if isinstance(ph_map, dict) and len(ph_map) > 0:
            names_by_index = [k for k, v in sorted(ph_map.items(), key=lambda kv: kv[1])]
            if isinstance(getattr(model, 'model_meta', None), dict):
                model.model_meta['phenotype_names'] = names_by_index
    except Exception:
        pass
    try:
        if isinstance(getattr(model, 'model_meta', None), dict):
            spatial_meta = {
                'n_fourier_freqs': int(getattr(dataset, 'n_fourier_freqs', config['spatial'].get('n_fourier_freqs', 10))),
                'k_neighbors': int(getattr(dataset, 'k_neighbors', config['spatial'].get('k_neighbors', 10))),
                'radius': (getattr(dataset, 'radius', config['spatial'].get('radius', None))),
                'algorithm': str(getattr(dataset, 'algorithm', config['spatial'].get('algorithm', 'auto'))),
                'n_jobs': int(getattr(dataset, 'n_jobs', config['spatial'].get('n_jobs', -1))),
                'default_mpp': float(config['spatial'].get('default_mpp', 0.5))
            }
            model.model_meta['spatial_config'] = spatial_meta
    except Exception:
        pass
    
    # 4. Training Components
    optimizer = optim.Adam(model.parameters(), lr=config['training']['learning_rate'])
    
    masking_engine = MaskingEngine(
        mask_ratio_expr=config['masking']['expr_ratio'],
        mask_ratio_edge=config['masking']['edge_ratio'],
        mask_ratio_phenotype=config['masking']['phenotype_ratio'],
        cell_mask_ratio_expr=config['masking'].get('cell_expr_ratio', 0.0)
    )
    
    loss_fn = VirtualTissueLoss(
        lambda_expr_mask=config['loss']['lambda_expr_mask'],
        lambda_reconstruction=config['loss']['lambda_reconstruction'],
        lambda_celltype=config['loss']['lambda_celltype'],
        lambda_cnp=config['loss'].get('lambda_cnp', 0.0),
        cnp_temperature=config['loss'].get('cnp_temperature', 0.1),
        lambda_token_specialization=config['loss'].get('lambda_token_specialization', 0.0),
        lambda_coord=config['loss'].get('lambda_coord', 0.0),
        spatial_weight_lambda=spatial_weight_lambda,
        spatial_weights=spatial_weights,
        cnp_enable_subsample=config['loss'].get('cnp_enable_subsample', True),
        cnp_max_nodes=config['loss'].get('cnp_max_nodes', 8192),
        cnp_subsample_ratio=config['loss'].get('cnp_subsample_ratio', 1.0)
    ).to(device)
    
    # Build maps for leakage classifier labels
    leak_cfg = leak_cls_cfg
    patch_map = {}
    image_map = {}
    try:
        if 'patch_id' in adata.obs.columns:
            uniques = sorted(adata.obs['patch_id'].astype(str).unique())
            patch_map = {val: i for i, val in enumerate(uniques)}
        uniques_img = sorted(adata.obs[img_col].astype(str).unique())
        image_map = {val: i for i, val in enumerate(uniques_img)}
    except Exception:
        pass
    leak_cfg_full = dict(leak_cfg)
    leak_cfg_full['patch_map'] = patch_map
    leak_cfg_full['image_map'] = image_map

    trainer = Trainer(
        model=model,
        loss_fn=loss_fn,
        masking_engine=masking_engine,
        optimizer=optimizer,
        device=device,
        output_dir=config['data']['output_dir'],
        save_recent_every=config['training'].get('save_recent_every', 5),
        n_anchors=config['training'].get('n_anchors', 4),
        patch_monitor=leak_root.get('patch_monitor', {'enabled': False}),
        patch_adv=leak_root.get('patch_adv', {'enabled': False, 'lambda_invariance': 0.0}),
        leak_classifier=leak_cfg_full,
        save_all_epochs=bool(config['training'].get('save_all_epochs', False))
    )
    
    # 5. Run
    print("Starting training...")
    start_epoch = 0
    resume_path = config['training'].get('resume_from', None)
    if resume_path:
        try:
            print(f"Resuming from checkpoint: {resume_path}")
            saved_epoch = load_checkpoint(resume_path, model, optimizer)
            start_epoch = saved_epoch + 1
            print(f"Loaded checkpoint from epoch {saved_epoch}. Resuming at epoch {start_epoch}.")
        except Exception as e:
            print(f"Failed to resume from {resume_path}: {e}. Starting from scratch.")
            start_epoch = 0

    trainer.fit(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=config['training']['epochs'],
        start_epoch=start_epoch
    )
    print("Training complete.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--epochs", type=int, default=None)
    args = parser.parse_args()
    if args.epochs is None:
        run(args.config)
    else:
        cfg = load_config(args.config)
        cfg['training']['epochs'] = args.epochs
        tmp_path = args.config
        import tempfile, yaml
        with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False) as tf:
            yaml.dump(cfg, tf)
            tmp_path = tf.name
        try:
            run(tmp_path)
        finally:
            import os
            try:
                os.remove(tmp_path)
            except Exception:
                pass

if __name__ == "__main__":
    main()

# Duplicate legacy CLI removed
