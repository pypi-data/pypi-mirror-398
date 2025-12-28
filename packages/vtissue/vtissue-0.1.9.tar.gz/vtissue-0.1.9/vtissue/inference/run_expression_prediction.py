import argparse
import os
import torch
import numpy as np
import anndata as ad
from torch_geometric.loader import DataLoader
from vtissue.preprocessing.pipeline import assign_patches
from vtissue.data.dataset import VirtualTissueDataset
from vtissue.inference.run_inference import load_config, build_model_from_checkpoint
import scipy.sparse as sp
try:
    from tqdm.auto import tqdm
except Exception:
    tqdm = None

def run(config_path, adata=None, dataset=None, save_output=True):
    cfg = load_config(config_path)
    expr_cfg = cfg.get('expression', {})
    if not bool(expr_cfg.get('enabled', True)):
        print("Expression prediction disabled by config; exiting.")
        return
    markers = expr_cfg.get('markers', [])
    if not isinstance(markers, (list, tuple)) or len(markers) == 0:
        raise ValueError("No markers provided in expression.markers")
    
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
    device = torch.device(
        expr_cfg.get('device', cfg.get('inference', {}).get('device', 'cuda' if torch.cuda.is_available() else 'cpu'))
    )
    model = model.to(device)
    model.eval()
    print(f"Using device: {device}")
    mpp = cfg['spatial'].get('mpp_map', {'default': cfg['spatial'].get('default_mpp', meta.get('spatial_config', {}).get('default_mpp', 0.5))})
    cache_dir = expr_cfg.get('cache_dir')
    if not cache_dir:
        cache_dir = (cfg.get('inference') or {}).get('cache_dir')
    if not cache_dir:
        cache_dir = (cfg.get('data') or {}).get('cache_dir')
    if not cache_dir:
        cache_dir = os.path.join(out_dir, 'graph_cache')
    print(f"[RunExpressionPrediction] Using cache_dir: {cache_dir}")
    
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
    batch_size = expr_cfg.get('batch_size', cfg.get('inference', {}).get('batch_size', 2))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    layer_name = str(expr_cfg.get('layer_name', 'vt_expr_pred'))
    gene_to_idx = {str(g): i for i, g in enumerate(list(adata.var_names))}
    marker_indices = []
    for m in markers:
        if str(m) not in gene_to_idx:
            raise ValueError(f"Marker '{m}' not found in AnnData var_names")
        marker_indices.append(int(gene_to_idx[str(m)]))
    try:
        n_model = int(meta.get('n_genes'))
        allow_mismatch = bool(cfg.get('inference', {}).get('allow_gene_mismatch', False))
        if int(adata.shape[1]) != n_model:
            msg = (
                f"Gene dimension mismatch: input has {int(adata.shape[1])} genes, "
                f"model expects {n_model}. "
                f"Use mapping to align or set inference.allow_gene_mismatch=true to clip indices."
            )
            if not allow_mismatch:
                raise ValueError(msg)
            else:
                print("Warning: " + msg)
        # Clip marker indices to model dimension when mismatch allowed
        marker_indices = [int(i) for i in marker_indices if int(i) < n_model]
        if len(marker_indices) == 0:
            raise ValueError("No marker indices remain within the model gene dimension after clipping.")
    except Exception:
        pass
    print("Running expression prediction...")
    rows_all = []
    cols_all = []
    data_all = []
    iterator = loader
    if tqdm is not None:
        iterator = tqdm(loader, total=len(loader), desc="Batches")
    with torch.no_grad():
        for batch in iterator:
            batch = batch.to(device)
            try:
                # Validate and preserve per-graph sparse segmentation; fail early if invalid without mismatch allowance
                if hasattr(batch, 'obs_cols') and hasattr(batch, 'obs_rows') and hasattr(batch, 'obs_vals'):
                    n_model = int(meta.get('n_genes'))
                    allow_mismatch = bool(cfg.get('inference', {}).get('allow_gene_mismatch', False))
                    valid_glob = (batch.obs_cols >= 0) & (batch.obs_cols < n_model)
                    if valid_glob.numel() > 0 and (not bool(valid_glob.all().item())):
                        if not allow_mismatch:
                            raise ValueError(
                                "Invalid obs_cols detected during expression prediction. Set inference.allow_gene_mismatch=true "
                                "to filter per-graph and rebuild obs_ptr, or ensure panels match the model."
                            )
                        if hasattr(batch, 'obs_ptr'):
                            obs_ptr_view = batch.obs_ptr.view(-1, 2)
                            rows_new = []
                            cols_new = []
                            vals_new = []
                            counts = []
                            for i in range(obs_ptr_view.size(0)):
                                s = int(obs_ptr_view[i, 0].item())
                                e = int(obs_ptr_view[i, 1].item())
                                if e > s:
                                    v_i = valid_glob[s:e]
                                    rows_seg = batch.obs_rows[s:e][v_i]
                                    cols_seg = batch.obs_cols[s:e][v_i]
                                    vals_seg = batch.obs_vals[s:e][v_i]
                                    rows_new.append(rows_seg)
                                    cols_new.append(cols_seg)
                                    vals_new.append(vals_seg)
                                    counts.append(int(rows_seg.numel()))
                                else:
                                    counts.append(0)
                            if len(rows_new) > 0:
                                batch.obs_rows = torch.cat(rows_new, dim=0)
                                batch.obs_cols = torch.cat(cols_new, dim=0)
                                batch.obs_vals = torch.cat(vals_new, dim=0)
                            else:
                                batch.obs_rows = torch.empty((0,), dtype=torch.long, device=batch.batch.device)
                                batch.obs_cols = torch.empty((0,), dtype=torch.long, device=batch.batch.device)
                                batch.obs_vals = torch.empty((0,), dtype=batch.obs_vals.dtype, device=batch.batch.device)
                            ptr = torch.empty((obs_ptr_view.size(0), 2), dtype=torch.long, device=batch.batch.device)
                            start = 0
                            for i, c in enumerate(counts):
                                ptr[i, 0] = start
                                start = start + int(c)
                                ptr[i, 1] = start
                            batch.obs_ptr = ptr.view(-1)
            except Exception:
                pass
            try:
                # Reindex obs_rows across collated graphs like training
                if hasattr(batch, 'obs_ptr') and hasattr(batch, 'batch') and hasattr(batch, 'obs_rows'):
                    B = int(batch.batch.max().item()) + 1
                    node_counts = torch.bincount(batch.batch, minlength=B)
                    node_offsets = torch.empty(B, dtype=torch.long, device=batch.batch.device)
                    node_offsets[0] = 0
                    if B > 1:
                        node_offsets[1:] = node_counts.cumsum(0)[:-1]
                    obs_ptr = batch.obs_ptr.view(-1, 2)
                    row_counts = (obs_ptr[:, 1] - obs_ptr[:, 0]).to(torch.long)
                    row_offsets_abs = torch.empty(B, dtype=torch.long, device=batch.batch.device)
                    row_offsets_abs[0] = 0
                    if B > 1:
                        row_offsets_abs[1:] = row_counts.cumsum(0)[:-1]
                    for g in range(B):
                        s_abs = int(row_offsets_abs[g].item())
                        e_abs = int(s_abs + row_counts[g].item())
                        if e_abs > s_abs:
                            batch.obs_rows[s_abs:e_abs] = batch.obs_rows[s_abs:e_abs] + node_offsets[g]
            except Exception:
                pass
            n_nodes = int(batch.spatial_enc.size(0))
            rows_per_gene = torch.arange(n_nodes, device=device, dtype=torch.long)
            rows_cat = []
            cols_cat = []
            masked_pos_list = []
            for gidx in marker_indices:
                rows_cat.append(rows_per_gene)
                cols_cat.append(torch.full((n_nodes,), int(gidx), device=device, dtype=torch.long))
                if hasattr(batch, 'obs_cols'):
                    pos = torch.where(batch.obs_cols == int(gidx))[0]
                    if pos.numel() > 0:
                        masked_pos_list.append(pos)
            if len(rows_cat) == 0:
                continue
            rows_cat = torch.cat(rows_cat, dim=0)
            cols_cat = torch.cat(cols_cat, dim=0)
            mask_indices = torch.stack([rows_cat, cols_cat], dim=1)
            if len(masked_pos_list) > 0:
                masked_obs_positions = torch.cat(masked_pos_list, dim=0)
            else:
                masked_obs_positions = None
            out = model(
                x=torch.empty((0, 0), device=device),
                edge_index=batch.edge_index,
                spatial_enc=batch.spatial_enc,
                phenotype=getattr(batch, 'phenotype', None),
                phenotype_mask_indices=None,
                batch=batch.batch,
                obs_mask=getattr(batch, 'obs_mask', None),
                mask_indices=mask_indices,
                compute_full_expr=False,
                obs_rows=getattr(batch, 'obs_rows', None),
                obs_cols=getattr(batch, 'obs_cols', None),
                obs_vals=getattr(batch, 'obs_vals', None),
                masked_obs_positions=masked_obs_positions,
                x_shape=torch.tensor([int(batch.spatial_enc.size(0)), int(meta['n_genes'])], device=device),
                obs_coords=None
            )
            pred_vals = out.get('pred_expr_masked_coords', None)
            if pred_vals is None:
                raise ValueError("Model did not produce expression predictions at indices")
            pred_np = pred_vals.detach().cpu().numpy()
            if hasattr(batch, 'row_index'):
                idx = batch.row_index.detach().cpu().numpy()
            else:
                idx = np.arange(n_nodes, dtype=np.int64)
            if idx.size != n_nodes:
                try:
                    gid_list = getattr(batch, cols.get('image_id', 'imageid'), None)
                    pid_list = getattr(batch, 'patch_id', None) if ('patch_id' in adata.obs.columns) else None
                    gid_i = (gid_list[0] if isinstance(gid_list, (list, tuple)) else gid_list)
                    pid_i = (pid_list[0] if (pid_list is not None and isinstance(pid_list, (list, tuple))) else pid_list)
                    raise ValueError(f"row_index mismatch during expression prediction: idx={idx.size}, n_nodes={n_nodes} image={gid_i} patch={pid_i}")
                except Exception:
                    raise ValueError(f"row_index mismatch during expression prediction: idx={idx.size}, n_nodes={n_nodes}")
            missing_this_batch = idx.shape[0] - np.unique(idx).shape[0]
            if missing_this_batch > 0:
                print(f"Duplicate indices in batch (expression): {missing_this_batch}")
            offset = 0
            for gi, gidx in enumerate(marker_indices):
                seg = pred_np[offset:offset+n_nodes]
                offset += n_nodes
                valid = idx < adata.shape[0]
                if np.any(valid):
                    r = idx[valid]
                    c = np.full(r.shape, int(gidx), dtype=np.int64)
                    d = seg[valid].astype(np.float32)
                    rows_all.append(r)
                    cols_all.append(c)
                    data_all.append(d)
    if len(rows_all) > 0:
        rows = np.concatenate(rows_all)
        cols = np.concatenate(cols_all)
        data = np.concatenate(data_all)
        coo_vals = sp.coo_matrix((data, (rows, cols)), shape=(adata.shape[0], adata.shape[1]), dtype=np.float32)
        csr_vals = coo_vals.tocsr()
        # Average duplicates instead of summing
        ones = np.ones_like(data, dtype=np.float32)
        coo_cnt = sp.coo_matrix((ones, (rows, cols)), shape=(adata.shape[0], adata.shape[1]), dtype=np.float32)
        csr_cnt = coo_cnt.tocsr()
        try:
            csr_vals.data = csr_vals.data / np.maximum(csr_cnt.data, 1.0)
            dup_pairs = int((csr_cnt.data > 1).sum())
            if dup_pairs > 0:
                print(f"Averaged duplicate (row,col) predictions: {dup_pairs}")
        except Exception:
            pass
        adata.layers[layer_name] = csr_vals
    else:
        adata.layers[layer_name] = sp.csr_matrix((adata.shape[0], adata.shape[1]), dtype=np.float32)
    if save_output:
        stem = os.path.splitext(os.path.basename(cfg['data']['input_anndata']))[0]
        overwrite_input = bool(expr_cfg.get('overwrite_input', False))
        if overwrite_input:
            out_path = cfg['data']['input_anndata']
        else:
            out_path = os.path.join(out_dir, f"{stem}_expr_pred.h5ad")
        print(f"Writing outputs to {out_path}...")
        try:
            adata.write_h5ad(out_path, compression='gzip')
        except Exception:
            adata.write(out_path)
    print("Expression prediction complete.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True)
    args = p.parse_args()
    run(args.config)

if __name__ == '__main__':
    main()
