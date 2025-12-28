import argparse
import yaml
import os
import torch
from torch_geometric.loader import DataLoader
import anndata as ad
from vtissue.preprocessing.pipeline import assign_patches
from vtissue.data.dataset import VirtualTissueDataset
from vtissue.model.transformer import VirtualTissueModel
try:
    from tqdm.auto import tqdm
except Exception:
    tqdm = None

def _normalize_vec(x, mode: str, counts=None):
    import torch
    if mode == 'none':
        return x
    if mode == 'count':
        if counts is None:
            return x
        c = counts.clone().to(x.dtype)
        c = torch.where(c > 0, c, torch.ones_like(c))
        return x / c
    if mode == 'minmax':
        mn = torch.min(x)
        mx = torch.max(x)
        if float(mx.item() - mn.item()) <= 0:
            return torch.zeros_like(x)
        return (x - mn) / (mx - mn)
    if mode == 'zscore':
        mu = torch.mean(x)
        sd = torch.std(x)
        if float(sd.item()) <= 0:
            return torch.zeros_like(x)
        return (x - mu) / sd
    return x

def _to_percent(x):
    import torch
    s = torch.sum(x)
    if float(s.item()) <= 0:
        return torch.zeros_like(x)
    return (x / s) * 100.0

def _knn_indices(X: torch.Tensor, k: int, metric: str = 'euclidean'):
    import torch
    n = int(X.size(0))
    k = int(max(1, min(k, max(1, n - 1))))
    if metric == 'cosine':
        Xn = torch.nn.functional.normalize(X, dim=1)
        D = 1.0 - (Xn @ Xn.T)
    else:
        D = torch.cdist(X, X)
    D.fill_diagonal_(float('inf'))
    vals, idx = torch.topk(D, k, largest=False, dim=1)
    return idx

def _gene_usage(cfg, adata, model, meta, loader, device):
    import torch
    import numpy as np
    gu_cfg = cfg.get('gene_usage', {})
    if not bool(gu_cfg.get('enabled', False)):
        try:
            print("Gene usage: disabled by config")
        except Exception:
            pass
        return
    try:
        print("Gene usage: starting")
    except Exception:
        pass
    modes = gu_cfg.get('modes', ['grad'])
    target = str(gu_cfg.get('target', 'local'))
    agg_scope = str(gu_cfg.get('aggregate_scope', 'per_image'))
    norm = str(gu_cfg.get('normalization', 'count'))
    combine = str(gu_cfg.get('combine', 'none'))
    k_embed = int(gu_cfg.get('k_embed', 15))
    n_perm = int(gu_cfg.get('n_permutations', 1))
    metric = str(gu_cfg.get('metric', 'euclidean'))
    sample_frac = float(gu_cfg.get('sample_frac', 1.0))
    layer_name = str(gu_cfg.get('layer_name', 'vt_gene_usage'))
    uns_key = str(gu_cfg.get('uns_key', 'vt_gene_usage'))
    img_col = cfg.get('columns', {}).get('image_id', 'imageid')
    allow_mismatch = bool(cfg.get('inference', {}).get('allow_gene_mismatch', False))
    n_genes = int(meta.get('n_genes'))
    gf = gu_cfg.get('gene_filter', {'mode': 'observed_only', 'min_occurrences': 1})
    gf_mode = str(gf.get('mode', 'observed_only'))
    min_occ = int(gf.get('min_occurrences', 1))
    custom_list = gf.get('custom_list', [])
    counts_global = torch.zeros(n_genes, dtype=torch.long, device=device)
    image_ids = []
    try:
        image_ids = list(adata.obs[img_col].astype(str).unique())
    except Exception:
        image_ids = []
    counts_by_image = {str(i): torch.zeros(n_genes, dtype=torch.long, device=device) for i in image_ids}
    for batch in loader:
        batch = batch.to(device)
        try:
            gmax = int(meta.get('n_genes'))
            if hasattr(batch, 'obs_cols') and hasattr(batch, 'obs_rows') and hasattr(batch, 'obs_vals') and gmax > 0:
                valid_glob = (batch.obs_cols >= 0) & (batch.obs_cols < gmax)
                if valid_glob.numel() > 0 and (not bool(valid_glob.all().item())):
                    if not allow_mismatch:
                        raise ValueError("Invalid obs_cols in gene usage")
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
                        cols_seg = batch.obs_cols[s_abs:e_abs]
                        counts_global.index_add_(0, cols_seg, torch.ones_like(cols_seg, dtype=torch.long))
                        gid_list = getattr(batch, img_col, None)
                        gid_i = (gid_list[g] if isinstance(gid_list, (list, tuple)) else gid_list)
                        kid = str(gid_i)
                        if kid not in counts_by_image:
                            counts_by_image[kid] = torch.zeros(n_genes, dtype=torch.long, device=device)
                        counts_by_image[kid].index_add_(0, cols_seg, torch.ones_like(cols_seg, dtype=torch.long))
        except Exception:
            pass
    try:
        total_obs = int(counts_global.sum().item())
        print(f"Gene usage: built counts (total observations={total_obs})")
    except Exception:
        pass
    if gf_mode == 'custom' and isinstance(custom_list, (list, tuple)) and len(custom_list) > 0:
        cand = torch.zeros(n_genes, dtype=torch.bool, device=device)
        try:
            names = list(adata.var.index.astype(str))
            name_to_idx = {n: i for i, n in enumerate(names)}
            for v in custom_list:
                if isinstance(v, str) and v in name_to_idx:
                    cand[name_to_idx[v]] = True
                elif isinstance(v, (int,)) and 0 <= int(v) < n_genes:
                    cand[int(v)] = True
        except Exception:
            pass
    else:
        if agg_scope == 'per_image':
            allc = torch.zeros(n_genes, dtype=torch.long, device=device)
            for k in counts_by_image:
                allc = allc + counts_by_image[k]
            cand = allc >= int(min_occ)
        else:
            cand = counts_global >= int(min_occ)
    cand_idx = torch.where(cand)[0].detach().cpu().tolist()
    try:
        print(f"Gene usage: candidate genes={len(cand_idx)} min_occurrences={min_occ} mode={gf_mode}")
    except Exception:
        pass
    usage_grad_global = None
    usage_grad_by_img = {}
    usage_pert_global = None
    usage_pert_by_img = {}
    if 'grad' in modes:
        try:
            print(f"Gene usage: running mode=grad target={target}")
        except Exception:
            pass
        usage_grad_global = torch.zeros(n_genes, dtype=torch.float32, device=device)
        usage_grad_by_img = {str(i): torch.zeros(n_genes, dtype=torch.float32, device=device) for i in counts_by_image.keys()}
        for batch in loader:
            batch = batch.to(device)
            try:
                if hasattr(batch, 'obs_vals') and hasattr(batch, 'obs_ptr'):
                    batch.obs_vals.requires_grad_(True)
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
                if target == 'global':
                    tgt = out['z_global'].norm(dim=1).sum()
                elif target == 'token':
                    zg = out['z_global_tokens']
                    tgt = zg.norm(dim=2).sum()
                else:
                    tgt = out['z_local'].norm(dim=1).sum()
                g = torch.autograd.grad(tgt, batch.obs_vals, retain_graph=False, allow_unused=True)[0]
                if g is None:
                    continue
                obs_ptr = batch.obs_ptr.view(-1, 2) if hasattr(batch, 'obs_ptr') else None
                B = int(batch.batch.max().item()) + 1
                gid_list = getattr(batch, img_col, None)
                for i in range(B):
                    s = int(obs_ptr[i, 0].item()) if obs_ptr is not None else 0
                    e = int(obs_ptr[i, 1].item()) if obs_ptr is not None else g.size(0)
                    if e > s:
                        cols_seg = batch.obs_cols[s:e]
                        grad_seg = g[s:e].abs()
                        usage_grad_global.index_add_(0, cols_seg, grad_seg)
                        gid_i = (gid_list[i] if isinstance(gid_list, (list, tuple)) else gid_list)
                        kid = str(gid_i)
                        if kid not in usage_grad_by_img:
                            usage_grad_by_img[kid] = torch.zeros(n_genes, dtype=torch.float32, device=device)
                        usage_grad_by_img[kid].index_add_(0, cols_seg, grad_seg)
            except Exception:
                pass
        try:
            v = usage_grad_global.detach().cpu().numpy()
            if v.size > 0:
                top = np.argsort(v)[-5:][::-1]
                bot = np.argsort(v)[:5]
                print(f"Gene usage: grad top={top} vals={v[top]}")
                print(f"Gene usage: grad bottom={bot} vals={v[bot]}")
        except Exception:
            pass
    if 'perturb' in modes:
        try:
            print(f"Gene usage: running mode=perturb target={target} k={k_embed} perms={n_perm} metric={metric}")
        except Exception:
            pass
        usage_pert_global = torch.zeros(n_genes, dtype=torch.float32, device=device)
        usage_pert_by_img = {str(i): torch.zeros(n_genes, dtype=torch.float32, device=device) for i in counts_by_image.keys()}
        for batch in loader:
            batch = batch.to(device)
            with torch.no_grad():
                out_base = model(
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
                if target == 'global':
                    emb_base = out_base['z_global']
                else:
                    emb_base = out_base['z_local']
                B = int(batch.batch.max().item()) + 1
                obs_ptr = batch.obs_ptr.view(-1, 2) if hasattr(batch, 'obs_ptr') else None
                gid_list = getattr(batch, img_col, None)
                for gidx in cand_idx:
                    overlap_sum = 0.0
                    overlap_cnt = 0
                    for r in range(n_perm):
                        vals_saved = None
                        if obs_ptr is not None:
                            for i in range(B):
                                s = int(obs_ptr[i, 0].item())
                                e = int(obs_ptr[i, 1].item())
                                if e <= s:
                                    continue
                                pos = (batch.obs_cols[s:e] == int(gidx)).nonzero(as_tuple=True)[0]
                                if pos.numel() == 0:
                                    continue
                                seg = batch.obs_vals[s:e]
                                vals_saved = seg[pos].clone()
                                order = torch.randperm(pos.numel(), device=device)
                                seg[pos] = seg[pos][order]
                            out_perm = model(
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
                            if target == 'global':
                                emb_perm = out_perm['z_global']
                            else:
                                emb_perm = out_perm['z_local']
                            for i in range(B):
                                idx_nodes = (batch.batch == i).nonzero(as_tuple=True)[0]
                                if idx_nodes.numel() <= 1:
                                    continue
                                Ei = emb_base[idx_nodes]
                                Ej = emb_perm[idx_nodes]
                                if sample_frac < 1.0:
                                    n_i = int(idx_nodes.numel())
                                    m = max(1, int(n_i * sample_frac))
                                    sel = torch.randperm(n_i, device=device)[:m]
                                    Ei = Ei[sel]
                                    Ej = Ej[sel]
                                knn_b = _knn_indices(Ei, k_embed, metric)
                                knn_p = _knn_indices(Ej, k_embed, metric)
                                inter = 0
                                k_eff = int(knn_b.size(1))
                                a = knn_b.detach().cpu().numpy()
                                b = knn_p.detach().cpu().numpy()
                                for t in range(a.shape[0]):
                                    inter += int(np.intersect1d(a[t], b[t]).size)
                                overlap_sum += (inter / float(max(1, a.shape[0] * k_eff)))
                                overlap_cnt += 1
                            if obs_ptr is not None and vals_saved is not None:
                                for i in range(B):
                                    s = int(obs_ptr[i, 0].item())
                                    e = int(obs_ptr[i, 1].item())
                                    pos = (batch.obs_cols[s:e] == int(gidx)).nonzero(as_tuple=True)[0]
                                    if pos.numel() > 0:
                                        seg = batch.obs_vals[s:e]
                                        seg[pos] = vals_saved[:pos.numel()]
                    if overlap_cnt > 0:
                        fail = 1.0 - (overlap_sum / float(overlap_cnt))
                        usage_pert_global[int(gidx)] += float(fail)
                        for i in range(B):
                            gid_i = (gid_list[i] if isinstance(gid_list, (list, tuple)) else gid_list)
                            kid = str(gid_i)
                            if kid not in usage_pert_by_img:
                                usage_pert_by_img[kid] = torch.zeros(n_genes, dtype=torch.float32, device=device)
                            usage_pert_by_img[kid][int(gidx)] += float(fail)
        try:
            v = usage_pert_global.detach().cpu().numpy()
            if v.size > 0:
                top = np.argsort(v)[-5:][::-1]
                bot = np.argsort(v)[:5]
                print(f"Gene usage: perturb top={top} vals={v[top]}")
                print(f"Gene usage: perturb bottom={bot} vals={v[bot]}")
        except Exception:
            pass
    out_vectors = {}
    counts_use = counts_global
    if agg_scope == 'per_image':
        counts_use = None
    if usage_grad_global is not None:
        vg = _normalize_vec(usage_grad_global, norm, counts_global)
        out_vectors['grad'] = vg
    if usage_pert_global is not None:
        vp = _normalize_vec(usage_pert_global, norm, counts_global)
        out_vectors['perturb'] = vp
    combined = None
    if len(out_vectors) == 1:
        combined = list(out_vectors.values())[0]
    elif len(out_vectors) > 1:
        if combine == 'mean':
            s = None
            for v in out_vectors.values():
                s = v if s is None else (s + v)
            combined = s / float(len(out_vectors))
        elif combine == 'median':
            import torch
            M = torch.stack(list(out_vectors.values()), dim=0)
            combined = torch.median(M, dim=0).values
        else:
            combined = None
    try:
        names = list(adata.var.index.astype(str))
    except Exception:
        names = None
    if combined is not None:
        import numpy as np
        adata.var[layer_name] = np.array(combined.detach().cpu().numpy(), dtype=np.float32)
        try:
            print(f"Gene usage: wrote adata.var['{layer_name}']")
        except Exception:
            pass
        if bool(gu_cfg.get('percent_enabled', False)):
            pct = _to_percent(combined)
            pl = str(gu_cfg.get('percent_layer_name', f"{layer_name}_pct"))
            adata.var[pl] = np.array(pct.detach().cpu().numpy(), dtype=np.float32)
            try:
                print(f"Gene usage: wrote adata.var['{pl}'] (percent)")
            except Exception:
                pass
    else:
        if 'grad' in out_vectors:
            import numpy as np
            adata.var[f"{layer_name}_grad"] = np.array(out_vectors['grad'].detach().cpu().numpy(), dtype=np.float32)
            try:
                print(f"Gene usage: wrote adata.var['{layer_name}_grad']")
            except Exception:
                pass
            if bool(gu_cfg.get('percent_enabled', False)):
                pl = str(gu_cfg.get('percent_layer_name', f"{layer_name}_pct"))
                adata.var[f"{pl}_grad"] = np.array(_to_percent(out_vectors['grad']).detach().cpu().numpy(), dtype=np.float32)
                try:
                    print(f"Gene usage: wrote adata.var['{pl}_grad'] (percent)")
                except Exception:
                    pass
        if 'perturb' in out_vectors:
            import numpy as np
            adata.var[f"{layer_name}_perturb"] = np.array(out_vectors['perturb'].detach().cpu().numpy(), dtype=np.float32)
            try:
                print(f"Gene usage: wrote adata.var['{layer_name}_perturb']")
            except Exception:
                pass
            if bool(gu_cfg.get('percent_enabled', False)):
                pl = str(gu_cfg.get('percent_layer_name', f"{layer_name}_pct"))
                adata.var[f"{pl}_perturb"] = np.array(_to_percent(out_vectors['perturb']).detach().cpu().numpy(), dtype=np.float32)
                try:
                    print(f"Gene usage: wrote adata.var['{pl}_perturb'] (percent)")
                except Exception:
                    pass
    if agg_scope == 'per_image':
        import numpy as np
        imgs = list(counts_by_image.keys())
        vectors = []
        for kid in imgs:
            vg = usage_grad_by_img.get(kid, None)
            vp = usage_pert_by_img.get(kid, None)
            if vg is not None and vp is not None and combine in ('mean', 'median'):
                if combine == 'mean':
                    vi = _normalize_vec(vg, norm, counts_by_image[kid]) + _normalize_vec(vp, norm, counts_by_image[kid])
                    vi = vi / 2.0
                else:
                    import torch
                    M = torch.stack([_normalize_vec(vg, norm, counts_by_image[kid]), _normalize_vec(vp, norm, counts_by_image[kid])], dim=0)
                    vi = torch.median(M, dim=0).values
            elif vg is not None and vp is None:
                vi = _normalize_vec(vg, norm, counts_by_image[kid])
            elif vp is not None and vg is None:
                vi = _normalize_vec(vp, norm, counts_by_image[kid])
            else:
                vi = None
            if vi is not None:
                vectors.append(vi.detach().cpu().numpy())
        if len(vectors) > 0:
            adata.uns[f"{uns_key}_image_ids"] = np.array(imgs, dtype=str)
            adata.uns[f"{uns_key}_vectors"] = np.stack(vectors, axis=0)
            try:
                print(f"Gene usage: wrote adata.uns['{uns_key}_vectors'] shape={adata.uns[f'{uns_key}_vectors'].shape}")
            except Exception:
                pass
            if bool(gu_cfg.get('percent_enabled', False)):
                import numpy as np
                pv = []
                for vi in vectors:
                    s = float(np.sum(vi))
                    if s <= 0:
                        pv.append(np.zeros_like(vi, dtype=np.float32))
                    else:
                        pv.append((vi / s) * 100.0)
                pkey = str(gu_cfg.get('percent_uns_key', f"{uns_key}_pct"))
                adata.uns[f"{pkey}_image_ids"] = np.array(imgs, dtype=str)
                adata.uns[f"{pkey}_vectors"] = np.stack(pv, axis=0)
                try:
                    print(f"Gene usage: wrote adata.uns['{pkey}_vectors'] shape={adata.uns[f'{pkey}_vectors'].shape} (percent)")
                except Exception:
                    pass

def _sanitize_obj(o):
    try:
        import numpy as np
    except Exception:
        np = None
    try:
        import torch as _t
    except Exception:
        _t = None
    if isinstance(o, (int, float, str, bool)):
        return o
    if o is None:
        return str('None')
    if np is not None and isinstance(o, (np.integer,)):
        return int(o)
    if np is not None and isinstance(o, (np.floating,)):
        return float(o)
    if np is not None and isinstance(o, (np.ndarray,)):
        try:
            return [_sanitize_obj(x) for x in o.tolist()]
        except Exception:
            return []
    if isinstance(o, (list, tuple)):
        return [_sanitize_obj(x) for x in o]
    if isinstance(o, dict):
        return {str(k): _sanitize_obj(v) for k, v in o.items()}
    if _t is not None and isinstance(o, _t.Tensor):
        try:
            return _sanitize_obj(o.detach().cpu().tolist())
        except Exception:
            return []
    try:
        return str(o)
    except Exception:
        return ''

def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def build_model_from_checkpoint(ckpt_path):
    try:
        ckpt = torch.load(ckpt_path, map_location='cpu', weights_only=False)
    except TypeError:
        ckpt = torch.load(ckpt_path, map_location='cpu')
    except Exception:
        try:
            import torch.serialization as tser
            tser.add_safe_globals([__import__('numpy')._core.multiarray.scalar])
            ckpt = torch.load(ckpt_path, map_location='cpu', weights_only=True)
        except Exception:
            ckpt = torch.load(ckpt_path, map_location='cpu')
    meta = ckpt.get('model_meta', None)
    if meta is None:
        raise ValueError("model_meta not found in checkpoint")
    model = VirtualTissueModel(
        n_genes=meta['n_genes'],
        d_model=meta['d_model'],
        n_heads=meta['n_heads'],
        n_layers=meta['n_layers'],
        n_spatial_features=meta['n_spatial_features'],
        n_phenotypes=meta['n_phenotypes'],
        dropout=meta['dropout'],
        n_global_tokens=meta['n_global_tokens'],
        n_global_tokens_global=meta['n_global_tokens_global'],
        n_global_tokens_local=meta['n_global_tokens_local']
    )
    sd = ckpt.get('model', ckpt.get('model_state_dict'))
    if sd is None:
        raise ValueError("state_dict not found in checkpoint")
    model.load_state_dict(sd, strict=False)
    return model, meta

def run(config_path):
    cfg = load_config(config_path)
    inf_cfg = cfg.get('inference', {})
    inf_enabled = bool(inf_cfg.get('enabled', True))
    pred_cfg = cfg.get('prediction', {})
    pred_enabled = bool(pred_cfg.get('enabled', False))
    expr_cfg = cfg.get('expression', {})
    expr_enabled = bool(expr_cfg.get('enabled', False))

    if not (inf_enabled or pred_enabled or expr_enabled):
        print("No tasks enabled (inference, prediction, expression). Exiting.")
        return

    print(f"Loading AnnData from {cfg['data']['input_anndata']}...")
    adata = ad.read_h5ad(cfg['data']['input_anndata'])
    cols = cfg.get('columns', {})
    
    # Patching
    if cfg.get('patching', {}).get('enabled', False):
        print("Assigning patches...")
        assign_patches(adata, cfg)

    # Check gene mismatch early
    try:
        n_model_genes = int(cfg.get('model', {}).get('n_genes', 0) or 0)
    except Exception:
        n_model_genes = 0

    out_dir = cfg['data']['output_dir']
    os.makedirs(out_dir, exist_ok=True)
    ckpt_path = cfg['model']['checkpoint_path']
    print(f"Loading checkpoint: {ckpt_path}")
    model, meta = build_model_from_checkpoint(ckpt_path)
    device = torch.device(cfg.get('inference', {}).get('device', 'cuda' if torch.cuda.is_available() else 'cpu'))
    model = model.to(device)
    model.eval()
    print(f"Using device: {device}")

    try:
        n_model = int(meta.get('n_genes'))
        allow_mismatch = bool(cfg.get('inference', {}).get('allow_gene_mismatch', False))
        if int(adata.shape[1]) != n_model:
            msg = (
                f"Gene dimension mismatch: input has {int(adata.shape[1])} genes, "
                f"model expects {n_model}. "
                f"If you used skip-mapping in preprocessing, the model must be trained with the same gene panel. "
                f"Set inference.allow_gene_mismatch=true to proceed with clipped indices (not recommended)."
            )
            if not allow_mismatch:
                raise ValueError(msg)
            else:
                print("Warning: " + msg)
    except Exception:
        pass

    mpp = cfg['spatial'].get('mpp_map', {'default': cfg['spatial'].get('default_mpp', meta.get('spatial_config', {}).get('default_mpp', 0.5))})
    cache_dir = (cfg.get('inference') or {}).get('cache_dir')
    if not cache_dir:
        cache_dir = (cfg.get('data') or {}).get('cache_dir')
    if not cache_dir:
        cache_dir = os.path.join(out_dir, 'graph_cache')
    print(f"[RunInference] Using cache_dir: {cache_dir}")
    print("Building dataset...")
    spatial_cfg = cfg.get('spatial', {})
    meta_sp = meta.get('spatial_config', {}) if isinstance(meta, dict) else {}
    n_ff = int(spatial_cfg.get('n_fourier_freqs', meta_sp.get('n_fourier_freqs', max(1, int(meta.get('n_spatial_features', 40)) // 4))))
    k_nn = int(spatial_cfg.get('k_neighbors', meta_sp.get('k_neighbors', 10)))
    rad = spatial_cfg.get('radius', meta_sp.get('radius', None))
    algo = str(spatial_cfg.get('algorithm', meta_sp.get('algorithm', 'auto')))
    nj = int(spatial_cfg.get('n_jobs', meta_sp.get('n_jobs', -1)))
    try:
        print(f"Spatial params: n_fourier_freqs={n_ff} (meta n_spatial_features={int(meta.get('n_spatial_features', -1))}), k_neighbors={k_nn}, radius={rad}, algorithm={algo}, n_jobs={nj}")
    except Exception:
        pass
    
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
    
    # Adjust dataset if mismatch
    try:
        if int(getattr(dataset, 'num_spatial_features')) != int(meta.get('n_spatial_features', getattr(dataset, 'num_spatial_features'))):
            expected = int(meta.get('n_spatial_features', getattr(dataset, 'num_spatial_features')))
            n_ff2 = max(1, expected // 4)
            print(f"Adjusting dataset: expected spatial_features={expected}, rebuilding with n_fourier_freqs={n_ff2}")
            dataset = VirtualTissueDataset(
                adata=adata,
                mpp=mpp,
                n_fourier_freqs=n_ff2,
                k_neighbors=k_nn,
                radius=rad,
                algorithm=algo,
                n_jobs=nj,
                columns=cols,
                cache_dir=cache_dir,
                memory=cfg.get('memory', {'policy': 'auto', 'feature_dtype': 'float32'}),
                group_by=str(cfg.get('data', {}).get('group_by', '') or '')
            )
    except Exception:
        pass
        
    # Pre-cache graphs with progress bar
    dataset.prepare_cache()
    print(f"Dataset graphs: {len(dataset)}")

    # Check if we should stop after cache creation
    if bool(cfg.get('data', {}).get('stop_after_cache', False)):
        print("Graph cache created successfully. Stopping as requested by 'stop_after_cache'.")
        return

    # -------------------------------------------------------------------------
    # 1. Run Embedding Inference (if enabled)
    # -------------------------------------------------------------------------
    if inf_enabled:
        print("Running embedding inference...")
        loader = DataLoader(dataset, batch_size=cfg.get('inference', {}).get('batch_size', 2), shuffle=False)
        targets = cfg.get('inference', {}).get('target_levels', ['patch'])
        print(f"Targets: {targets}")
        include_node = ('node' in targets)
        include_token = ('token' in targets)
        include_patch = ('patch' in targets)
        include_sample = ('sample' in targets)
        token_tokens = []
        token_imageids = []
        token_patchids = []
        patch_embeddings = []
        patch_imageids = []
        patch_patchids = []
        sample_map = {}
        img_col = cols.get('image_id', 'imageid')
        patch_col = 'patch_id' if 'patch_id' in adata.obs.columns else None
        
        iterator = loader
        if tqdm is not None:
            iterator = tqdm(loader, total=len(loader), desc="Batches")
            
        if include_node:
            import numpy as np
            covered = np.zeros(adata.shape[0], dtype=bool)
            write_counts = np.zeros(adata.shape[0], dtype=np.int32)
            
        with torch.no_grad():
            for batch in iterator:
                batch = batch.to(device)
                try:
                    gmax = int(meta.get('n_genes'))
                    allow_mismatch = bool(cfg.get('inference', {}).get('allow_gene_mismatch', False))
                    # Validate sparse coords against model gene dimension; preserve per-graph segmentation
                    if hasattr(batch, 'obs_cols') and hasattr(batch, 'obs_rows') and hasattr(batch, 'obs_vals') and gmax > 0:
                        valid_glob = (batch.obs_cols >= 0) & (batch.obs_cols < gmax)
                        if valid_glob.numel() > 0 and (not bool(valid_glob.all().item())):
                            if not allow_mismatch:
                                raise ValueError(
                                    "Invalid obs_cols detected during inference. Set inference.allow_gene_mismatch=true "
                                    "to filter per-graph and rebuild obs_ptr, or ensure panels match the model."
                                )
                            # Per-graph filtering and obs_ptr rebuild to preserve segmentation
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
                                # Rebuild obs_ptr cumulatively per graph
                                ptr = torch.empty((obs_ptr_view.size(0), 2), dtype=torch.long, device=batch.batch.device)
                                start = 0
                                for i, c in enumerate(counts):
                                    ptr[i, 0] = start
                                    start = start + int(c)
                                    ptr[i, 1] = start
                                batch.obs_ptr = ptr.view(-1)
                    # Reindex obs_rows across collated graphs
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
                if include_node:
                    emb = out['z_local'].detach().cpu()
                    n = int(batch.spatial_enc.size(0))
                    if hasattr(batch, 'row_index'):
                        idx = batch.row_index.detach().cpu().numpy()
                    else:
                        idx = np.arange(n, dtype=np.int64)
                    if idx.size != emb.size(0):
                        try:
                            gid_list = getattr(batch, img_col, None)
                            pid_list = getattr(batch, patch_col, None) if patch_col else None
                            gid_i = (gid_list[0] if isinstance(gid_list, (list, tuple)) else gid_list)
                            pid_i = (pid_list[0] if (patch_col and isinstance(pid_list, (list, tuple))) else (pid_list if patch_col else None))
                            raise ValueError(f"row_index mismatch: idx={idx.size}, emb={emb.size(0)} image={gid_i} patch={pid_i}")
                        except Exception:
                            raise ValueError(f"row_index mismatch: idx={idx.size}, emb={emb.size(0)}")
                    missing_this_batch = idx.shape[0] - np.unique(idx).shape[0]
                    if missing_this_batch > 0:
                        print(f"Duplicate indices in batch: {missing_this_batch}")
                    X = adata.obsm.get('vt_node_emb', None)
                    if X is None:
                        X = np.full((adata.shape[0], emb.size(1)), np.nan, dtype=np.float32)
                    if idx.size > 0:
                        mask = idx < X.shape[0]
                        if not np.all(mask):
                            idx = idx[mask]
                            emb = emb[mask]
                        X[idx, :] = emb.numpy()
                        covered[idx] = True
                        write_counts[idx] += 1
                    adata.obsm['vt_node_emb'] = X
                if include_token:
                    gt = out['z_global_tokens'].detach().cpu()
                    bmax = int(batch.batch.max().item()) + 1
                    gid_list = getattr(batch, img_col, None)
                    pid_list = getattr(batch, patch_col, None) if patch_col else None
                    for i in range(bmax):
                        gid_i = (gid_list[i] if isinstance(gid_list, (list, tuple)) else gid_list)
                        pid_i = (pid_list[i] if (patch_col and isinstance(pid_list, (list, tuple))) else (pid_list if patch_col else None))
                        token_tokens.append(gt[i].numpy())
                        token_imageids.append(str(gid_i))
                        token_patchids.append(str(pid_i) if pid_i is not None else "")
                if include_patch:
                    pg = out['z_global'].detach().cpu().numpy()
                    bmax = int(batch.batch.max().item()) + 1
                    gid_list = getattr(batch, img_col, None)
                    pid_list = getattr(batch, patch_col, None) if patch_col else None
                    for i in range(bmax):
                        gid_i = (gid_list[i] if isinstance(gid_list, (list, tuple)) else gid_list)
                        pid_i = (pid_list[i] if (patch_col and isinstance(pid_list, (list, tuple))) else (pid_list if patch_col else None))
                        patch_embeddings.append(pg[i])
                        patch_imageids.append(str(gid_i))
                        patch_patchids.append(str(pid_i) if pid_i is not None else "")
                if include_sample:
                    pg = out['z_global'].detach().cpu().numpy()
                    bmax = int(batch.batch.max().item()) + 1
                    gid_list = getattr(batch, img_col, None)
                    for i in range(bmax):
                        gid_i = (gid_list[i] if isinstance(gid_list, (list, tuple)) else gid_list)
                        if gid_i not in sample_map:
                            sample_map[gid_i] = []
                        sample_map[gid_i].append(pg[i])
        
        if include_node:
            try:
                import numpy as np
                c_mean = float(covered.mean()) if covered.size > 0 else 0.0
                print(f"Coverage: {c_mean}")
                print(f"Uncovered cells: {int((~covered).sum())}")
                print(f"Write count stats: {int(write_counts.min())} {int(write_counts.max())}")
                print(f"Cells written >1 times: {int((write_counts > 1).sum())}")
                u = np.where(~covered)[0]
                if u.size > 0:
                    c1 = patch_col if patch_col else 'patch_id'
                    c2 = cols.get('x_centroid', 'X_centroid')
                    c3 = cols.get('y_centroid', 'Y_centroid')
                    print(adata.obs.iloc[u[:20]][[c1, c2, c3]])
            except Exception:
                pass
        if include_token:
            import numpy as np
            if len(token_tokens) > 0:
                adata.uns['vt_token_emb_tokens'] = np.stack(token_tokens, axis=0)
                adata.uns['vt_token_emb_imageid'] = np.array(token_imageids, dtype=str)
                adata.uns['vt_token_emb_patch_id'] = np.array(token_patchids, dtype=str)
                print(f"Saved token embeddings: {adata.uns['vt_token_emb_tokens'].shape}")
        if include_patch:
            import numpy as np
            if len(patch_embeddings) > 0:
                adata.uns['vt_patch_emb'] = np.stack(patch_embeddings, axis=0)
                adata.uns['vt_patch_emb_imageid'] = np.array(patch_imageids, dtype=str)
                adata.uns['vt_patch_emb_patch_id'] = np.array(patch_patchids, dtype=str)
                print(f"Saved patch embeddings: {adata.uns['vt_patch_emb'].shape}")
        if include_sample:
            import numpy as np
            keys = list(sample_map.keys())
            embs = []
            for k in keys:
                M = np.stack(sample_map[k], axis=0)
                embs.append(M.mean(axis=0))
            adata.uns['vt_sample_emb'] = np.stack(embs, axis=0)
            adata.uns['vt_sample_emb_imageid'] = np.array(keys, dtype=str)
            print(f"Saved sample embeddings: {adata.uns['vt_sample_emb'].shape}")
        
        manifest = {
            'checkpoint_path': ckpt_path,
            'model_meta': meta,
            'targets': targets
        }
        adata.uns['vt_manifest'] = _sanitize_obj(manifest)
        try:
            _gene_usage(cfg, adata, model, meta, loader, device)
        except Exception as e:
            print(f"Gene usage step failed: {e}")
        
        print("Inference (embedding) complete.")

    # -------------------------------------------------------------------------
    # 2. Run Cell Type Prediction (if enabled)
    # -------------------------------------------------------------------------
    if pred_enabled:
        print("Running cell type prediction section...")
        try:
            from vtissue.inference.run_cell_type_prediction import run as run_pred
            # We pass save_output=False so we can write everything once at the end
            run_pred(config_path, adata=adata, dataset=dataset, save_output=False)
        except Exception as e:
            print(f"Cell type prediction failed: {e}")

    # -------------------------------------------------------------------------
    # 3. Run Expression Prediction (if enabled)
    # -------------------------------------------------------------------------
    if expr_enabled:
        print("Running expression prediction section...")
        try:
            from vtissue.inference.run_expression_prediction import run as run_expr
            # We pass save_output=False so we can write everything once at the end
            run_expr(config_path, adata=adata, dataset=dataset, save_output=False)
        except Exception as e:
            print(f"Expression prediction failed: {e}")

    # -------------------------------------------------------------------------
    # 4. Final Write (Single Write Operation)
    # -------------------------------------------------------------------------
    stem = os.path.splitext(os.path.basename(cfg['data']['input_anndata']))[0]
    
    # Determine output path based on priority of enabled tasks
    # If inference ran, we use embeddings suffix.
    # Else if prediction ran, use predictions suffix.
    # Else use expression suffix.
    if inf_enabled:
        overwrite = bool(inf_cfg.get('overwrite_input', False))
        suffix = "_embeddings.h5ad"
    elif pred_enabled:
        overwrite = bool(pred_cfg.get('overwrite_input', False))
        suffix = "_predictions.h5ad"
    else:
        overwrite = bool(expr_cfg.get('overwrite_input', False))
        suffix = "_expr_pred.h5ad"
    
    if overwrite:
        out_path = cfg['data']['input_anndata']
    else:
        out_path = os.path.join(out_dir, f"{stem}{suffix}")
        
    print(f"Writing combined outputs to {out_path}...")
    try:
        adata.write_h5ad(out_path, compression='gzip')
    except Exception:
        adata.write(out_path)
    print("Pipeline execution complete.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True)
    args = p.parse_args()
    run(args.config)

if __name__ == '__main__':
    main()
