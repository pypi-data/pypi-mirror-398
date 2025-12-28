import torch
import numpy as np
from typing import List, Optional, Dict, Union
from ..model.transformer import VirtualTissueModel

class PerturbationEngine:
    """
    Performs in silico perturbations on Virtual Tissue graphs.
    """
    def __init__(self, model: VirtualTissueModel, device: torch.device):
        self.model = model
        self.device = device
        self.model.eval()
        self.model.to(device)
        
    def _forward(self, batch):
        with torch.no_grad():
            output = self.model(
                x=batch.x,
                edge_index=batch.edge_index,
                spatial_enc=batch.spatial_enc,
                phenotype=getattr(batch, 'phenotype', None),
                batch=batch.batch
            )
        return output
        
    def perturb_gene_knockout(
        self, 
        batch, 
        gene_indices: List[int]
    ) -> Dict[str, torch.Tensor]:
        """
        Simulate gene knockout by setting expression of specific genes to 0.
        
        Args:
            batch: PyG Batch or Data object.
            gene_indices: List of gene indices to knockout.
            
        Returns:
            results: Dict containing 'baseline' and 'perturbed' outputs.
        """
        batch = batch.to(self.device)
        
        # Baseline
        baseline_output = self._forward(batch)
        
        # Perturbation
        # Clone batch to avoid modifying original
        perturbed_batch = batch.clone()
        
        # Set expression to 0 for target genes
        # x is (N, G)
        for gene_idx in gene_indices:
            perturbed_batch.x[:, gene_idx] = 0.0
            
        perturbed_output = self._forward(perturbed_batch)
        
        return {
            'baseline': baseline_output,
            'perturbed': perturbed_output
        }
        
    def perturb_cell_ablation(
        self,
        batch,
        phenotype_indices: List[int]
    ) -> Dict[str, torch.Tensor]:
        """
        Simulate cell ablation by removing nodes of specific phenotypes.
        
        Args:
            batch: PyG Batch or Data object.
            phenotype_indices: List of phenotype indices to remove.
            
        Returns:
            results: Dict containing 'baseline' and 'perturbed' outputs.
        """
        batch = batch.to(self.device)
        
        if not hasattr(batch, 'phenotype'):
            raise ValueError("Batch must have phenotype labels for ablation.")
            
        # Baseline
        baseline_output = self._forward(batch)
        
        # Identify nodes to keep
        # phenotype is (N,)
        mask = torch.ones(batch.num_nodes, dtype=torch.bool, device=self.device)
        for p_idx in phenotype_indices:
            mask = mask & (batch.phenotype != p_idx)
            
        # Subgraph
        # We need to re-index edges and filter features
        # PyG has utilities for this but let's do it manually or use subgraph
        from torch_geometric.utils import subgraph
        
        subset_edge_index, _ = subgraph(mask, batch.edge_index, relabel_nodes=True)
        
        # Create new batch/data
        # Note: This is simplified and might break if batch.batch is complex
        # But for single graph or simple batch it should work if we handle attributes
        
        from torch_geometric.data import Data
        
        perturbed_data = Data(
            x=batch.x[mask],
            edge_index=subset_edge_index,
            spatial_enc=batch.spatial_enc[mask],
            phenotype=batch.phenotype[mask]
        )
             
        if hasattr(batch, 'batch') and batch.batch is not None:
            perturbed_data.batch = batch.batch[mask]
            
        # Forward on perturbed
        # Note: Global token logic might depend on batch size which changes if we remove nodes?
        # No, batch size (number of graphs) stays same, but number of nodes changes.
        # Unless we remove ALL nodes in a graph.
        
        perturbed_output = self._forward(perturbed_data)
        
        return {
            'baseline': baseline_output,
            'perturbed': perturbed_output
        }

    def compute_perturbation_effect(
        self,
        results: Dict[str, Dict[str, torch.Tensor]]
    ) -> Dict[str, float]:
        """
        Compute metrics quantifying the effect of perturbation.
        """
        baseline = results['baseline']
        perturbed = results['perturbed']
        
        # Latent shift (Global)
        # z_global: (Batch, D)
        # We can compute MSE or Cosine distance
        z_global_base = baseline['z_global']
        z_global_pert = perturbed['z_global']
        
        # If ablation, batch size might be same (number of graphs)
        # Check shapes
        if z_global_base.shape != z_global_pert.shape:
             # This might happen if we removed a whole graph?
             # Or if our ablation logic didn't preserve batch structure correctly?
             # For now assume shapes match
             pass
             
        mse_global = torch.nn.functional.mse_loss(z_global_base, z_global_pert).item()
        
        # Local shift?
        # If ablation, nodes are different, so we can't compare 1-to-1 easily.
        # If knockout, nodes are same.
        
        metrics = {
            'mse_global': mse_global
        }
        
        if baseline['z_local'].shape == perturbed['z_local'].shape:
            mse_local = torch.nn.functional.mse_loss(baseline['z_local'], perturbed['z_local']).item()
            metrics['mse_local'] = mse_local
            
        return metrics
