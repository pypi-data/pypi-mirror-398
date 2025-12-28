import triton
import triton.language as tl
import torch

@triton.jit
def lif_fwd_kernel(
    X_ptr, V_init_ptr, S_out_ptr, S_packed_ptr, V_seq_ptr, V_final_ptr, 
    n_neurons, n_steps, decay, threshold, 
    BLOCK_SIZE: tl.constexpr
):
    """
    Triton kernel for LIF forward pass.

    Parameters
    ----------
    X_ptr : pointer
        Input sequence.
    V_init_ptr : pointer
        Initial membrane potentials.
    S_out_ptr : pointer
        Output spikes.
    S_packed_ptr : pointer
        Packed spikes.
    V_seq_ptr : pointer
        Membrane potential sequence.
    V_final_ptr : pointer
        Final membrane potentials.
    n_neurons : int
        Number of neurons.
    n_steps : int
        Number of time steps.
    decay : float
        Decay factor.
    threshold : float
        Spiking threshold.
    BLOCK_SIZE : int
        Block size for Triton.
    """
    pid = tl.program_id(0)
    offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_neurons

    v = tl.load(V_init_ptr + offsets, mask=mask)
    
    # Accumulator for bit-packing
    packed_spikes = tl.zeros([BLOCK_SIZE], dtype=tl.int32)
    
    for t in range(n_steps):
        # Memory layout: [Time, Neurons]
        x = tl.load(X_ptr + t * n_neurons + offsets, mask=mask)
        v = v * decay + x
        
        # Store membrane potential BEFORE reset
        tl.store(V_seq_ptr + t * n_neurons + offsets, v, mask=mask)
        
        spike_bool = v >= threshold
        spike_float = spike_bool.to(tl.float32)
        
        tl.store(S_out_ptr + t * n_neurons + offsets, spike_float, mask=mask)
        
        # Bit Packing Logic
        bit_idx = t % 32
        bit_val = (1 << bit_idx)
        added_bit = tl.where(spike_bool, bit_val, 0)
        packed_spikes = packed_spikes | added_bit
        
        # If we just filled the last bit of an int32, store it
        if bit_idx == 31:
            block_idx = t // 32
            tl.store(S_packed_ptr + block_idx * n_neurons + offsets, packed_spikes, mask=mask)
            # Reset accumulator
            packed_spikes = tl.zeros([BLOCK_SIZE], dtype=tl.int32)
        
        # Hard reset
        v = tl.where(spike_bool, 0.0, v)
        
    tl.store(V_final_ptr + offsets, v, mask=mask)
    
    # Store remaining bits if any
    if (n_steps % 32) != 0:
        block_idx = n_steps // 32
        tl.store(S_packed_ptr + block_idx * n_neurons + offsets, packed_spikes, mask=mask)

@triton.jit

def lif_bwd_kernel(

    GRAD_OUT_ptr, S_packed_ptr, V_seq_ptr, GRAD_X_ptr, 

    GRAD_V_FINAL_ptr, V_init_ptr,

    n_neurons, n_steps, decay_ptr, threshold_ptr, alpha_ptr,

    GRAD_DECAY_ptr, GRAD_THRESHOLD_ptr, GRAD_ALPHA_ptr,

    surrogate_type,

    BLOCK_SIZE: tl.constexpr

):

    """

    Triton kernel for LIF backward pass.



    Parameters

    ----------

    GRAD_OUT_ptr : pointer

        Gradients w.r.t. output spikes.

    S_packed_ptr : pointer

        Packed spikes.

    V_seq_ptr : pointer

        Membrane potential sequence.

    GRAD_X_ptr : pointer

        Gradients w.r.t. input.

    GRAD_V_FINAL_ptr : pointer

        Gradients w.r.t. final potentials.

    V_init_ptr : pointer

        Initial potentials.

    n_neurons : int

        Number of neurons.

    n_steps : int

        Number of time steps.

    decay_ptr : pointer

        Decay parameter.

    threshold_ptr : pointer

        Threshold parameter.

    alpha_ptr : pointer

        Alpha parameter.

    GRAD_DECAY_ptr : pointer

        Gradients w.r.t. decay.

    GRAD_THRESHOLD_ptr : pointer

        Gradients w.r.t. threshold.

    GRAD_ALPHA_ptr : pointer

        Gradients w.r.t. alpha.

    surrogate_type : int

        Type of surrogate gradient (0: Arctan, 1: Sigmoid, 2: FastSigmoid).

    BLOCK_SIZE : int

        Block size for Triton.

    """

    pid = tl.program_id(0)

    offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)

    mask = offsets < n_neurons



    alpha = tl.load(alpha_ptr)

    decay = tl.load(decay_ptr)

    threshold = tl.load(threshold_ptr)

    

    grad_v = tl.load(GRAD_V_FINAL_ptr + offsets, mask=mask)



    d_decay = 0.0

    d_threshold = 0.0

    d_alpha = 0.0

    

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

        

        # Surrogate Gradient Calculation

        if surrogate_type == 1: # Sigmoid

            val = alpha * (v - threshold)

            sig = 1.0 / (1.0 + tl.exp(-val))

            surrogate = alpha * sig * (1.0 - sig)

        elif surrogate_type == 2: # FastSigmoid

            val = tl.abs(alpha * (v - threshold))

            denom = 1.0 + val

            surrogate = 1.0 / (denom * denom)

        else: # Arctan (Default)

            pi = 3.14159265359

            diff = alpha * pi * (v - threshold)

            denom = 1.0 + diff * diff

            surrogate = alpha / denom

        

        d_threshold -= tl.sum(grad_out * surrogate)

        d_alpha += tl.sum(grad_out * (v - threshold) * surrogate / alpha)



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

            d_decay += tl.sum(grad_v * v_prev_post)

        else:

            v_prev_post = tl.load(V_init_ptr + offsets, mask=mask)

            d_decay += tl.sum(grad_v * v_prev_post)



    tl.atomic_add(GRAD_DECAY_ptr, d_decay)

    tl.atomic_add(GRAD_THRESHOLD_ptr, d_threshold)

    tl.atomic_add(GRAD_ALPHA_ptr, d_alpha)
