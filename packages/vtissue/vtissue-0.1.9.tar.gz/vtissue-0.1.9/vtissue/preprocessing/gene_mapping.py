import pandas as pd
import numpy as np
from scipy import sparse
import os
from typing import List, Tuple, Optional

class GlobalGeneMapper:
    """
    Maps panel-specific genes to a global gene universe.
    """
    def __init__(self, gene_list_path: str):
        """
        Initialize with path to the global gene list file.
        
        Args:
            gene_list_path: Path to text file containing global gene list (one per line).
        """
        if not os.path.exists(gene_list_path):
            raise FileNotFoundError(f"Gene list file not found at: {gene_list_path}")
            
        # Read gene list, assuming header "Gene name" or similar, or just list
        # We'll try to be robust.
        try:
            df = pd.read_csv(gene_list_path, header=None)
            # Check if first row looks like a header
            if "Gene" in str(df.iloc[0, 0]) or "name" in str(df.iloc[0, 0]):
                self.genes = df.iloc[1:, 0].astype(str).values
            else:
                self.genes = df.iloc[:, 0].astype(str).values
        except Exception as e:
            raise ValueError(f"Failed to read gene list: {e}")
            
        self.gene_to_idx = {gene: i for i, gene in enumerate(self.genes)}
        self.n_global_genes = len(self.genes)
        
    def map_genes(self, panel_genes: List[str]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Map a list of panel genes to global indices.
        
        Args:
            panel_genes: List of gene names in the panel.
            
        Returns:
            panel_indices: Indices of genes in the panel (0 to len(panel_genes)-1) that were found.
            global_indices: Corresponding indices in the global gene list.
            unmapped_genes: List of genes from the panel that were NOT found in the global list.
        """
        panel_idxs = []
        global_idxs = []
        unmapped = []
        
        for i, gene in enumerate(panel_genes):
            if gene in self.gene_to_idx:
                panel_idxs.append(i)
                global_idxs.append(self.gene_to_idx[gene])
            else:
                unmapped.append(gene)
                
        return np.array(panel_idxs, dtype=int), np.array(global_idxs, dtype=int), unmapped
    
    def create_global_matrices(self, adata, layer: Optional[str] = None) -> Tuple[sparse.csr_matrix, sparse.csr_matrix, List[str]]:
        """
        Create sparse global expression and mask matrices for an AnnData object.
        
        Args:
            adata: AnnData object with .var_names containing gene names.
            layer: Key in adata.layers to use for expression values. If None, use adata.X.
            
        Returns:
            global_expr: Sparse matrix (n_cells, n_global_genes) with expression values.
            mask: Sparse matrix (n_cells, n_global_genes) with 1s where genes were measured.
            unmapped_genes: List of genes present in adata but missing from global gene list.
        """
        n_cells = adata.shape[0]
        panel_genes = adata.var_names.tolist()
        
        panel_idxs, global_idxs, unmapped_genes = self.map_genes(panel_genes)
        
        if len(panel_idxs) == 0:
            # No genes mapped? Return empty sparse matrices
            return (
                sparse.csr_matrix((n_cells, self.n_global_genes), dtype=np.float32),
                sparse.csr_matrix((n_cells, self.n_global_genes), dtype=np.float32),
                unmapped_genes
            )
            
        # Get expression values for mapped genes
        if layer is not None:
            if layer not in adata.layers:
                raise ValueError(f"Layer '{layer}' not found in adata.layers")
            source_matrix = adata.layers[layer]
        else:
            source_matrix = adata.X
            
        if sparse.issparse(source_matrix):
            expr_values = source_matrix[:, panel_idxs].toarray()
        else:
            expr_values = source_matrix[:, panel_idxs]
            
        # Construct global sparse matrix
        # We need to place expr_values columns into global_idxs columns
        # We can construct COO matrix then convert to CSR
        
        # Rows: repeat 0..n_cells for each mapped gene
        rows = np.repeat(np.arange(n_cells), len(global_idxs))
        # Cols: tile global_idxs for each cell
        cols = np.tile(global_idxs, n_cells)
        # Data: flatten the expression values (cells x mapped_genes)
        data = expr_values.flatten()
        
        global_expr = sparse.coo_matrix(
            (data, (rows, cols)), 
            shape=(n_cells, self.n_global_genes)
        ).tocsr()
        
        # Construct mask matrix (all 1s where we have data)
        mask_data = np.ones_like(data)
        mask = sparse.coo_matrix(
            (mask_data, (rows, cols)),
            shape=(n_cells, self.n_global_genes)
        ).tocsr()
        
        return global_expr, mask, unmapped_genes
