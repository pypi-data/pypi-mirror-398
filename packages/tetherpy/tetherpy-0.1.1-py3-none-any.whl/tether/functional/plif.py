import torch
import triton
from ..kernels.plif import plif_fwd_kernel, plif_bwd_kernel

class PLIFSubFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x_seq, v_init, decay, threshold, alpha, surrogate_type):
        """
        Forward pass of the PLIF function with vector-valued parameters.

        Parameters
        ----------
        ctx : context
            Context object for saving tensors for backward pass.
        x_seq : torch.Tensor
            Input spike/current sequence. Shape: (n_steps, batch_size * n_neurons) or (n_steps, n_total_neurons).
        v_init : torch.Tensor
            Initial membrane potentials. Shape: (n_total_neurons,).
        decay : torch.Tensor
            Decay factor vector. Shape: (n_total_neurons,).
        threshold : torch.Tensor
            Threshold vector. Shape: (n_total_neurons,).
        alpha : torch.Tensor
            Surrogate gradient scaling parameter (scalar).
        surrogate_type : int
            Integer ID representing the surrogate gradient function (0: Arctan, 1: Sigmoid, 2: FastSigmoid).

        Returns
        -------
        tuple
            - spikes (torch.Tensor): Output spike sequence. Shape same as x_seq.
            - v_final (torch.Tensor): Final membrane potentials. Shape same as v_init.
            - v_seq (torch.Tensor): Membrane potential sequence. Shape same as x_seq.
        """
        x_seq, v_init = x_seq.contiguous(), v_init.contiguous()
        decay, threshold = decay.contiguous(), threshold.contiguous()
        
        n_steps, n_neurons = x_seq.shape
        
        out_spikes = torch.empty_like(x_seq)
        n_int32 = (n_steps + 31) // 32
        out_spikes_packed = torch.empty((n_int32, n_neurons), device=x_seq.device, dtype=torch.int32)
        
        v_seq = torch.empty_like(x_seq)
        v_final = torch.empty_like(v_init)
        
        grid = (triton.cdiv(n_neurons, 1024),)
        plif_fwd_kernel[grid](
            x_seq, v_init, out_spikes, out_spikes_packed, v_seq, v_final, 
            n_neurons, n_steps, decay, threshold, 
            BLOCK_SIZE=1024
        )
        
        ctx.save_for_backward(out_spikes_packed, v_seq, v_init, decay, threshold, alpha)
        ctx.surrogate_type = surrogate_type
        ctx.mark_non_differentiable(v_seq)
        return out_spikes, v_final, v_seq

    @staticmethod
    def backward(ctx, grad_spikes, grad_v_final, grad_v_seq):
        """
        Backward pass of the PLIF function.

        Computes gradients for inputs and parameters (decay, threshold, alpha) using 
        the fused Triton backward kernel.

        Parameters
        ----------
        ctx : context
            Context object with saved tensors.
        grad_spikes : torch.Tensor
            Gradient of loss w.r.t. output spikes.
        grad_v_final : torch.Tensor
            Gradient of loss w.r.t. final membrane potential.
        grad_v_seq : torch.Tensor
            Gradient of loss w.r.t. membrane potential sequence (usually None or unused).

        Returns
        -------
        tuple
            Gradients w.r.t. (x_seq, v_init, decay, threshold, alpha, surrogate_type).
            Note: surrogate_type gradient is None.
        """
        out_spikes_packed, v_seq, v_init, decay, threshold, alpha = ctx.saved_tensors
        surrogate_type = ctx.surrogate_type
        n_steps, n_neurons = v_seq.shape
        
        grad_x = torch.empty_like(v_seq)
        
        # Gradients for parameters (Vectors)
        grad_decay = torch.zeros_like(decay)
        grad_threshold = torch.zeros_like(threshold)
        grad_alpha = torch.zeros(1, device=grad_spikes.device, dtype=torch.float32)
        
        if grad_v_final is None:
            grad_v_final = torch.zeros_like(v_init)
        
        grid = (triton.cdiv(n_neurons, 1024),)
        
        plif_bwd_kernel[grid](
            grad_spikes.contiguous(), out_spikes_packed, 
            v_seq.contiguous(), grad_x, 
            grad_v_final.contiguous(), v_init.contiguous(),
            n_neurons, n_steps, decay, threshold, alpha,
            grad_decay, grad_threshold, grad_alpha,
            surrogate_type,
            BLOCK_SIZE=1024
        )
        
        return grad_x, grad_v_final, grad_decay, grad_threshold, grad_alpha, None
