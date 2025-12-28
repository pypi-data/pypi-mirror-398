import torch
import numpy as np
from typing import Tuple, Optional

class MaskingEngine:
    """
    Handles masking of expression and edges for self-supervision.
    """
    def __init__(
        self,
        mask_ratio_expr: float = 0.15,
        mask_ratio_edge: float = 0.15,
        mask_ratio_phenotype: float = 0.15,
        cell_mask_ratio_expr: float = 0.0
    ):
        self.mask_ratio_expr = mask_ratio_expr
        self.mask_ratio_edge = mask_ratio_edge
        self.mask_ratio_phenotype = mask_ratio_phenotype
        self.cell_mask_ratio_expr = cell_mask_ratio_expr
        
    def mask_expression(
        self, 
        x: torch.Tensor, 
        obs_mask: torch.Tensor,
        generator: Optional[torch.Generator] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Mask expression values.
        
        Args:
            x: (N, G) expression matrix.
            obs_mask: (N, G) binary mask (1 = observed).
            
        Returns:
            masked_x: x with masked values set to 0.
            target_mask: (N, G) binary mask (1 = masked and should be predicted).
        """
        N, G = x.shape
        device = x.device
        gen = generator
        
        # Cell-level masking: select a subset of cells to fully mask
        cell_mask = torch.zeros(N, dtype=torch.bool, device=device)
        if self.cell_mask_ratio_expr > 0.0:
            num_cells_mask = int(N * self.cell_mask_ratio_expr)
            if num_cells_mask > 0:
                perm = torch.randperm(N, generator=gen, device=device)
                cell_mask[perm[:num_cells_mask]] = True
        
        obs = (obs_mask > 0.5)
        counts = obs.sum(dim=1).to(torch.int64)
        idx = obs.nonzero(as_tuple=False)
        offsets = torch.empty(N + 1, dtype=torch.int64, device=device)
        offsets[0] = 0
        if N > 0:
            offsets[1:] = counts.cumsum(0)
        masked_rows = []
        masked_cols = []
        for i in range(N):
            start = offsets[i].item()
            end = offsets[i + 1].item()
            c = end - start
            if c == 0:
                continue
            genes_i = idx[start:end, 1]
            if cell_mask[i]:
                masked_rows.append(torch.full((c,), i, dtype=torch.long, device=device))
                masked_cols.append(genes_i)
                continue
            k = int(float(c) * float(self.mask_ratio_expr))
            if k <= 0:
                continue
            perm = torch.randperm(c, generator=gen, device=device)
            sel = perm[:k]
            masked_rows.append(torch.full((sel.numel(),), i, dtype=torch.long, device=device))
            masked_cols.append(genes_i[sel])
        if len(masked_rows) > 0:
            rows = torch.cat(masked_rows, dim=0)
            cols = torch.cat(masked_cols, dim=0)
            masked_pairs = torch.stack([rows, cols], dim=1)
        else:
            masked_pairs = torch.empty((0, 2), dtype=torch.long, device=device)
        masked_x = x.clone()
        if masked_pairs.numel() > 0:
            masked_x[masked_pairs[:, 0], masked_pairs[:, 1]] = 0.0
        return masked_x, masked_pairs

    def mask_expression_sparse(
        self,
        obs_rows: torch.Tensor,
        obs_cols: torch.Tensor,
        n_nodes: Optional[torch.Tensor] = None,
        n_genes: Optional[torch.Tensor] = None,
        generator: Optional[torch.Generator] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        device = obs_rows.device
        if n_nodes is None:
            N = int(obs_rows.max().item()) + 1 if obs_rows.numel() > 0 else 0
        elif isinstance(n_nodes, torch.Tensor):
            N = int(n_nodes.item()) if n_nodes.numel() == 1 else (int(obs_rows.max().item()) + 1 if obs_rows.numel() > 0 else 0)
        else:
            N = int(n_nodes)
        gen = generator
        counts = torch.bincount(obs_rows, minlength=N).to(torch.int64)
        offsets = torch.empty(N + 1, dtype=torch.int64, device=device)
        offsets[0] = 0
        if N > 0:
            offsets[1:] = counts.cumsum(0)
        masked_rows = []
        masked_cols = []
        masked_positions = []
        # Optional full-cell masking
        cell_mask = torch.zeros(N, dtype=torch.bool, device=device)
        if self.cell_mask_ratio_expr > 0.0:
            num_cells_mask = int(N * self.cell_mask_ratio_expr)
            if num_cells_mask > 0:
                perm = torch.randperm(N, generator=gen, device=device)
                cell_mask[perm[:num_cells_mask]] = True
        for i in range(N):
            start = offsets[i].item()
            end = offsets[i + 1].item()
            c = end - start
            if c == 0:
                continue
            genes_i = obs_cols[start:end]
            if cell_mask[i]:
                masked_rows.append(torch.full((c,), i, dtype=torch.long, device=device))
                masked_cols.append(genes_i)
                masked_positions.append(torch.arange(start, end, dtype=torch.long, device=device))
                continue
            k = int(float(c) * float(self.mask_ratio_expr))
            if k <= 0:
                continue
            perm = torch.randperm(c, generator=gen, device=device)
            sel = perm[:k]
            masked_rows.append(torch.full((sel.numel(),), i, dtype=torch.long, device=device))
            masked_cols.append(genes_i[sel])
            masked_positions.append(sel.to(torch.long) + start)
        if len(masked_rows) > 0:
            rows = torch.cat(masked_rows, dim=0)
            cols = torch.cat(masked_cols, dim=0)
            positions = torch.cat(masked_positions, dim=0)
            masked_pairs = torch.stack([rows, cols], dim=1)
        else:
            masked_pairs = torch.empty((0, 2), dtype=torch.long, device=device)
            positions = torch.empty((0,), dtype=torch.long, device=device)
        return masked_pairs, positions
    
    def mask_edges(
        self, 
        edge_index: torch.Tensor, 
        num_nodes: int
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Mask edges for link prediction.
        
        Args:
            edge_index: (2, E)
            num_nodes: Number of nodes.
            
        Returns:
            masked_edge_index: (2, E_keep)
            pos_edge_label_index: (2, E_drop) - edges that were dropped (positive samples)
            neg_edge_label_index: (2, E_drop) - random non-existent edges (negative samples)
        """
        num_edges = edge_index.size(1)
        num_mask = int(num_edges * self.mask_ratio_edge)
        
        # Random permutation
        perm = torch.randperm(num_edges)
        mask_idx = perm[:num_mask]
        keep_idx = perm[num_mask:]
        
        masked_edge_index = edge_index[:, keep_idx]
        pos_edge_label_index = edge_index[:, mask_idx]
        
        # Negative sampling
        # We want same number of negatives as positives
        from torch_geometric.utils import negative_sampling
        neg_edge_label_index = negative_sampling(
            edge_index=edge_index, # Don't sample existing edges
            num_nodes=num_nodes,
            num_neg_samples=num_mask
        )
        
        return masked_edge_index, pos_edge_label_index, neg_edge_label_index

    def mask_phenotype(
        self,
        phenotype: torch.Tensor,
        generator: Optional[torch.Generator] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Mask phenotype labels for masked-label modeling.

        Args:
            phenotype: (N,) integer labels.

        Returns:
            masked_phenotype: (N,) labels (currently identical to input).
                               The encoder applies a learned [MASK] embedding
                               at positions indicated by target_mask.
            target_mask: (N,) boolean mask of cells to train on.
        """
        # Assuming 0 is not a special token yet, or we need to handle it in embedding.
        # For now, let's assume the caller handles the token replacement or we return a mask.
        
        if generator is not None:
            rand = torch.rand(phenotype.shape, generator=generator, device=phenotype.device)
        else:
            rand = torch.rand_like(phenotype.float())
        target_mask = (rand < self.mask_ratio_phenotype)
        
        masked_phenotype = phenotype.clone()
        # We can't set to -1 if embedding expects non-negative.
        # We'll leave it as is, but the caller should use target_mask to replace with MASK token
        # before passing to model.
        
        return masked_phenotype, target_mask
