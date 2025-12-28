import torch
import triton
from ..kernels.lif import lif_fwd_kernel, lif_bwd_kernel

class LIFSubFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x_seq, v_init, decay, threshold, alpha, surrogate_type):
        """
        Forward pass of the LIF function.

        Parameters
        ----------
        ctx : context
            Context for saving tensors.
        x_seq : torch.Tensor
            Input sequence of shape (n_steps, n_neurons).
        v_init : torch.Tensor
            Initial membrane potentials of shape (n_neurons,).
        decay : torch.Tensor
            Decay factor.
        threshold : torch.Tensor
            Spiking threshold.
        alpha : torch.Tensor
            Surrogate gradient parameter.
        surrogate_type : int
            Type of surrogate gradient.

        Returns
        -------
        tuple
            Spikes and final membrane potentials.
        """
        x_seq, v_init = x_seq.contiguous(), v_init.contiguous()
        n_steps, n_neurons = x_seq.shape
        
        out_spikes = torch.empty_like(x_seq)
        
        # Bit-packing: 32 spikes per int32
        n_int32 = (n_steps + 31) // 32
        out_spikes_packed = torch.empty((n_int32, n_neurons), device=x_seq.device, dtype=torch.int32)
        
        v_seq = torch.empty_like(x_seq) # Store membrane potentials for backward
        v_final = torch.empty_like(v_init)
        
        grid = (triton.cdiv(n_neurons, 1024),)
        lif_fwd_kernel[grid](
            x_seq, v_init, out_spikes, out_spikes_packed, v_seq, v_final, 
            n_neurons, n_steps, decay.item(), threshold.item(), 
            BLOCK_SIZE=1024
        )
        
        # Save packed spikes for backward to save memory
        ctx.save_for_backward(out_spikes_packed, v_seq, v_init, decay, threshold, alpha)
        ctx.surrogate_type = surrogate_type
        ctx.mark_non_differentiable(v_seq)
        return out_spikes, v_final, v_seq

    @staticmethod
    def backward(ctx, grad_spikes, grad_v_final, grad_v_seq):
        """
        Backward pass of the LIF function.

        Parameters
        ----------
        ctx : context
            Context with saved tensors.
        grad_spikes : torch.Tensor
            Gradients w.r.t. spikes.
        grad_v_final : torch.Tensor
            Gradients w.r.t. final membrane potentials.
        grad_v_seq : torch.Tensor
            Gradients w.r.t. voltage sequence.

        Returns
        -------
        tuple
            Gradients w.r.t. inputs and parameters.
        """
        out_spikes_packed, v_seq, v_init, decay, threshold, alpha = ctx.saved_tensors
        surrogate_type = ctx.surrogate_type
        n_steps, n_neurons = v_seq.shape
        
        grad_x = torch.empty_like(v_seq)
        
        # Gradients for parameters
        grad_decay = torch.zeros(1, device=grad_spikes.device, dtype=torch.float32)
        grad_threshold = torch.zeros(1, device=grad_spikes.device, dtype=torch.float32)
        grad_alpha = torch.zeros(1, device=grad_spikes.device, dtype=torch.float32)
        
        if grad_v_final is None:
            grad_v_final = torch.zeros_like(v_init)
        
        grid = (triton.cdiv(n_neurons, 1024),)
        
        lif_bwd_kernel[grid](
            grad_spikes.contiguous(), out_spikes_packed, 
            v_seq.contiguous(), grad_x, 
            grad_v_final.contiguous(), v_init.contiguous(),
            n_neurons, n_steps, decay, threshold, alpha,
            grad_decay, grad_threshold, grad_alpha,
            surrogate_type,
            BLOCK_SIZE=1024
        )
        
        # Returns grads for (x_seq, v_init, decay, threshold, alpha, surrogate_type)
        return grad_x, grad_v_final, grad_decay, grad_threshold, grad_alpha, None
