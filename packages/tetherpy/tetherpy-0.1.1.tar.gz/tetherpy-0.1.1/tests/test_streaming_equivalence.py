import torch
import torch.nn as nn
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from train_stories import TetherLM

def test_streaming_equivalence():
    """
    Test equivalence between full forward pass and streaming pass.
    """
    torch.manual_seed(42)
    device = "cpu" # Test on CPU for simplicity, or CUDA if available
    if torch.cuda.is_available():
        device = "cuda"

    vocab_size = 100
    dim = 32
    n_layers = 2
    n_heads = 4
    seq_len = 10
    
    model = TetherLM(vocab_size, dim, n_layers, n_heads).to(device)
    model.eval()

    # Create random input
    x = torch.randint(0, vocab_size, (1, seq_len)).to(device)

    # 1. Full Forward Pass
    model.reset_states()
    with torch.no_grad():
        out_full = model(x) # (Batch, Seq, Vocab)

    # 2. Streaming Pass
    model.reset_states()
    outputs = []
    with torch.no_grad():
        for i in range(seq_len):
            x_step = x[:, i:i+1] # (Batch, 1)
            out_step = model(x_step) # (Batch, 1, Vocab)
            outputs.append(out_step)
    
    out_stream = torch.cat(outputs, dim=1)

    # Compare
    # Tolerances might be needed due to float precision, but they should be very close
    max_diff = (out_full - out_stream).abs().max()
    print(f"Max difference: {max_diff.item()}")
    
    assert torch.allclose(out_full, out_stream, atol=1e-5), f"Streaming output mismatch! Max diff: {max_diff.item()}"
    print("Test Passed: Streaming is equivalent to Batch processing.")

if __name__ == "__main__":
    test_streaming_equivalence()
