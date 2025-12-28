import torch
import torch.nn as nn
from ..functional.lif import LIFSubFunction

class LIF(nn.Module):
    def __init__(self, n_neurons, decay=0.9, threshold=1.0, alpha=2.0):
        """
        Initialize the LIF module.

        Parameters
        ----------
        n_neurons : int
            Number of neurons.
        decay : float, optional
            Decay factor (default is 0.9).
        threshold : float, optional
            Spiking threshold (default is 1.0).
        alpha : float, optional
            Surrogate gradient parameter (default is 2.0).
        """
        super().__init__()
        self.n_neurons = n_neurons
        self.decay = nn.Parameter(torch.tensor(decay))
        self.threshold = nn.Parameter(torch.tensor(threshold))
        self.alpha = nn.Parameter(torch.tensor(alpha))
        self.register_buffer("v", torch.zeros(n_neurons))
        self.firing_rate = 0.0

    def forward(self, x_seq):
        """
        Forward pass of the LIF module.

        Parameters
        ----------
        x_seq : torch.Tensor
            Input sequence.

        Returns
        -------
        torch.Tensor
            Output spikes with the same shape as input.
        """
        orig_shape = x_seq.shape
        # Flatten all but Time dimension: (Time, Batch * Features)
        x_flat = x_seq.reshape(orig_shape[0], -1)
        
        if self.v.shape[0] != x_flat.shape[1]:
            self.v = torch.zeros(x_flat.shape[1], device=x_seq.device)

        spikes, v_next = LIFSubFunction.apply(x_flat, self.v, self.decay, self.threshold, self.alpha)
        
        # Calculate and store firing rate for logging
        # spikes: (Time, Batch * Features)
        self.firing_rate = spikes.mean().item()
        
        self.v = v_next.detach()
        return spikes.reshape(orig_shape)