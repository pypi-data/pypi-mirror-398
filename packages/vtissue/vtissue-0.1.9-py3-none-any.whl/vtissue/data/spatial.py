import torch
import numpy as np
from typing import Optional, Tuple

class SpatialEncoder:
    """
    Handles spatial coordinate transformations and encoding.
    """
    def __init__(self, mpp: float = 0.5, n_fourier_freqs: int = 10):
        """
        Args:
            mpp: Microns per pixel.
            n_fourier_freqs: Number of frequency bands for positional encoding.
        """
        self.mpp = mpp
        self.n_fourier_freqs = n_fourier_freqs
        
    def normalize_coords(self, coords: np.ndarray, min_vals: Optional[np.ndarray] = None, max_vals: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert pixel coordinates to normalized micron coordinates.
        
        Args:
            coords: (N, 2) array of [x, y] in pixels.
            
        Returns:
            norm_coords: (N, 2) array in [0, 1] range.
            micron_coords: (N, 2) array in microns.
        """
        # Convert to microns
        micron_coords = coords * self.mpp
        if min_vals is None or max_vals is None:
            min_vals = micron_coords.min(axis=0)
            max_vals = micron_coords.max(axis=0)
        range_vals = max_vals - min_vals
        
        # Avoid division by zero
        range_vals[range_vals == 0] = 1.0
        
        norm_coords = (micron_coords - min_vals) / range_vals
        
        return norm_coords, micron_coords
    
    def compute_fourier_features(self, norm_coords: torch.Tensor) -> torch.Tensor:
        """
        Compute Fourier positional encodings.
        
        Args:
            norm_coords: (N, 2) tensor in [0, 1].
            
        Returns:
            encodings: (N, 4 * n_fourier_freqs) tensor.
        """
        if int(self.n_fourier_freqs) <= 0:
            return torch.zeros((norm_coords.size(0), 0), dtype=norm_coords.dtype, device=norm_coords.device)
        # norm_coords is (N, 2) -> x, y
        x = norm_coords[:, 0]
        y = norm_coords[:, 1]
        
        encodings = []
        for i in range(self.n_fourier_freqs):
            freq = 2.0 ** i
            # Sin/Cos for X
            encodings.append(torch.sin(freq * np.pi * x))
            encodings.append(torch.cos(freq * np.pi * x))
            # Sin/Cos for Y
            encodings.append(torch.sin(freq * np.pi * y))
            encodings.append(torch.cos(freq * np.pi * y))
        
        return torch.stack(encodings, dim=-1)
