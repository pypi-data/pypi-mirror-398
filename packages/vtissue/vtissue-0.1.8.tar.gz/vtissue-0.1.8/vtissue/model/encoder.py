import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import TransformerConv
from torch_geometric.utils import to_dense_batch
from typing import Optional

class SpatialGraphEncoder(nn.Module):
    """
    Graph Transformer Encoder with local and global attention.
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
        n_global_tokens_global: Optional[int] = None,
        n_global_tokens_local: Optional[int] = None,
        center_on_graph: bool = False
    ):
        super().__init__()
        self.d_model = d_model
        # Backward compatibility: if split not provided, treat all as local+global combined
        if n_global_tokens_global is None or n_global_tokens_local is None:
            # Default split: 2 global, rest local
            n_global_tokens_global = max(1, min(n_global_tokens, 2))
            n_global_tokens_local = max(0, n_global_tokens - n_global_tokens_global)
        self.n_global_tokens_global = n_global_tokens_global
        self.n_global_tokens_local = n_global_tokens_local
        self.n_global_tokens = self.n_global_tokens_global + self.n_global_tokens_local
        self.center_on_graph = bool(center_on_graph)
        
        # 1. Input Projections
        self.gene_weight = nn.Parameter(torch.randn(n_genes, d_model))
        self.gene_bias = nn.Parameter(torch.zeros(d_model))
        self.spatial_encoder = nn.Linear(n_spatial_features, d_model)
        
        # Gated Fusion for combining gene and spatial features
        self.fusion_gate = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.Sigmoid()
        )
        self.mask_embedding = nn.Parameter(torch.randn(d_model))
        self.mask_gate_proj = nn.Linear(d_model, d_model)
        
        if n_phenotypes > 0:
            self.phenotype_embedding = nn.Embedding(n_phenotypes, d_model)
            self.phenotype_mask_embedding = nn.Parameter(torch.randn(d_model))
        else:
            self.phenotype_embedding = None
            self.phenotype_mask_embedding = None
            
        
        # Global Tokens (two groups)
        self.global_tokens_global = nn.Parameter(torch.randn(self.n_global_tokens_global, d_model))
        self.global_tokens_local = nn.Parameter(torch.randn(self.n_global_tokens_local, d_model))
        
        # 2. Transformer Layers
        self.layers = nn.ModuleList([
            GraphTransformerLayer(d_model, n_heads, dropout)
            for _ in range(n_layers)
        ])
        self.use_checkpoint = True
        
    def forward(
        self, 
        x: torch.Tensor, 
        edge_index: torch.Tensor, 
        spatial_enc: torch.Tensor,
        phenotype: Optional[torch.Tensor] = None,
        phenotype_mask_indices: Optional[torch.Tensor] = None,
        batch: Optional[torch.Tensor] = None,
        obs_mask: Optional[torch.Tensor] = None,
        obs_rows: Optional[torch.Tensor] = None,
        obs_cols: Optional[torch.Tensor] = None,
        obs_vals: Optional[torch.Tensor] = None,
        masked_obs_positions: Optional[torch.Tensor] = None,
        x_shape: Optional[torch.Tensor] = None
    ):
        """
        Args:
            x: (N, n_genes) expression
            edge_index: (2, E)
            spatial_enc: (N, n_spatial_features)
            phenotype: (N,)
            sample_type: (N,)
            batch: (N,) batch assignment
        """
        # Encode gene and spatial features separately
        if obs_rows is not None and obs_cols is not None and obs_vals is not None and x_shape is not None:
            N = int(x_shape[0].item() if isinstance(x_shape, torch.Tensor) else int(x_shape[0]))
            # Sum contributions over observed genes
            W = self.gene_weight[obs_cols]
            contrib_all = obs_vals.unsqueeze(1) * W
            gene_h = torch.zeros(N, self.d_model, device=contrib_all.device, dtype=contrib_all.dtype)
            gene_h.index_add_(0, obs_rows, contrib_all)
            if masked_obs_positions is not None and masked_obs_positions.numel() > 0:
                Wm = self.gene_weight[obs_cols[masked_obs_positions]]
                vm = obs_vals[masked_obs_positions]
                contrib_mask = vm.unsqueeze(1) * Wm
                gene_h.index_add_(0, obs_rows[masked_obs_positions], -contrib_mask)
            gene_h = gene_h + self.gene_bias
            gene_h = F.gelu(gene_h)
        else:
            raise ValueError("Sparse observation coordinates required: provide obs_rows, obs_cols, obs_vals, and x_shape")
        spatial_h = self.spatial_encoder(spatial_enc)
        
        # Mask features: aggregate masked count per node and project
        if masked_obs_positions is not None and obs_rows is not None and masked_obs_positions.numel() > 0:
            N = int(self.n_global_tokens)  # placeholder; corrected below
            if x_shape is not None:
                N = int(x_shape[0].item() if isinstance(x_shape, torch.Tensor) else int(x_shape[0]))
            masked_rows = obs_rows[masked_obs_positions]
            mask_count = torch.zeros(N, dtype=gene_h.dtype, device=gene_h.device)
            mask_count.index_add_(0, masked_rows, torch.ones_like(masked_rows, dtype=gene_h.dtype))
            mask_feat = mask_count.unsqueeze(1) * self.mask_embedding
        else:
            mask_feat = torch.zeros_like(gene_h)
        # Gated fusion with mask conditioning: gate = sigmoid(W[gene; spatial] + U[mask_feat])
        combined = torch.cat([gene_h, spatial_h], dim=-1)
        gate_pre = self.fusion_gate[0](combined) + self.mask_gate_proj(mask_feat)
        gate = torch.sigmoid(gate_pre)
        h = gate * gene_h + (1 - gate) * spatial_h
        
        if self.phenotype_embedding is not None and phenotype is not None:
            safe_ph = phenotype
            if not torch.is_floating_point(safe_ph):
                safe_ph = safe_ph.clone()
            else:
                safe_ph = safe_ph.to(dtype=torch.long)
            invalid = (safe_ph < 0) | (safe_ph >= self.phenotype_embedding.num_embeddings)
            if invalid.any():
                safe_ph[invalid] = 0
            ph_emb = self.phenotype_embedding(safe_ph)
            if invalid.any():
                if self.phenotype_mask_embedding is not None:
                    ph_emb[invalid] = self.phenotype_mask_embedding
                else:
                    ph_emb[invalid] = 0.0
            if phenotype_mask_indices is not None and self.phenotype_mask_embedding is not None:
                ph_emb = ph_emb.clone()
                ph_emb[phenotype_mask_indices] = self.phenotype_mask_embedding
            h = h + ph_emb

        if self.center_on_graph:
            if batch is None:
                mu = h.mean(dim=0)
                h = h - mu
            else:
                B = int(batch.max().item()) + 1
                sums = torch.zeros(B, h.size(1), dtype=h.dtype, device=h.device)
                sums.index_add_(0, batch, h)
                counts = torch.bincount(batch, minlength=B).to(h.dtype).unsqueeze(1)
                mu = sums / counts.clamp(min=1)
                h = h - mu[batch]
            
        
        # Initialize global token per graph in batch
        if batch is None:
            batch_size = 1
            batch = torch.zeros(h.size(0), dtype=torch.long, device=h.device)
        else:
            batch_size = batch.max().item() + 1
        
        global_h_global = self.global_tokens_global.unsqueeze(0).expand(batch_size, -1, -1)
        global_h_local = self.global_tokens_local.unsqueeze(0).expand(batch_size, -1, -1)
        global_h = torch.cat([global_h_global, global_h_local], dim=1)
        
        # Pass through layers
        token_reg = 0.0
        for layer in self.layers:
            if self.use_checkpoint and self.training:
                def fn(h_in, g_in):
                    x_out, g_out, _ = layer(
                        h_in, edge_index, g_in, batch,
                        n_global_tokens_global=self.n_global_tokens_global,
                        n_global_tokens_local=self.n_global_tokens_local
                    )
                    return x_out, g_out
                h, global_h = torch.utils.checkpoint.checkpoint(fn, h, global_h, use_reentrant=False)
            else:
                h, global_h, reg = layer(
                    h, edge_index, global_h, batch,
                    n_global_tokens_global=self.n_global_tokens_global,
                    n_global_tokens_local=self.n_global_tokens_local
                )
                token_reg = token_reg + reg
        if len(self.layers) > 0:
            token_reg = token_reg / float(len(self.layers))
        
        return h, global_h, token_reg

class GraphTransformerLayer(nn.Module):
    def __init__(self, d_model: int, n_heads: int, dropout: float):
        super().__init__()
        # Local attention (GNN)
        self.local_attn = TransformerConv(
            d_model, d_model // n_heads, heads=n_heads, dropout=dropout, beta=True
        )
        self.norm1 = nn.LayerNorm(d_model)
        
        self.node_to_global_attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.global_to_node_attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.norm_global = nn.LayerNorm(d_model)
        self.norm_node_global = nn.LayerNorm(d_model)
        
        # FFN
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 2, d_model)
        )
        self.norm2 = nn.LayerNorm(d_model)
        
    def forward(self, x, edge_index, global_h, batch, n_global_tokens_global: int, n_global_tokens_local: int):
        h_local = self.local_attn(x, edge_index)
        x = self.norm1(x + h_local)
        dense_x, mask = to_dense_batch(x, batch)
        q_global = global_h
        key_padding = ~mask
        global_out, attn_weights = self.node_to_global_attn(
            q_global, dense_x, dense_x,
            key_padding_mask=key_padding,
            need_weights=True,
            average_attn_weights=True
        )
        global_h = self.norm_global(global_h + global_out)
        kv_global = global_h
        nodes_out, _ = self.global_to_node_attn(dense_x, kv_global, kv_global)
        dense_x = self.norm_node_global(dense_x + nodes_out)
        B = dense_x.size(0)
        for i in range(B):
            idx = (batch == i).nonzero(as_tuple=True)[0]
            if idx.numel() == 0:
                continue
            valid = mask[i]
            x[idx] = dense_x[i, valid]
        x = self.norm2(x + self.ffn(x))
        # Regularizer: penalize overlap among local tokens' attention distributions per graph
        reg = 0.0
        if n_global_tokens_local > 0:
            # attn_weights shape: (B, T, S) with average_attn_weights=True, T=K_total, S=max_nodes
            local_start = n_global_tokens_global
            local_end = n_global_tokens_global + n_global_tokens_local
            for i in range(B):
                valid = mask[i]  # (S,)
                P = attn_weights[i, local_start:local_end, :]  # (K_local, S)
                if valid.sum() == 0:
                    continue
                P = P[:, valid]  # (K_local, N_i)
                # Normalize rows to sum to 1 over valid nodes
                eps = 1e-8
                P = P / (P.sum(dim=1, keepdim=True) + eps)
                G = P @ P.t()  # (K_local, K_local)
                K = G.size(0)
                off_diag = G[~torch.eye(K, dtype=torch.bool, device=G.device)]
                reg = reg + off_diag.mean()
            reg = reg / max(B, 1)
        return x, global_h, reg
