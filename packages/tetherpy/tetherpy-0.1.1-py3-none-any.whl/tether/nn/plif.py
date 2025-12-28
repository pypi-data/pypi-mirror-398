import torch
import torch.nn as nn
from ..functional.plif import PLIFSubFunction
from .surrogates import Surrogate, Arctan

class PLIF(nn.Module):
    def __init__(self, n_neurons, init_decay=0.9, init_threshold=1.0, alpha=2.0, surrogate: Surrogate = None, store_traces=False):
        """
        Initialize the Parametric LIF (PLIF) module.
        Decay and Threshold are learnable vectors per neuron.

        Parameters
        ----------
        n_neurons : int
            Number of neurons.
        init_decay : float, optional
            Initial decay factor (default is 0.9).
        init_threshold : float, optional
            Initial spiking threshold (default is 1.0).
        alpha : float, optional
            Surrogate gradient parameter (default is 2.0).
        surrogate : Surrogate, optional
            Surrogate gradient module. If None, uses Arctan.
        store_traces : bool, optional
            Whether to store the membrane potential trace.
        """
        super().__init__()
        self.n_neurons = n_neurons
        
        # Learnable vector parameters
        self.decay = nn.Parameter(torch.full((n_neurons,), init_decay))
        self.threshold = nn.Parameter(torch.full((n_neurons,), init_threshold))
        
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
        Forward pass of the PLIF module.

        Parameters
        ----------
        x_seq : torch.Tensor
            Input sequence of shape (Time, Batch, Neurons) or (Time, Batch * Neurons).

        Returns
        -------
        torch.Tensor
            Output spikes with the same shape as input.
        """
        orig_shape = x_seq.shape
        x_flat = x_seq.reshape(orig_shape[0], -1)
        
        if self.v.shape[0] != x_flat.shape[1]:
            self.v = torch.zeros(x_flat.shape[1], device=x_seq.device)

        spikes, v_next, v_seq = PLIFSubFunction.apply(
            x_flat, self.v, self.decay, self.threshold, self.surrogate.alpha, self.surrogate.get_id()
        )
        
        if self.store_traces:
            self.v_seq = v_seq.detach().reshape(orig_shape)
        else:
            self.v_seq = None
        
        self.firing_rate = spikes.mean().item()
        self.v = v_next.detach()
        return spikes.reshape(orig_shape)
