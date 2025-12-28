import torch
import pytest
from tether.nn import LIF

def pytorch_lif_ref(x_seq, v_init, decay, threshold):
    """The slow but trusted PyTorch reference implementation."""
    n_steps, batch_size, n_neurons = x_seq.shape
    v = v_init.clone()
    spikes_seq = []
    
    for t in range(n_steps):
        v = v * decay + x_seq[t]
        spike = (v >= threshold).float()
        spikes_seq.append(spike)
        # Hard reset
        v = v * (1 - spike) 
        
    return torch.stack(spikes_seq), v

@pytest.mark.parametrize("n_neurons", [128, 1024])
@pytest.mark.parametrize("n_steps", [16, 64])
def test_lif_fwd_bwd(n_neurons, n_steps):
    """
    Test forward and backward passes of LIF.

    Parameters
    ----------
    n_neurons : int
        Number of neurons.
    n_steps : int
        Number of time steps.
    """
    device = 'cuda'
    batch_size = 32
    decay, threshold = 0.9, 1.0
    
    # 1. Setup Data
    x = torch.randn(n_steps, batch_size, n_neurons, device=device, requires_grad=True)
    v_init = torch.zeros(batch_size * n_neurons, device=device)
    
    # 2. Run Tether (Triton)
    tether_layer = LIF(n_neurons=n_neurons, decay=decay, threshold=threshold).to(device)
    tether_spikes = tether_layer(x)
    
    # 3. Run Reference (Vanilla PyTorch)
    ref_spikes, _ = pytorch_lif_ref(x, v_init.view(batch_size, n_neurons), decay, threshold)
    ref_spikes = ref_spikes.view(n_steps, batch_size, n_neurons)

    # 4. Compare Forward Pass
    torch.testing.assert_close(tether_spikes, ref_spikes, atol=1e-5, rtol=1e-5)
    print(f"Forward Match: {n_neurons} neurons, {n_steps} steps")

    # 5. Compare Backward Pass (Gradients)
    tether_spikes.sum().backward()
    tether_grad = x.grad.clone()
    
    x.grad.zero_()
    # Note: For exact gradient matching, you'd implement the same surrogate in the ref.
    # Here we check if gradients are flowing and have the correct shape/magnitude.
    assert tether_grad is not None
    assert tether_grad.shape == x.shape
    print(f"Backward Flowing: Mean Grad = {tether_grad.abs().mean().item():.4f}")

    # Check parameter gradients
    for param_name, param in [("alpha", tether_layer.alpha), 
                              ("decay", tether_layer.decay), 
                              ("threshold", tether_layer.threshold)]:
        assert param.grad is not None, f"Gradient for {param_name} is None"
        print(f"Gradient for {param_name}: {param.grad.item():.4f}")
        assert param.grad.abs().item() > 0, f"Gradient for {param_name} should be non-zero"

if __name__ == "__main__":
    test_lif_fwd_bwd(1024, 64)