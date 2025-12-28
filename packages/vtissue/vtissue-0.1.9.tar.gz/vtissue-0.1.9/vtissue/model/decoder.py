import torch
import torch.nn as nn
from typing import Optional, Tuple

class GraphDecoder(nn.Module):
    def __init__(
        self,
        d_model: int,
        n_genes: int,
        n_phenotypes: int = 0
    ):
        super().__init__()
        self.expr_fc1 = nn.Linear(d_model, d_model)
        self.expr_fc2 = nn.Linear(d_model, n_genes)
        if n_phenotypes > 0:
            self.phenotype_head = nn.Sequential(
                nn.Linear(d_model, d_model),
                nn.ReLU(),
                nn.Linear(d_model, n_phenotypes)
            )
        else:
            self.phenotype_head = None

    def _expr_hidden(self, h: torch.Tensor) -> torch.Tensor:
        return torch.relu(self.expr_fc1(h))

    def predict_expr_full(self, h: torch.Tensor) -> torch.Tensor:
        hidden = self._expr_hidden(h)
        return self.expr_fc2(hidden)

    def predict_expr_at_indices(self, h: torch.Tensor, rows: torch.Tensor, cols: torch.Tensor) -> torch.Tensor:
        hidden = self._expr_hidden(h)
        w = self.expr_fc2.weight[cols]
        b = self.expr_fc2.bias[cols]
        v = (hidden[rows] * w).sum(dim=1) + b
        return v

    def forward(
        self,
        h: torch.Tensor,
        global_h: torch.Tensor,
        batch: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        pred_expr = self.predict_expr_full(h)
        pred_phenotype = None
        if self.phenotype_head is not None:
            pred_phenotype = self.phenotype_head(h)
        return pred_expr, pred_phenotype

    def predict_phenotype(self, h: torch.Tensor) -> Optional[torch.Tensor]:
        if self.phenotype_head is None:
            return None
        return self.phenotype_head(h)
