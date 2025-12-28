import torch
import triton
import time
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tether.functional.lif import LIFSubFunction
from tether.functional.plif import PLIFSubFunction

def benchmark_plif():
    """
    Benchmark LIF vs PLIF (Triton vs Triton).
    """
    if not torch.cuda.is_available():
        print("Skipping benchmark on CPU.")
        return

    device = torch.device("cuda")
    print(f"Benchmarking LIF vs PLIF on {torch.cuda.get_device_name(0)}")

    batch_size = 32
    seq_len = 2048
    dim = 768
    n_neurons = batch_size * dim
    
    x_seq = torch.randn(seq_len, n_neurons, device=device)
    v_init = torch.zeros(n_neurons, device=device)
    
    # LIF Params (Scalar)
    decay_scalar = torch.tensor(0.9, device=device)
    threshold_scalar = torch.tensor(1.0, device=device)
    alpha = torch.tensor(2.0, device=device)
    
    # PLIF Params (Vector)
    decay_vector = torch.full((n_neurons,), 0.9, device=device)
    threshold_vector = torch.full((n_neurons,), 1.0, device=device)

    # Warmup
    print("Warming up...")
    for _ in range(10):
        with torch.no_grad():
            LIFSubFunction.apply(x_seq, v_init, decay_scalar, threshold_scalar, alpha, 0)
            PLIFSubFunction.apply(x_seq, v_init, decay_vector, threshold_vector, alpha, 0)
    
    # Benchmark LIF
    torch.cuda.synchronize()
    start_time = time.time()
    iterations = 50
    with torch.no_grad():
        for _ in range(iterations):
            LIFSubFunction.apply(x_seq, v_init, decay_scalar, threshold_scalar, alpha, 0)
    torch.cuda.synchronize()
    lif_time = (time.time() - start_time) / iterations
    print(f"LIF Time:  {lif_time * 1000:.3f} ms")

    # Benchmark PLIF
    torch.cuda.synchronize()
    start_time = time.time()
    with torch.no_grad():
        for _ in range(iterations):
            PLIFSubFunction.apply(x_seq, v_init, decay_vector, threshold_vector, alpha, 0)
    torch.cuda.synchronize()
    plif_time = (time.time() - start_time) / iterations
    print(f"PLIF Time: {plif_time * 1000:.3f} ms")
    
    print(f"Overhead: {plif_time / lif_time:.2f}x slower")

if __name__ == "__main__":
    benchmark_plif()
