import torch
import torch.nn as nn
from ..functional.lif import LIFSubFunction
from .surrogates import Surrogate, Arctan

class LIF(nn.Module):
    def __init__(self, n_neurons, decay=0.9, threshold=1.0, alpha=2.0, surrogate: Surrogate = None, store_traces=False):
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
        surrogate : Surrogate, optional
            Surrogate gradient module. If None, uses Arctan with specified alpha.
        store_traces : bool, optional
            Whether to store the membrane potential trace (default is False).
        """
        super().__init__()
        self.n_neurons = n_neurons
        self.decay = nn.Parameter(torch.tensor(decay))
        self.threshold = nn.Parameter(torch.tensor(threshold))
        
        if surrogate is None:
            self.surrogate = Arctan(alpha=alpha, trainable=True)
        else:
            self.surrogate = surrogate
            
        self.store_traces = store_traces
        self.register_buffer("v", torch.zeros(n_neurons))
        self.v_seq = None
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

        spikes, v_next, v_seq = LIFSubFunction.apply(
            x_flat, self.v, self.decay, self.threshold, self.surrogate.alpha, self.surrogate.get_id()
        )
        
        if self.store_traces:
            self.v_seq = v_seq.detach().reshape(orig_shape)
        else:
            self.v_seq = None
        
        # Calculate and store firing rate for logging
        # spikes: (Time, Batch * Features)
        self.firing_rate = spikes.mean().item()
        
        self.v = v_next.detach()
        return spikes.reshape(orig_shape)

    @property
    def alpha(self):
        return self.surrogate.alpha