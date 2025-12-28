import torch
import triton
import time
import sys
import os

# Add src to path so we can import tether
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tether.functional.lif import LIFSubFunction

def lif_pytorch(x_seq, v_init, decay, threshold):
    """
    PyTorch reference implementation of LIF.

    Parameters
    ----------
    x_seq : torch.Tensor
        Input sequence of shape (Time, Neurons).
    v_init : torch.Tensor
        Initial membrane potentials of shape (Neurons,).
    decay : float
        Decay factor.
    threshold : float
        Spiking threshold.

    Returns
    -------
    torch.Tensor
        Output spikes of shape (Time, Neurons).
    """
    # x_seq: (Time, Neurons)
    # v_init: (Neurons)
    
    n_steps, n_neurons = x_seq.shape
    v = v_init.clone()
    spikes_list = []
    
    # We use a simple loop as LIF is recurrent
    # This simulates "Vanilla PyTorch" without custom CUDA kernels or JIT
    for t in range(n_steps):
        x = x_seq[t]
        v = v * decay + x
        
        spike = (v >= threshold).float()
        spikes_list.append(spike)
        
        # Hard reset
        v = v * (1.0 - spike)
        
    return torch.stack(spikes_list)

def benchmark():
    """
    Benchmark PyTorch vs Triton implementations of LIF.
    """
    if not torch.cuda.is_available():
        print("Skipping benchmark on CPU (Triton requires CUDA).")
        return

    device = torch.device("cuda")
    print(f"Benchmarking on {torch.cuda.get_device_name(0)}")

    # Dimensions
    # Simulating a reasonable layer size for a Transformer
    batch_size = 32
    seq_len = 2048 # Longer context to emphasize the loop overhead vs kernel
    dim = 768      # Standard BERT-base dimension
    n_neurons = batch_size * dim
    
    # Inputs
    x_seq = torch.randn(seq_len, n_neurons, device=device)
    v_init = torch.zeros(n_neurons, device=device)
    decay = torch.tensor(0.9, device=device)
    threshold = torch.tensor(1.0, device=device)
    alpha = torch.tensor(2.0, device=device)

    # Warmup
    print("Warming up...")
    for _ in range(10):
        with torch.no_grad():
            _ = lif_pytorch(x_seq, v_init, decay, threshold)
            LIFSubFunction.apply(x_seq, v_init, decay, threshold, alpha, 0)
    
    # Benchmark PyTorch
    torch.cuda.synchronize()
    start_time = time.time()
    iterations = 50
    with torch.no_grad():
        for _ in range(iterations):
            _ = lif_pytorch(x_seq, v_init, decay, threshold)
    torch.cuda.synchronize()
    pytorch_time = (time.time() - start_time) / iterations
    print(f"PyTorch Time: {pytorch_time * 1000:.3f} ms")

    # Benchmark Triton
    torch.cuda.synchronize()
    start_time = time.time()
    with torch.no_grad():
        for _ in range(iterations):
            # Note: We use apply but inside no_grad, so it just runs forward
            LIFSubFunction.apply(x_seq, v_init, decay, threshold, alpha, 0)
    torch.cuda.synchronize()
    triton_time = (time.time() - start_time) / iterations
    print(f"Triton Time:  {triton_time * 1000:.3f} ms")
    
    print(f"Speedup: {pytorch_time / triton_time:.2f}x")

if __name__ == "__main__":
    benchmark()
