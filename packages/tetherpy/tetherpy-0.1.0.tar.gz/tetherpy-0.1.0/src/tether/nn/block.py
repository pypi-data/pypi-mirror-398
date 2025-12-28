import torch.nn as nn
from .attention import SpikingSelfAttention
from .lif import LIF
import torch

class SpikingTransformerBlock(nn.Module):
    def __init__(self, dim, num_heads=8, mlp_ratio=4):
        """
        Initialize the SpikingTransformerBlock.

        Parameters
        ----------
        dim : int
            Model dimension.
        num_heads : int, optional
            Number of attention heads (default is 8).
        mlp_ratio : int, optional
            MLP expansion ratio (default is 4).
        """
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = SpikingSelfAttention(dim, num_heads)
        self.norm2 = nn.LayerNorm(dim)
        
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * mlp_ratio),
            LIF(dim * mlp_ratio),
            nn.Linear(dim * mlp_ratio, dim)
        )
        
        # ADDED: A learnable scaling factor to bridge the gap between Norm and Spiking
        self.scale = nn.Parameter(torch.tensor(0.5))

    def forward(self, x):
        """
        Forward pass of the SpikingTransformerBlock.

        Parameters
        ----------
        x : torch.Tensor
            Input tensor.

        Returns
        -------
        torch.Tensor
            Output tensor.
        """
        # We multiply the normalized output by a scaling factor 
        # to ensure it hits the threshold range naturally.
        x = x + self.attn(self.norm1(x) * self.scale)
        x = x + self.mlp(self.norm2(x) * self.scale)
        return x