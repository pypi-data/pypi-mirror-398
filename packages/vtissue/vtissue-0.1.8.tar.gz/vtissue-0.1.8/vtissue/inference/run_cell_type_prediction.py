import argparse
import os
import torch
import torch.nn.functional as F
import numpy as np
import pandas as pd
import anndata as ad
from torch_geometric.loader import DataLoader
from vtissue.preprocessing.pipeline import assign_patches
from vtissue.data.dataset import VirtualTissueDataset
from vtissue.inference.run_inference import load_config, build_model_from_checkpoint
try:
    from tqdm.auto import tqdm
except Exception:
    tqdm = None

def run(config_path, adata=None, dataset=None, save_output=True):
    cfg = load_config(config_path)
    pred_cfg = cfg.get('prediction', {})
    if not bool(pred_cfg.get('enabled', True)):
        print("Prediction disabled by config; exiting.")
        return
    if adata is None:
        print(f"Loading AnnData from {cfg['data']['input_anndata']}...")
        adata = ad.read_h5ad(cfg['data']['input_anndata'])
        if cfg.get('patching', {}).get('enabled', False):
            print("Assigning patches...")
            assign_patches(adata, cfg)
    else:
        print("Using provided AnnData object.")

    cols = cfg.get('columns', {})
    out_dir = cfg['data']['output_dir']
    os.makedirs(out_dir, exist_ok=True)
    ckpt_path = cfg['model']['checkpoint_path']
    print(f"Loading checkpoint: {ckpt_path}")
    model, meta = build_model_from_checkpoint(ckpt_path)
    n_ph = int(meta.get('n_phenotypes', 0))
    if n_ph <= 0:
        raise ValueError("Checkpoint does not include a phenotype head")
    device = torch.device(
        cfg.get('prediction', {}).get(
            'device', cfg.get('inference', {}).get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        )
    )
    model = model.to(device)
    model.eval()
    print(f"Using device: {device}")
    mpp = cfg['spatial'].get('mpp_map', {'default': cfg['spatial'].get('default_mpp', meta.get('spatial_config', {}).get('default_mpp', 0.5))})
    cache_dir = (cfg.get('prediction') or {}).get('cache_dir')
    if not cache_dir:
        cache_dir = (cfg.get('inference') or {}).get('cache_dir')
    if not cache_dir:
        cache_dir = (cfg.get('data') or {}).get('cache_dir')
    if not cache_dir:
        cache_dir = os.path.join(out_dir, 'graph_cache')
    print(f"[RunCellTypePrediction] Using cache_dir: {cache_dir}")
    
    if dataset is None:
        print("Building dataset...")
        spatial_cfg = cfg.get('spatial', {})
        meta_sp = meta.get('spatial_config', {}) if isinstance(meta, dict) else {}
        n_ff = int(spatial_cfg.get('n_fourier_freqs', meta_sp.get('n_fourier_freqs', max(1, int(meta.get('n_spatial_features', 40)) // 4))))
        k_nn = int(spatial_cfg.get('k_neighbors', meta_sp.get('k_neighbors', 10)))
        rad = spatial_cfg.get('radius', meta_sp.get('radius', None))
        algo = str(spatial_cfg.get('algorithm', meta_sp.get('algorithm', 'auto')))
        nj = int(spatial_cfg.get('n_jobs', meta_sp.get('n_jobs', -1)))
        dataset = VirtualTissueDataset(
            adata=adata,
            mpp=mpp,
            n_fourier_freqs=n_ff,
            k_neighbors=k_nn,
            radius=rad,
            algorithm=algo,
            n_jobs=nj,
            columns=cols,
            cache_dir=cache_dir,
            memory=cfg.get('memory', {'policy': 'auto', 'feature_dtype': 'float32'}),
            group_by=str(cfg.get('data', {}).get('group_by', '') or '')
        )
        # Pre-cache graphs with progress bar
        dataset.prepare_cache()
    else:
        print("Using provided Dataset object.")
    
    print(f"Dataset graphs: {len(dataset)}")
    batch_size = pred_cfg.get('batch_size', cfg.get('inference', {}).get('batch_size', 2))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    col_name = pred_cfg.get('cell_type_column', 'vt_pred_celltype')
    print("Running cell type prediction...")
    pred_labels = np.empty(adata.shape[0], dtype=object)
    pred_labels[:] = ''
    ph_map = getattr(dataset, 'phenotype_map', {})
    inv_map = {v: k for k, v in ph_map.items()} if isinstance(ph_map, dict) else {}
    meta_names = meta.get('phenotype_names', None)
    if not isinstance(meta_names, (list, tuple)) or len(meta_names) != n_ph:
        raise ValueError("Checkpoint missing phenotype_names in model_meta or length mismatch")
    min_conf = float(pred_cfg.get('min_confidence', 0.0))
    unknown_label = str(pred_cfg.get('unknown_label', 'Unknown'))
    iterator = loader
    if tqdm is not None:
        iterator = tqdm(loader, total=len(loader), desc="Batches")
    with torch.no_grad():
        for batch in iterator:
            batch = batch.to(device)
            out = model(
                x=torch.empty((0, 0), device=device),
                edge_index=batch.edge_index,
                spatial_enc=batch.spatial_enc,
                phenotype=getattr(batch, 'phenotype', None),
                phenotype_mask_indices=None,
                batch=batch.batch,
                obs_mask=getattr(batch, 'obs_mask', None),
                mask_indices=None,
                compute_full_expr=False,
                obs_rows=getattr(batch, 'obs_rows', None),
                obs_cols=getattr(batch, 'obs_cols', None),
                obs_vals=getattr(batch, 'obs_vals', None),
                masked_obs_positions=None,
                x_shape=torch.tensor([int(batch.spatial_enc.size(0)), int(meta['n_genes'])], device=device),
                obs_coords=None
            )
            logits = out['pred_phenotype']
            if logits is None:
                raise ValueError("Model did not produce phenotype predictions")
            probs = F.softmax(logits, dim=1)
            max_probs, pred_idx_t = probs.max(dim=1)
            pred_idx = pred_idx_t.detach().cpu().numpy()
            max_probs_np = max_probs.detach().cpu().numpy()
            if hasattr(batch, 'row_index'):
                idx = batch.row_index.detach().cpu().numpy()
            else:
                idx = np.arange(int(batch.spatial_enc.size(0)))
            n_nodes = int(batch.spatial_enc.size(0))
            if idx.size != n_nodes:
                try:
                    gid_list = getattr(batch, cols.get('image_id', 'imageid'), None)
                    pid_list = getattr(batch, 'patch_id', None) if ('patch_id' in adata.obs.columns) else None
                    gid_i = (gid_list[0] if isinstance(gid_list, (list, tuple)) else gid_list)
                    pid_i = (pid_list[0] if (pid_list is not None and isinstance(pid_list, (list, tuple))) else pid_list)
                    raise ValueError(f"row_index mismatch during cell type prediction: idx={idx.size}, n_nodes={n_nodes} image={gid_i} patch={pid_i}")
                except Exception:
                    raise ValueError(f"row_index mismatch during cell type prediction: idx={idx.size}, n_nodes={n_nodes}")
            dup = idx.shape[0] - np.unique(idx).shape[0]
            if dup > 0:
                print(f"Duplicate indices in batch (prediction): {dup}")
            names = np.array([meta_names[int(i)] for i in pred_idx], dtype=object)
            if min_conf > 0.0:
                low_mask = max_probs_np < min_conf
                if np.any(low_mask):
                    names[low_mask] = unknown_label
            mask = idx < adata.shape[0]
            if np.any(mask):
                pred_labels[idx[mask]] = names[mask]
    adata.obs[col_name] = pd.Categorical(pred_labels)
    if save_output:
        stem = os.path.splitext(os.path.basename(cfg['data']['input_anndata']))[0]
        overwrite_input = bool(pred_cfg.get('overwrite_input', False))
        if overwrite_input:
            out_path = cfg['data']['input_anndata']
        else:
            out_path = os.path.join(out_dir, f"{stem}_predictions.h5ad")
        print(f"Writing outputs to {out_path}...")
        adata.write(out_path)
    print("Cell type prediction complete.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True)
    args = p.parse_args()
    run(args.config)

if __name__ == '__main__':
    main()
