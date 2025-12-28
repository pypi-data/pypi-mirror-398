import torch
import triton
from ..kernels.alif import alif_fwd_kernel, alif_bwd_kernel

class ALIFSubFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x_seq, v_init, a_init, decay_v, decay_a, threshold, beta, alpha):
        """
        Forward pass of the ALIF function.
        """
        x_seq, v_init, a_init = x_seq.contiguous(), v_init.contiguous(), a_init.contiguous()
        n_steps, n_neurons = x_seq.shape
        
        out_spikes = torch.empty_like(x_seq)
        
        n_int32 = (n_steps + 31) // 32
        out_spikes_packed = torch.empty((n_int32, n_neurons), device=x_seq.device, dtype=torch.int32)
        
        v_seq = torch.empty_like(x_seq)
        a_seq = torch.empty_like(x_seq)
        v_final = torch.empty_like(v_init)
        a_final = torch.empty_like(a_init)
        
        grid = (triton.cdiv(n_neurons, 1024),)
        alif_fwd_kernel[grid](
            x_seq, v_init, a_init, 
            out_spikes, out_spikes_packed, v_seq, v_final, a_seq, a_final,
            n_neurons, n_steps, decay_v.item(), decay_a.item(), threshold.item(), beta.item(), 
            BLOCK_SIZE=1024
        )
        
        ctx.save_for_backward(out_spikes_packed, v_seq, a_seq, v_init, a_init, decay_v, decay_a, threshold, beta, alpha)
        ctx.mark_non_differentiable(v_seq)
        ctx.mark_non_differentiable(a_seq)
        return out_spikes, v_final, a_final, v_seq, a_seq

    @staticmethod
    def backward(ctx, grad_spikes, grad_v_final, grad_a_final, grad_v_seq, grad_a_seq):
        """
        Backward pass of the ALIF function.
        """
        out_spikes_packed, v_seq, a_seq, v_init, a_init, decay_v, decay_a, threshold, beta, alpha = ctx.saved_tensors
        n_steps, n_neurons = v_seq.shape
        
        grad_x = torch.empty_like(v_seq)
        
        grad_decay_v = torch.zeros(1, device=grad_spikes.device, dtype=torch.float32)
        grad_decay_a = torch.zeros(1, device=grad_spikes.device, dtype=torch.float32)
        grad_threshold = torch.zeros(1, device=grad_spikes.device, dtype=torch.float32)
        grad_beta = torch.zeros(1, device=grad_spikes.device, dtype=torch.float32)
        grad_alpha = torch.zeros(1, device=grad_spikes.device, dtype=torch.float32)
        
        if grad_v_final is None:
            grad_v_final = torch.zeros_like(v_init)
        if grad_a_final is None:
            grad_a_final = torch.zeros_like(a_init)
            
        grid = (triton.cdiv(n_neurons, 1024),)
        
        alif_bwd_kernel[grid](
            grad_spikes.contiguous(), out_spikes_packed, 
            v_seq.contiguous(), a_seq.contiguous(),
            grad_x, 
            grad_v_final.contiguous(), grad_a_final.contiguous(),
            v_init.contiguous(), a_init.contiguous(),
            n_neurons, n_steps, 
            decay_v, decay_a, threshold, beta, alpha,
            grad_decay_v, grad_decay_a, grad_threshold, grad_beta, grad_alpha,
            BLOCK_SIZE=1024
        )
        
        return grad_x, grad_v_final, grad_a_final, grad_decay_v, grad_decay_a, grad_threshold, grad_beta, grad_alpha
