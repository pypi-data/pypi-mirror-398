import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict

class VirtualTissueLoss(nn.Module):
    def __init__(
        self,
        lambda_expr_mask: float = 1.0,
        lambda_reconstruction: float = 0.0,
        lambda_celltype: float = 0.0,
        lambda_cnp: float = 0.0,
        cnp_temperature: float = 0.1,
        lambda_token_specialization: float = 0.0,
        lambda_coord: float = 0.0
        ,
        spatial_weight_lambda: float = 0.0,
        spatial_weights: Optional[torch.Tensor] = None,
        cnp_enable_subsample: bool = True,
        cnp_max_nodes: int = 8192,
        cnp_subsample_ratio: float = 1.0
    ):
        super().__init__()
        self.lambda_expr_mask = lambda_expr_mask
        self.lambda_reconstruction = lambda_reconstruction
        self.lambda_celltype = lambda_celltype
        self.lambda_cnp = lambda_cnp
        self.cnp_temperature = cnp_temperature
        self.lambda_token_specialization = lambda_token_specialization
        self.lambda_coord = lambda_coord
        self.spatial_weight_lambda = spatial_weight_lambda
        self.cnp_enable_subsample = cnp_enable_subsample
        self.cnp_max_nodes = int(cnp_max_nodes)
        self.cnp_subsample_ratio = float(cnp_subsample_ratio)
        self.register_buffer("spatial_weights", None)
        if spatial_weights is not None:
            w = torch.tensor(spatial_weights, dtype=torch.float32)
            self.register_buffer("spatial_weights", w)
        
    def forward(
        self,
        pred_expr: torch.Tensor,
        target_expr: torch.Tensor,
        obs_mask: torch.Tensor,
        mask_indices: Optional[torch.Tensor] = None,
        pred_expr_masked_coords: Optional[torch.Tensor] = None,
        masked_coords: Optional[torch.Tensor] = None,
        pred_expr_obs_coords: Optional[torch.Tensor] = None,
        obs_coords: Optional[torch.Tensor] = None,
        pred_phenotype: Optional[torch.Tensor] = None,
        target_phenotype: Optional[torch.Tensor] = None,
        phenotype_mask_indices: Optional[torch.Tensor] = None,
        z_local: Optional[torch.Tensor] = None,
        batch_nodes: Optional[torch.Tensor] = None,
        edge_index: Optional[torch.Tensor] = None,
        token_specialization_reg: Optional[torch.Tensor] = None,
        coord_pred: Optional[torch.Tensor] = None,
        coords: Optional[torch.Tensor] = None,
        target_expr_masked_vals: Optional[torch.Tensor] = None,
        target_expr_obs_vals: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Compute total loss and components.
        """
        losses = {}
        total_loss = 0.0
        
        # 1. Expression Mask Loss
        if self.lambda_expr_mask > 0 and mask_indices is not None:
            if pred_expr_masked_coords is not None and masked_coords is not None:
                rows = masked_coords[:, 0]
                cols = masked_coords[:, 1]
                if target_expr_masked_vals is not None:
                    tgt = target_expr_masked_vals
                else:
                    tgt = target_expr[rows, cols]
                err = (pred_expr_masked_coords - tgt) ** 2
                if err.numel() > 0:
                    if self.spatial_weight_lambda > 0.0 and self.spatial_weights is not None:
                        G = int(self.spatial_weights.numel())
                        sum_err = torch.zeros(G, device=tgt.device, dtype=tgt.dtype)
                        cnt = torch.zeros(G, device=tgt.device, dtype=tgt.dtype)
                        sum_err.index_add_(0, cols, err)
                        cnt.index_add_(0, cols, torch.ones_like(err))
                        per_gene = sum_err / (cnt + 1e-8)
                        w = self.spatial_weights
                        w = w / (w.sum() + 1e-8)
                        loss_expr_mask = (per_gene * w).sum()
                    else:
                        loss_expr_mask = err.mean()
                else:
                    loss_expr_mask = torch.tensor(0.0, device=tgt.device)
                losses['loss_expr_mask'] = loss_expr_mask
                total_loss += self.lambda_expr_mask * loss_expr_mask
            else:
                if mask_indices.dtype == torch.bool:
                    mask = mask_indices & (obs_mask > 0.5)
                    if mask.sum() > 0:
                        loss_unweighted = ((pred_expr - target_expr) ** 2)[mask].mean()
                        if self.spatial_weight_lambda > 0.0 and self.spatial_weights is not None and self.spatial_weights.numel() == target_expr.size(1):
                            N, G = target_expr.shape
                            mask_2d = mask.view(N, G)
                            loss_weighted = self._weighted_gene_mse(pred_expr, target_expr, mask_2d)
                            loss_expr_mask = (1.0 - self.spatial_weight_lambda) * loss_unweighted + self.spatial_weight_lambda * loss_weighted
                        else:
                            loss_expr_mask = loss_unweighted
                        losses['loss_expr_mask'] = loss_expr_mask
                        total_loss += self.lambda_expr_mask * loss_expr_mask
                    else:
                        losses['loss_expr_mask'] = torch.tensor(0.0, device=target_expr.device)
                else:
                    coords = mask_indices
                    if coords.numel() > 0:
                        rows = coords[:, 0]
                        cols = coords[:, 1]
                        err = ((pred_expr - target_expr)[rows, cols]) ** 2
                        if err.numel() > 0:
                            if self.spatial_weight_lambda > 0.0 and self.spatial_weights is not None and self.spatial_weights.numel() == target_expr.size(1):
                                G = target_expr.size(1)
                                sum_err = torch.zeros(G, device=target_expr.device, dtype=target_expr.dtype)
                                cnt = torch.zeros(G, device=target_expr.device, dtype=target_expr.dtype)
                                sum_err.index_add_(0, cols, err)
                                cnt.index_add_(0, cols, torch.ones_like(err))
                                per_gene = sum_err / (cnt + 1e-8)
                                w = self.spatial_weights
                                w = w / (w.sum() + 1e-8)
                                loss_expr_mask = (per_gene * w).sum()
                            else:
                                loss_expr_mask = err.mean()
                        else:
                            loss_expr_mask = torch.tensor(0.0, device=target_expr.device)
                    else:
                        loss_expr_mask = torch.tensor(0.0, device=target_expr.device)
                    losses['loss_expr_mask'] = loss_expr_mask
                    total_loss += self.lambda_expr_mask * loss_expr_mask
                
        # 2. Reconstruction Loss (Global)
        if self.lambda_reconstruction > 0:
            if pred_expr_obs_coords is not None and obs_coords is not None:
                rows = obs_coords[:, 0]
                cols = obs_coords[:, 1]
                tgt = target_expr_obs_vals if target_expr_obs_vals is not None else target_expr[rows, cols]
                err = (pred_expr_obs_coords - tgt) ** 2
                if err.numel() > 0:
                    if self.spatial_weight_lambda > 0.0 and self.spatial_weights is not None:
                        G = int(self.spatial_weights.numel())
                        sum_err = torch.zeros(G, device=tgt.device, dtype=tgt.dtype)
                        cnt = torch.zeros(G, device=tgt.device, dtype=tgt.dtype)
                        sum_err.index_add_(0, cols, err)
                        cnt.index_add_(0, cols, torch.ones_like(err))
                        per_gene = sum_err / (cnt + 1e-8)
                        w = self.spatial_weights
                        w = w / (w.sum() + 1e-8)
                        loss_recon = (per_gene * w).sum()
                    else:
                        loss_recon = err.mean()
                else:
                    loss_recon = torch.tensor(0.0, device=tgt.device)
                losses['loss_reconstruction'] = loss_recon
                total_loss += self.lambda_reconstruction * loss_recon
            else:
                obs_coords2 = (obs_mask > 0.5).nonzero(as_tuple=False)
                if obs_coords2.numel() > 0:
                    rows = obs_coords2[:, 0]
                    cols = obs_coords2[:, 1]
                    err = ((pred_expr - target_expr)[rows, cols]) ** 2
                    if err.numel() > 0:
                        if self.spatial_weight_lambda > 0.0 and self.spatial_weights is not None and self.spatial_weights.numel() == target_expr.size(1):
                            G = target_expr.size(1)
                            sum_err = torch.zeros(G, device=target_expr.device, dtype=target_expr.dtype)
                            cnt = torch.zeros(G, device=target_expr.device, dtype=target_expr.dtype)
                            sum_err.index_add_(0, cols, err)
                            cnt.index_add_(0, cols, torch.ones_like(err))
                            per_gene = sum_err / (cnt + 1e-8)
                            w = self.spatial_weights
                            w = w / (w.sum() + 1e-8)
                            loss_recon = (per_gene * w).sum()
                        else:
                            loss_recon = err.mean()
                    else:
                        loss_recon = torch.tensor(0.0, device=target_expr.device)
                    losses['loss_reconstruction'] = loss_recon
                    total_loss += self.lambda_reconstruction * loss_recon
                else:
                    losses['loss_reconstruction'] = torch.tensor(0.0, device=target_expr.device)
                
        # 3. Cell Type Loss
        if self.lambda_celltype > 0 and pred_phenotype is not None and target_phenotype is not None:
            if phenotype_mask_indices is not None:
                # Only on masked
                mask = phenotype_mask_indices
                if mask.sum() > 0:
                    loss_celltype = F.cross_entropy(pred_phenotype[mask], target_phenotype[mask])
                    losses['loss_celltype'] = loss_celltype
                    total_loss += self.lambda_celltype * loss_celltype
            else:
                # All
                loss_celltype = F.cross_entropy(pred_phenotype, target_phenotype)
                losses['loss_celltype'] = loss_celltype
                total_loss += self.lambda_celltype * loss_celltype
                
        # 4. Contrastive Neighborhood Prediction (CNP)
        if self.lambda_cnp > 0 and z_local is not None and edge_index is not None:
            N, D = z_local.size()
            src, dst = edge_index[0], edge_index[1]
            sum_nei = torch.zeros(N, D, device=z_local.device, dtype=z_local.dtype)
            sum_nei.index_add_(0, dst, z_local[src])
            deg = torch.zeros(N, device=z_local.device, dtype=z_local.dtype)
            deg.index_add_(0, dst, torch.ones_like(dst, dtype=z_local.dtype))
            valid = deg > 0
            if valid.sum() > 1:
                h_nei = sum_nei / deg.clamp(min=1).unsqueeze(-1)
                sel = valid.nonzero(as_tuple=True)[0]
                M_full = int(sel.numel())
                M_cap = M_full
                if self.cnp_enable_subsample:
                    if self.cnp_subsample_ratio < 1.0:
                        M_cap = int(M_full * self.cnp_subsample_ratio)
                    M_cap = min(M_cap, self.cnp_max_nodes)
                if M_cap < M_full:
                    idx = torch.randperm(M_full, device=z_local.device)[:M_cap]
                    sel = sel[idx]
                z_norm = torch.nn.functional.normalize(z_local[sel], dim=-1)
                h_norm = torch.nn.functional.normalize(h_nei[sel], dim=-1)
                sim = (z_norm @ h_norm.t()) / self.cnp_temperature
                M = sim.size(0)
                targets = torch.arange(M, device=sim.device)
                loss_rows = F.cross_entropy(sim, targets)
                loss_cols = F.cross_entropy(sim.t(), targets)
                loss_cnp = 0.5 * (loss_rows + loss_cols)
            else:
                loss_cnp = torch.tensor(0.0, device=z_local.device)
            losses['loss_cnp'] = loss_cnp
            total_loss += self.lambda_cnp * loss_cnp
        
        # 5. Coordinate Prediction Loss
        if self.lambda_coord > 0 and coord_pred is not None and coords is not None:
            loss_coord = F.mse_loss(coord_pred, coords)
            losses['loss_coord'] = loss_coord
            total_loss += self.lambda_coord * loss_coord

        # 7. Token Specialization Regularizer
        if self.lambda_token_specialization > 0 and token_specialization_reg is not None:
            loss_tok = torch.as_tensor(
                token_specialization_reg,
                dtype=torch.float32,
                device=(z_local.device if z_local is not None else (target_expr.device if target_expr is not None else None))
            )
            losses['loss_token_specialization'] = loss_tok
            total_loss += self.lambda_token_specialization * loss_tok
        
        if not isinstance(total_loss, torch.Tensor):
            total_loss = torch.tensor(
                float(total_loss),
                dtype=torch.float32,
                device=(target_expr.device if target_expr is not None else None)
            )
        losses['total_loss'] = total_loss
        return losses

    def _weighted_gene_mse(self, pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        err = (pred - target) ** 2 * mask.float()
        per_gene = err.sum(dim=0) / (mask.float().sum(dim=0) + 1e-8)
        if self.spatial_weights is None:
            return per_gene.mean()
        w = self.spatial_weights
        w = w / (w.sum() + 1e-8)
        return (per_gene * w).sum()
