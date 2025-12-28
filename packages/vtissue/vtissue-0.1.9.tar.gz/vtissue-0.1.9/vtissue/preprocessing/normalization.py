import numpy as np
import pandas as pd
from typing import Optional, List

def normalize_expression(adata, method: str = 'arcsinh', cofactor: float = 5.0):
    """
    Normalize expression data in adata.X.
    
    Args:
        adata: AnnData object.
        method: Normalization method ('arcsinh', 'log1p', 'zscore').
        cofactor: Cofactor for arcsinh normalization.
    """
    if method == 'arcsinh':
        # arcsinh(x / cofactor)
        adata.X = np.arcsinh(adata.X / cofactor)
    elif method == 'log1p':
        # log(X + 1)
        if hasattr(adata.X, 'log1p'):
             # Sparse matrix often has this method or use np.log1p which handles it
             adata.X = adata.X.log1p()
        else:
             adata.X = np.log1p(adata.X)
    elif method == 'zscore':
        # (X - mean) / std
        if hasattr(adata.X, 'toarray'):
            X = adata.X.toarray()
        else:
            X = adata.X
        
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0)
        # Handle zero std
        std[std == 0] = 1.0
        
        adata.X = (X - mean) / std
    else:
        raise ValueError(f"Unknown normalization method: {method}")
        
    return adata

def standardize_metadata(
    adata, 
    required_cols: Optional[List[str]] = None,
    defaults: Optional[dict] = None
):
    """
    Ensure standard metadata columns exist and handle missing values.
    
    Args:
        adata: AnnData object.
        required_cols: List of columns that must exist.
        defaults: Dictionary of default values for missing columns.
    """
    if required_cols is None:
        required_cols = ['phenotype', 'sample_type', 'imageid']
        
    if defaults is None:
        defaults = {
            'phenotype': 'No_label',
            'sample_type': 'Unknown',
            'disease': 'Unknown'
        }
        
    for col in required_cols:
        if col not in adata.obs.columns:
            if col in defaults:
                adata.obs[col] = defaults[col]
            else:
                # If required but no default, maybe raise error or fill NA
                adata.obs[col] = np.nan
                
    # Specific handling for phenotype
    if 'phenotype' in adata.obs.columns:
        s = adata.obs['phenotype']
        s = s.astype(str)
        adata.obs['phenotype'] = s.replace({'nan': 'No_label'}).fillna('No_label')
        
    # Ensure imageid is string
    if 'imageid' in adata.obs.columns:
        adata.obs['imageid'] = adata.obs['imageid'].astype(str)
        
    return adata
