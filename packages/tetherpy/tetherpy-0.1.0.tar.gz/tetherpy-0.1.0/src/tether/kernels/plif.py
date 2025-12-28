import triton
import triton.language as tl
import torch

@triton.jit
def plif_fwd_kernel(
    X_ptr, V_init_ptr, S_out_ptr, S_packed_ptr, V_seq_ptr, V_final_ptr, 
    n_neurons, n_steps, decay_ptr, threshold_ptr, 
    BLOCK_SIZE: tl.constexpr
):
    """
    Triton kernel for PLIF forward pass (Vector Parameters).
    """
    pid = tl.program_id(0)
    offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_neurons

    v = tl.load(V_init_ptr + offsets, mask=mask)
    
    # Load vector parameters
    decay = tl.load(decay_ptr + offsets, mask=mask)
    threshold = tl.load(threshold_ptr + offsets, mask=mask)
    
    packed_spikes = tl.zeros([BLOCK_SIZE], dtype=tl.int32)
    
    for t in range(n_steps):
        x = tl.load(X_ptr + t * n_neurons + offsets, mask=mask)
        v = v * decay + x
        
        tl.store(V_seq_ptr + t * n_neurons + offsets, v, mask=mask)
        
        spike_bool = v >= threshold
        spike_float = spike_bool.to(tl.float32)
        
        tl.store(S_out_ptr + t * n_neurons + offsets, spike_float, mask=mask)
        
        bit_idx = t % 32
        bit_val = (1 << bit_idx)
        added_bit = tl.where(spike_bool, bit_val, 0)
        packed_spikes = packed_spikes | added_bit
        
        if bit_idx == 31:
            block_idx = t // 32
            tl.store(S_packed_ptr + block_idx * n_neurons + offsets, packed_spikes, mask=mask)
            packed_spikes = tl.zeros([BLOCK_SIZE], dtype=tl.int32)
        
        v = tl.where(spike_bool, 0.0, v)
        
    tl.store(V_final_ptr + offsets, v, mask=mask)
    
    if (n_steps % 32) != 0:
        block_idx = n_steps // 32
        tl.store(S_packed_ptr + block_idx * n_neurons + offsets, packed_spikes, mask=mask)

@triton.jit
def plif_bwd_kernel(
    GRAD_OUT_ptr, S_packed_ptr, V_seq_ptr, GRAD_X_ptr, 
    GRAD_V_FINAL_ptr, V_init_ptr,
    n_neurons, n_steps, decay_ptr, threshold_ptr, alpha_ptr,
    GRAD_DECAY_ptr, GRAD_THRESHOLD_ptr, GRAD_ALPHA_ptr,
    surrogate_type,
    BLOCK_SIZE: tl.constexpr
):
    """
    Triton kernel for PLIF backward pass (Vector Parameters).
    """
    pid = tl.program_id(0)
    offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_neurons

    alpha = tl.load(alpha_ptr) # Alpha remains scalar usually, or shared
    # Vector parameters
    decay = tl.load(decay_ptr + offsets, mask=mask)
    threshold = tl.load(threshold_ptr + offsets, mask=mask)
    
    grad_v = tl.load(GRAD_V_FINAL_ptr + offsets, mask=mask)

    # Accumulators for vector gradients
    d_decay = tl.zeros([BLOCK_SIZE], dtype=tl.float32)
    d_threshold = tl.zeros([BLOCK_SIZE], dtype=tl.float32)
    d_alpha_local = tl.zeros([BLOCK_SIZE], dtype=tl.float32)
    
    current_packed = tl.zeros([BLOCK_SIZE], dtype=tl.int32)

    for t in range(n_steps - 1, -1, -1):
        bit_idx = t % 32
        
        if t == n_steps - 1 or bit_idx == 31:
             block_idx = t // 32
             current_packed = tl.load(S_packed_ptr + block_idx * n_neurons + offsets, mask=mask)

        spike_int = (current_packed >> bit_idx) & 1
        spike = spike_int.to(tl.float32)
        
        grad_out = tl.load(GRAD_OUT_ptr + t * n_neurons + offsets, mask=mask)
        v = tl.load(V_seq_ptr + t * n_neurons + offsets, mask=mask)
        
        if surrogate_type == 1: # Sigmoid
            val = alpha * (v - threshold)
            sig = 1.0 / (1.0 + tl.exp(-val))
            surrogate = alpha * sig * (1.0 - sig)
        elif surrogate_type == 2: # FastSigmoid
            val = tl.abs(alpha * (v - threshold))
            denom = 1.0 + val
            surrogate = 1.0 / (denom * denom)
        else: # Arctan
            pi = 3.14159265359
            diff = alpha * pi * (v - threshold)
            denom = 1.0 + diff * diff
            surrogate = alpha / denom
        
        d_threshold -= grad_out * surrogate
        d_alpha_local += grad_out * (v - threshold) * surrogate / alpha

        grad_v = grad_out * surrogate + grad_v * decay * (1.0 - spike)
        
        tl.store(GRAD_X_ptr + t * n_neurons + offsets, grad_v, mask=mask)

        if t > 0:
            v_prev = tl.load(V_seq_ptr + (t - 1) * n_neurons + offsets, mask=mask)
            
            if bit_idx > 0:
                 s_prev_int = (current_packed >> (bit_idx - 1)) & 1
                 s_prev = s_prev_int.to(tl.float32)
            else:
                 prev_packed = tl.load(S_packed_ptr + (t // 32 - 1) * n_neurons + offsets, mask=mask)
                 s_prev_int = (prev_packed >> 31) & 1
                 s_prev = s_prev_int.to(tl.float32)
            
            v_prev_post = v_prev * (1.0 - s_prev)
            d_decay += grad_v * v_prev_post
        else:
            v_prev_post = tl.load(V_init_ptr + offsets, mask=mask)
            d_decay += grad_v * v_prev_post

    # Store vector gradients
    tl.store(GRAD_DECAY_ptr + offsets, d_decay, mask=mask)
    tl.store(GRAD_THRESHOLD_ptr + offsets, d_threshold, mask=mask)
    
    # Reduce alpha gradient (scalar)
    tl.atomic_add(GRAD_ALPHA_ptr, tl.sum(d_alpha_local))
