import torch
import torch.nn as nn
from typing import Optional, Tuple
from .encoder import SpatialGraphEncoder
from .decoder import GraphDecoder

class VirtualTissueModel(nn.Module):
    """
    Virtual Tissue Graph Transformer Model.
    """
    def __init__(
        self,
        n_genes: int,
        d_model: int = 128,
        n_heads: int = 4,
        n_layers: int = 2,
        n_spatial_features: int = 40,
        n_phenotypes: int = 0,
        dropout: float = 0.1,
        n_global_tokens: int = 8,
        n_global_tokens_global: int | None = None,
        n_global_tokens_local: int | None = None,
        center_on_graph: bool = False,
        n_patch_classes: int = 0,
        n_image_classes: int = 0
    ):
        super().__init__()
        
        self.encoder = SpatialGraphEncoder(
            n_genes=n_genes,
            d_model=d_model,
            n_heads=n_heads,
            n_layers=n_layers,
            n_spatial_features=n_spatial_features,
            n_phenotypes=n_phenotypes,
            dropout=dropout,
            n_global_tokens=n_global_tokens,
            n_global_tokens_global=n_global_tokens_global,
            n_global_tokens_local=n_global_tokens_local,
            center_on_graph=center_on_graph
        )
        
        self.decoder = GraphDecoder(
            d_model=d_model,
            n_genes=n_genes,
            n_phenotypes=n_phenotypes
        )
        self.coord_head = nn.Linear(d_model, 2)
        self.patch_head = nn.Sequential(nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, int(n_patch_classes))) if int(n_patch_classes) > 0 else None
        self.image_head = nn.Sequential(nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, int(n_image_classes))) if int(n_image_classes) > 0 else None
        self.model_meta = {
            'n_genes': int(n_genes),
            'd_model': int(d_model),
            'n_heads': int(n_heads),
            'n_layers': int(n_layers),
            'n_spatial_features': int(n_spatial_features),
            'n_phenotypes': int(n_phenotypes),
            'dropout': float(dropout),
            'n_global_tokens': int(n_global_tokens),
            'n_global_tokens_global': int(self.encoder.n_global_tokens_global),
            'n_global_tokens_local': int(self.encoder.n_global_tokens_local),
            'n_patch_classes': int(n_patch_classes),
            'n_image_classes': int(n_image_classes)
        }
        
    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        spatial_enc: torch.Tensor,
        phenotype: Optional[torch.Tensor] = None,
        phenotype_mask_indices: Optional[torch.Tensor] = None,
        sample_type: Optional[torch.Tensor] = None,
        batch: Optional[torch.Tensor] = None,
        obs_mask: Optional[torch.Tensor] = None,
        mask_indices: Optional[torch.Tensor] = None,
        compute_full_expr: bool = True,
        obs_rows: Optional[torch.Tensor] = None,
        obs_cols: Optional[torch.Tensor] = None,
        obs_vals: Optional[torch.Tensor] = None,
        masked_obs_positions: Optional[torch.Tensor] = None,
        x_shape: Optional[torch.Tensor] = None,
        obs_coords: Optional[torch.Tensor] = None
    ):
        """
        Forward pass.
        """
        # Encode
        h, global_tokens, token_reg = self.encoder(
            x=x,
            edge_index=edge_index,
            spatial_enc=spatial_enc,
            phenotype=phenotype,
            phenotype_mask_indices=phenotype_mask_indices,
            batch=batch,
            obs_mask=obs_mask,
            obs_rows=obs_rows,
            obs_cols=obs_cols,
            obs_vals=obs_vals,
            masked_obs_positions=masked_obs_positions,
            x_shape=x_shape
        )
        # Only aggregate global group for graph-level representations
        Kg = self.encoder.n_global_tokens_global
        pooled_global = global_tokens[:, :Kg, :].mean(dim=1)
        if compute_full_expr:
            pred_expr, pred_phenotype = self.decoder(
                h=h,
                global_h=pooled_global,
                batch=batch
            )
            pred_expr_masked_coords = None
            pred_expr_obs_coords = None
            masked_coords = None
            obs_coords = None
        else:
            pred_expr = None
            pred_phenotype = self.decoder.predict_phenotype(h)
            pred_expr_masked_coords = None
            masked_coords = None
            if mask_indices is not None and mask_indices.numel() > 0:
                rows = mask_indices[:, 0]
                cols = mask_indices[:, 1]
                pred_expr_masked_coords = self.decoder.predict_expr_at_indices(h, rows, cols)
                masked_coords = mask_indices
            if obs_coords is not None and obs_coords.numel() > 0:
                rows_o = obs_coords[:, 0]
                cols_o = obs_coords[:, 1]
                pred_expr_obs_coords = self.decoder.predict_expr_at_indices(h, rows_o, cols_o)
            elif obs_mask is not None:
                obs_b = (obs_mask > 0)
                obs_coords2 = obs_b.nonzero(as_tuple=False)
                if obs_coords2.numel() > 0:
                    rows_o = obs_coords2[:, 0]
                    cols_o = obs_coords2[:, 1]
                    pred_expr_obs_coords = self.decoder.predict_expr_at_indices(h, rows_o, cols_o)
                    obs_coords = obs_coords2
                else:
                    pred_expr_obs_coords = None
                    obs_coords = None
            else:
                pred_expr_obs_coords = None
                obs_coords = None
        coord_pred = self.coord_head(h)
        pred_patch = self.patch_head(h) if self.patch_head is not None else None
        pred_image = self.image_head(h) if self.image_head is not None else None
        
        return {
            'pred_expr': pred_expr,
            'pred_phenotype': pred_phenotype,
            'z_local': h,
            'z_global': pooled_global,
            'z_global_tokens': global_tokens,
            'token_specialization_reg': token_reg,
            'coord_pred': coord_pred,
            'pred_patch_id': pred_patch,
            'pred_image_id': pred_image,
            'pred_expr_masked_coords': pred_expr_masked_coords,
            'masked_coords': masked_coords,
            'pred_expr_obs_coords': pred_expr_obs_coords,
            'obs_coords': obs_coords
        }
