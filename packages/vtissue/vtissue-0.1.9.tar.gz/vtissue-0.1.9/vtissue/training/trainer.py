import torch
import torch.nn.functional as F
import torch.optim as optim
from torch_geometric.loader import DataLoader
import os
import time
from typing import Optional, Dict, List
import numpy as np
from ..model.transformer import VirtualTissueModel
from ..model.masking import MaskingEngine
from ..model.losses import VirtualTissueLoss

def save_checkpoint(path: str, model: VirtualTissueModel, optimizer: optim.Optimizer, epoch: int):
    checkpoint = {
        'model': model.state_dict(),
        'optimizer': optimizer.state_dict(),
        'epoch': epoch,
        'model_meta': getattr(model, 'model_meta', None)
    }
    torch.save(checkpoint, path)

def load_checkpoint(path: str, model: VirtualTissueModel, optimizer: optim.Optimizer) -> int:
    try:
        ckpt = torch.load(path, map_location='cpu', weights_only=False)
    except TypeError:
        ckpt = torch.load(path, map_location='cpu')
    except Exception:
        try:
            import torch.serialization as tser
            tser.add_safe_globals([__import__('numpy')._core.multiarray.scalar])
            ckpt = torch.load(path, map_location='cpu', weights_only=True)
        except Exception:
            ckpt = torch.load(path, map_location='cpu')
    if 'model' in ckpt:
        model.load_state_dict(ckpt['model'], strict=False)
    elif 'model_state_dict' in ckpt:
        model.load_state_dict(ckpt['model_state_dict'], strict=False)
    if 'optimizer' in ckpt:
        optimizer.load_state_dict(ckpt['optimizer'])
    elif 'optimizer_state_dict' in ckpt:
        optimizer.load_state_dict(ckpt['optimizer_state_dict'])
    if 'model_meta' in ckpt and getattr(model, 'model_meta', None) is None:
        try:
            model.model_meta = ckpt['model_meta']
        except Exception:
            pass
    return int(ckpt.get('epoch', 0))

class Trainer:
    """
    Handles training and validation of Virtual Tissue model.
    """
    class _GradReverse(torch.autograd.Function):
        @staticmethod
        def forward(ctx, x, alpha: float):
            ctx.alpha = float(alpha)
            return x.view_as(x)
        @staticmethod
        def backward(ctx, grad_output):
            return -ctx.alpha * grad_output, None

    def __init__(
        self,
        model: VirtualTissueModel,
        loss_fn: VirtualTissueLoss,
        masking_engine: MaskingEngine,
        optimizer: optim.Optimizer,
        device: torch.device,
        output_dir: str,
        save_recent_every: int = 5,
        n_anchors: int = 4,
        patch_monitor: Optional[Dict] = None,
        patch_adv: Optional[Dict] = None,
        leak_classifier: Optional[Dict] = None,
        save_all_epochs: bool = False
    ):
        self.model = model
        self.loss_fn = loss_fn
        self.masking_engine = masking_engine
        self.optimizer = optimizer
        self.device = device
        self.output_dir = output_dir
        self.best_val_loss = float('inf')
        self.save_recent_every = save_recent_every
        self.save_all_epochs = bool(save_all_epochs)
        self.n_anchors = n_anchors
        try:
            self.scaler = torch.amp.GradScaler('cuda')
        except Exception:
            self.scaler = torch.cuda.amp.GradScaler()
        
        os.makedirs(output_dir, exist_ok=True)
        if self.save_all_epochs:
            try:
                os.makedirs(os.path.join(output_dir, "model"), exist_ok=True)
            except Exception:
                pass
        self.patch_monitor = patch_monitor or {'enabled': False}
        self.patch_adv = patch_adv or {'enabled': False, 'lambda_invariance': 0.0}
        self.leak_cls = leak_classifier or {'enabled': False, 'target': 'patch', 'lambda': 0.0}
        
    def train_epoch(self, loader: DataLoader) -> Dict[str, float]:
        self.model.train()
        total_losses = {}
        n_batches = 0
        
        for batch in loader:
            batch = batch.to(self.device)
            with torch.amp.autocast('cuda'):
                # 1. Masking
                if hasattr(batch, 'obs_rows') and hasattr(batch, 'obs_cols') and hasattr(batch, 'n_nodes') and hasattr(batch, 'n_genes'):
                    if hasattr(batch, 'obs_ptr') and hasattr(batch, 'batch'):
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
                    expr_mask_indices, masked_positions = self.masking_engine.mask_expression_sparse(
                        batch.obs_rows, batch.obs_cols, batch.n_nodes, batch.n_genes
                    )
                else:
                    masked_x, expr_mask_indices = self.masking_engine.mask_expression(
                        batch.x, batch.obs_mask
                    )
                    masked_positions = None
                x_in = masked_x if masked_positions is None else torch.empty((0, 0), device=batch.spatial_enc.device)
                try:
                    n = int(getattr(batch, 'n_nodes', batch.x.size(0)))
                    g = int(getattr(batch, 'n_genes', batch.x.size(1)))
                    if hasattr(batch, 'obs_rows'):
                        obs_count = int(batch.obs_rows.numel())
                    else:
                        obs_count = int((batch.obs_mask > 0.5).sum().item())
                    masked_count = expr_mask_indices.shape[0] if expr_mask_indices.ndim == 2 else int(expr_mask_indices.sum().item())
                    if torch.cuda.is_available():
                        alloc = torch.cuda.memory_allocated(self.device)
                        reserv = torch.cuda.memory_reserved(self.device)
                        print(f"Batch x={n}x{g} obs={obs_count} masked={masked_count} cuda_alloc={alloc} cuda_reserved={reserv}")
                    else:
                        print(f"Batch x={n}x{g} obs={obs_count} masked={masked_count}")
                except Exception:
                    pass
                masked_edge_index = batch.edge_index
                phenotype_mask_indices = None
                masked_phenotype = None
                if hasattr(batch, 'phenotype') and batch.phenotype is not None:
                    masked_phenotype, phenotype_mask_indices = self.masking_engine.mask_phenotype(batch.phenotype)
                # 2. Forward
                # Safe shapes for sparse path
                _N_total = int(batch.spatial_enc.size(0))
                if hasattr(batch, 'n_genes'):
                    _ng = getattr(batch, 'n_genes')
                    _G_total = (int(_ng) if not isinstance(_ng, torch.Tensor) else int(_ng[0].item()))
                else:
                    _G_total = int(self.model.decoder.expr_fc2.out_features)
                output = self.model(
                    x=x_in,
                    edge_index=masked_edge_index,
                    spatial_enc=batch.spatial_enc,
                    phenotype=masked_phenotype,
                    phenotype_mask_indices=phenotype_mask_indices,
                    batch=batch.batch,
                    obs_mask=getattr(batch, 'obs_mask', None),
                    mask_indices=expr_mask_indices,
                    compute_full_expr=False,
                    obs_rows=getattr(batch, 'obs_rows', None),
                    obs_cols=getattr(batch, 'obs_cols', None),
                    obs_vals=getattr(batch, 'obs_vals', None),
                    masked_obs_positions=masked_positions,
                    x_shape=torch.tensor([_N_total, _G_total], device=batch.spatial_enc.device),
                    obs_coords=torch.stack([getattr(batch, 'obs_rows', torch.tensor([], dtype=torch.long)), getattr(batch, 'obs_cols', torch.tensor([], dtype=torch.long))], dim=1) if hasattr(batch, 'obs_rows') else None
                )
                # 3. Loss
                
                losses = self.loss_fn(
                    pred_expr=output['pred_expr'],
                    target_expr=(batch.x if hasattr(batch, 'x') else torch.empty((0, _G_total), device=batch.spatial_enc.device)),
                    obs_mask=batch.obs_mask,
                    mask_indices=expr_mask_indices,
                    pred_expr_masked_coords=output.get('pred_expr_masked_coords', None),
                    masked_coords=output.get('masked_coords', None),
                    pred_expr_obs_coords=output.get('pred_expr_obs_coords', None),
                    obs_coords=output.get('obs_coords', None),
                    target_expr_masked_vals=(getattr(batch, 'obs_vals', None)[masked_positions] if masked_positions is not None and hasattr(batch, 'obs_vals') else None),
                    target_expr_obs_vals=getattr(batch, 'obs_vals', None),
                    pred_phenotype=output['pred_phenotype'],
                    target_phenotype=getattr(batch, 'phenotype', None),
                    phenotype_mask_indices=phenotype_mask_indices,
                    z_local=output['z_local'],
                    batch_nodes=batch.batch,
                    token_specialization_reg=output.get('token_specialization_reg', None),
                    edge_index=batch.edge_index,
                    coord_pred=output.get('coord_pred', None),
                    coords=getattr(batch, 'coords', None)
                )
                # Patch invariance regularizer and monitor
                if (self.patch_monitor.get('enabled', False) or self.patch_adv.get('enabled', False)) and 'z_local' in output:
                    z_local = output['z_local']
                    B = int(batch.batch.max().item()) + 1
                    means = []
                    for i in range(B):
                        idx = (batch.batch == i)
                        if idx.any():
                            means.append(z_local[idx].mean(dim=0))
                    if len(means) >= 2:
                        M = torch.stack(means, dim=0)
                        var_means = M.var(dim=0).mean()
                        var_nodes = z_local.var(dim=0).mean()
                        leakage = (var_means / (var_nodes + 1e-8))
                        losses['patch_leakage'] = leakage.detach()
                        lam = float(self.patch_adv.get('lambda_invariance', 0.0)) if self.patch_adv.get('enabled', False) else 0.0
                        if lam > 0.0:
                            D = 0.0
                            cnt = 0
                            for i in range(M.size(0)):
                                for j in range(i+1, M.size(0)):
                                    D = D + torch.norm(M[i] - M[j], p=2)
                                    cnt += 1
                            if cnt > 0:
                                loss_inv = D / cnt
                                losses['loss_patch_invariance'] = loss_inv
                                losses['total_loss'] = losses['total_loss'] + lam * loss_inv
                # Adversarial leakage classifier (patch/image) via gradient reversal
                if self.leak_cls.get('enabled', False) and 'z_local' in output:
                    target = str(self.leak_cls.get('target', 'patch'))
                    alpha = float(self.leak_cls.get('lambda', 0.0))
                    if alpha > 0.0:
                        B = int(batch.batch.max().item()) + 1
                        y = torch.empty(int(batch.spatial_enc.size(0)), dtype=torch.long, device=self.device)
                        if target == 'patch' and getattr(self.model, 'patch_head', None) is not None:
                            pid_list = getattr(batch, 'patch_id', None)
                            pmap = self.leak_cls.get('patch_map', {})
                            for i in range(B):
                                li = (pid_list[i] if isinstance(pid_list, (list, tuple)) else pid_list)
                                yi = int(pmap.get(str(li), 0))
                                y[batch.batch == i] = yi
                            h_grl = self._GradReverse.apply(output['z_local'], alpha)
                            logits = self.model.patch_head(h_grl)
                            loss_ce = F.cross_entropy(logits, y)
                            losses['loss_leak_patch_ce'] = loss_ce
                            losses['total_loss'] = losses['total_loss'] + loss_ce
                        elif target == 'image' and getattr(self.model, 'image_head', None) is not None:
                            gid_list = getattr(batch, 'imageid', None)
                            gmap = self.leak_cls.get('image_map', {})
                            for i in range(B):
                                li = (gid_list[i] if isinstance(gid_list, (list, tuple)) else gid_list)
                                yi = int(gmap.get(str(li), 0))
                                y[batch.batch == i] = yi
                            h_grl = self._GradReverse.apply(output['z_local'], alpha)
                            logits = self.model.image_head(h_grl)
                            loss_ce = F.cross_entropy(logits, y)
                            losses['loss_leak_image_ce'] = loss_ce
                            losses['total_loss'] = losses['total_loss'] + loss_ce
            self.scaler.scale(losses['total_loss']).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()
            self.optimizer.zero_grad()
            
            # Accumulate
            for k, v in losses.items():
                if k not in total_losses:
                    total_losses[k] = 0.0
                total_losses[k] += (v.item() if hasattr(v, 'item') else float(v))
            n_batches += 1
            
        # Average
        avg_losses = {k: v / n_batches for k, v in total_losses.items()}
        return avg_losses
    
    def validate(self, loader: DataLoader) -> Dict[str, float]:
        self.model.eval()
        total_losses = {}
        n_batches = 0
        
        with torch.no_grad():
            for batch in loader:
                batch = batch.to(self.device)
                with torch.amp.autocast('cuda'):
                    if hasattr(batch, 'obs_rows') and hasattr(batch, 'obs_cols') and hasattr(batch, 'n_nodes') and hasattr(batch, 'n_genes'):
                        if hasattr(batch, 'obs_ptr') and hasattr(batch, 'batch'):
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
                        expr_mask_indices, masked_positions = self.masking_engine.mask_expression_sparse(
                            batch.obs_rows, batch.obs_cols, batch.n_nodes, batch.n_genes
                        )
                    else:
                        masked_x, expr_mask_indices = self.masking_engine.mask_expression(
                            batch.x, batch.obs_mask
                        )
                        masked_positions = None
                    x_in = masked_x if masked_positions is None else torch.empty((0, 0), device=batch.spatial_enc.device)
                    try:
                        n = int(getattr(batch, 'n_nodes', batch.x.size(0)))
                        g = int(getattr(batch, 'n_genes', batch.x.size(1)))
                        if hasattr(batch, 'obs_rows'):
                            obs_count = int(batch.obs_rows.numel())
                        else:
                            obs_count = int((batch.obs_mask > 0.5).sum().item())
                        masked_count = expr_mask_indices.shape[0] if expr_mask_indices.ndim == 2 else int(expr_mask_indices.sum().item())
                        if torch.cuda.is_available():
                            alloc = torch.cuda.memory_allocated(self.device)
                            reserv = torch.cuda.memory_reserved(self.device)
                            print(f"Val batch x={n}x{g} obs={obs_count} masked={masked_count} cuda_alloc={alloc} cuda_reserved={reserv}")
                        else:
                            print(f"Val batch x={n}x{g} obs={obs_count} masked={masked_count}")
                    except Exception:
                        pass
                    masked_edge_index = batch.edge_index
                    phenotype_mask_indices = None
                    masked_phenotype = None
                    if hasattr(batch, 'phenotype') and batch.phenotype is not None:
                        masked_phenotype, phenotype_mask_indices = self.masking_engine.mask_phenotype(batch.phenotype)
                    _N_total = int(batch.spatial_enc.size(0))
                    if hasattr(batch, 'n_genes'):
                        _ng = getattr(batch, 'n_genes')
                        _G_total = (int(_ng) if not isinstance(_ng, torch.Tensor) else int(_ng[0].item()))
                    else:
                        _G_total = int(self.model.decoder.expr_fc2.out_features)
                    output = self.model(
                        x=x_in,
                        edge_index=masked_edge_index,
                        spatial_enc=batch.spatial_enc,
                        phenotype=masked_phenotype,
                        phenotype_mask_indices=phenotype_mask_indices,
                        batch=batch.batch,
                        obs_mask=getattr(batch, 'obs_mask', None),
                        mask_indices=expr_mask_indices,
                        compute_full_expr=False,
                        obs_rows=getattr(batch, 'obs_rows', None),
                        obs_cols=getattr(batch, 'obs_cols', None),
                        obs_vals=getattr(batch, 'obs_vals', None),
                        masked_obs_positions=masked_positions,
                        x_shape=torch.tensor([_N_total, _G_total], device=batch.spatial_enc.device),
                        obs_coords=torch.stack([getattr(batch, 'obs_rows', torch.tensor([], dtype=torch.long)), getattr(batch, 'obs_cols', torch.tensor([], dtype=torch.long))], dim=1) if hasattr(batch, 'obs_rows') else None
                    )
                    
                    losses = self.loss_fn(
                        pred_expr=output['pred_expr'],
                        target_expr=(batch.x if hasattr(batch, 'x') else torch.empty((0, _G_total), device=batch.spatial_enc.device)),
                        obs_mask=batch.obs_mask,
                        mask_indices=expr_mask_indices,
                        pred_expr_masked_coords=output.get('pred_expr_masked_coords', None),
                        masked_coords=output.get('masked_coords', None),
                        pred_expr_obs_coords=output.get('pred_expr_obs_coords', None),
                        obs_coords=output.get('obs_coords', None),
                        target_expr_masked_vals=(getattr(batch, 'obs_vals', None)[masked_positions] if masked_positions is not None and hasattr(batch, 'obs_vals') else None),
                        target_expr_obs_vals=getattr(batch, 'obs_vals', None),
                        pred_phenotype=output['pred_phenotype'],
                        target_phenotype=getattr(batch, 'phenotype', None),
                        phenotype_mask_indices=phenotype_mask_indices,
                        z_local=output['z_local'],
                        batch_nodes=batch.batch,
                        token_specialization_reg=output.get('token_specialization_reg', None),
                        edge_index=batch.edge_index,
                        coord_pred=output.get('coord_pred', None),
                        coords=getattr(batch, 'coords', None)
                    )
                    if self.patch_monitor.get('enabled', False) and 'z_local' in output:
                        z_local = output['z_local']
                        B = int(batch.batch.max().item()) + 1
                        means = []
                        for i in range(B):
                            idx = (batch.batch == i)
                            if idx.any():
                                means.append(z_local[idx].mean(dim=0))
                        if len(means) >= 2:
                            M = torch.stack(means, dim=0)
                            var_means = M.var(dim=0).mean()
                            var_nodes = z_local.var(dim=0).mean()
                            leakage = (var_means / (var_nodes + 1e-8))
                            losses['patch_leakage'] = leakage.detach()
                
                for k, v in losses.items():
                    if k not in total_losses:
                        total_losses[k] = 0.0
                    total_losses[k] += (v.item() if hasattr(v, 'item') else float(v))
                n_batches += 1
                
        if n_batches == 0:
            return {}
            
        avg_losses = {k: v / n_batches for k, v in total_losses.items()}
        return avg_losses
    
    def fit(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int = 10, start_epoch: int = 0):
        for epoch in range(start_epoch, epochs):
            start_time = time.time()
            train_metrics = self.train_epoch(train_loader)
            val_metrics = self.validate(val_loader)
            end_time = time.time()
            
            print(f"Epoch {epoch+1}/{epochs} - Time: {end_time - start_time:.2f}s")
            print(f"  Train: {train_metrics}")
            print(f"  Val:   {val_metrics}")
            
            if (epoch + 1) % self.save_recent_every == 0:
                recent_path = os.path.join(self.output_dir, "checkpoint_recent.pt")
                save_checkpoint(recent_path, self.model, self.optimizer, epoch)
                print(f"  Saved recent checkpoint to {recent_path}")
            
            if val_metrics and 'total_loss' in val_metrics:
                current_loss = val_metrics['total_loss']
                loss_type = "Val"
            else:
                current_loss = train_metrics.get('total_loss', float('inf'))
                loss_type = "Train"
            
            if current_loss < self.best_val_loss:
                self.best_val_loss = current_loss
                best_path = os.path.join(self.output_dir, "checkpoint_best.pt")
                save_checkpoint(best_path, self.model, self.optimizer, epoch)
                print(f"  ✓ New best model! {loss_type} loss: {current_loss:.4f} - Saved to {best_path}")
            if self.save_all_epochs:
                try:
                    ep_path = os.path.join(self.output_dir, "model", f"checkpoint_epoch_{epoch+1}.pt")
                    save_checkpoint(ep_path, self.model, self.optimizer, epoch)
                    print(f"  Saved epoch checkpoint to {ep_path}")
                except Exception as e:
                    print(f"  Failed to save epoch checkpoint: {e}")
