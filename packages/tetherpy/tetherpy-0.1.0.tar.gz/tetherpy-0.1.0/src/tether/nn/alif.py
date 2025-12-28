
import torch
import torch.nn as nn
from ..functional.alif import ALIFSubFunction

class ALIF(nn.Module):
    def __init__(self, n_neurons, decay_v=0.9, decay_a=0.9, threshold=1.0, beta=0.5, alpha=2.0, store_traces=False):
        """
        Initialize the ALIF module.

        Parameters
        ----------
        n_neurons : int
            Number of neurons.
        decay_v : float, optional
            Membrane potential decay factor (default is 0.9).
        decay_a : float, optional
            Adaptation variable decay factor (default is 0.9).
        threshold : float, optional
            Base spiking threshold (default is 1.0).
        beta : float, optional
            Adaptation strength (default is 0.5).
        alpha : float, optional
            Surrogate gradient parameter (default is 2.0).
        store_traces : bool, optional
            Whether to store the membrane potential and adaptation traces (default is False).
        """
        super().__init__()
        self.n_neurons = n_neurons
        self.decay_v = nn.Parameter(torch.tensor(decay_v))
        self.decay_a = nn.Parameter(torch.tensor(decay_a))
        self.threshold = nn.Parameter(torch.tensor(threshold))
        self.beta = nn.Parameter(torch.tensor(beta))
        self.alpha = nn.Parameter(torch.tensor(alpha))
        self.store_traces = store_traces
        
        self.register_buffer("v", torch.zeros(n_neurons))
        self.register_buffer("a", torch.zeros(n_neurons))
        
        self.v_seq = None
        self.a_seq = None
        self.firing_rate = 0.0

    def forward(self, x_seq):
        """
        Forward pass of the ALIF module.

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
            self.a = torch.zeros(x_flat.shape[1], device=x_seq.device)

        spikes, v_next, a_next, v_seq, a_seq = ALIFSubFunction.apply(
            x_flat, self.v, self.a, self.decay_v, self.decay_a, self.threshold, self.beta, self.alpha
        )
        
        if self.store_traces:
            self.v_seq = v_seq.detach().reshape(orig_shape)
            self.a_seq = a_seq.detach().reshape(orig_shape)
        else:
            self.v_seq = None
            self.a_seq = None
        
        self.firing_rate = spikes.mean().item()
        
        self.v = v_next.detach()
        self.a = a_next.detach()
        return spikes.reshape(orig_shape)
