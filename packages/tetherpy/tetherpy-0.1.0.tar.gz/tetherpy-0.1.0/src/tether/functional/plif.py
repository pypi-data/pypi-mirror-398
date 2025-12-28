import torch
import triton
from ..kernels.plif import plif_fwd_kernel, plif_bwd_kernel

class PLIFSubFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x_seq, v_init, decay, threshold, alpha, surrogate_type):
        """
        Forward pass of the PLIF function.
        Decay and Threshold are vectors (n_neurons,).
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
