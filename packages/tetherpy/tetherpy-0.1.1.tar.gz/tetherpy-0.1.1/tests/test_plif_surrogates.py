import torch
import torch.nn as nn
import pytest
from tether import LIF, PLIF, Arctan, Sigmoid, FastSigmoid

@pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
def test_lif_surrogates():
    n_neurons = 10
    n_steps = 20
    x = torch.rand(n_steps, 1, n_neurons).cuda()
    
    # Test Arctan (Default)
    lif_arctan = LIF(n_neurons, surrogate=Arctan(alpha=2.0)).cuda()
    s_arctan = lif_arctan(x)
    assert s_arctan.shape == x.shape
    
    # Test Sigmoid
    lif_sigmoid = LIF(n_neurons, surrogate=Sigmoid(alpha=4.0)).cuda()
    s_sigmoid = lif_sigmoid(x)
    assert s_sigmoid.shape == x.shape
    
    # Test FastSigmoid
    lif_fast = LIF(n_neurons, surrogate=FastSigmoid(alpha=3.0)).cuda()
    s_fast = lif_fast(x)
    assert s_fast.shape == x.shape

@pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
def test_plif_gradients():
    n_neurons = 5
    n_steps = 10
    x = torch.rand(n_steps, 1, n_neurons).cuda()
    target = torch.randint(0, 2, (n_steps, 1, n_neurons)).float().cuda()
    
    # PLIF with learnable decay
    plif = PLIF(n_neurons, init_decay=0.5).cuda()
    
    # Check if decay is vector
    assert plif.decay.shape == (n_neurons,)
    
    out = plif(x)
    loss = ((out - target)**2).sum()
    loss.backward()
    
    assert plif.decay.grad is not None
    assert plif.decay.grad.shape == (n_neurons,)
    assert torch.any(plif.decay.grad != 0)
    print("PLIF Decay Gradients:", plif.decay.grad)

@pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
def test_surrogate_gradients():
    # Verify that different surrogates produce different gradients
    n_neurons = 1
    n_steps = 5
    # Input near threshold to ensure gradients
    x = torch.full((n_steps, 1, n_neurons), 0.2).cuda() 
    
    # Model 1: Arctan
    model1 = LIF(n_neurons, threshold=0.5, decay=0.5, surrogate=Arctan(alpha=1.0)).cuda()
    model1.v.zero_()
    out1 = model1(x)
    loss1 = out1.sum()
    loss1.backward()
    grad1 = model1.threshold.grad.clone()
    
    # Model 2: Sigmoid
    model2 = LIF(n_neurons, threshold=0.5, decay=0.5, surrogate=Sigmoid(alpha=1.0)).cuda()
    model2.v.zero_()
    out2 = model2(x)
    loss2 = out2.sum()
    loss2.backward()
    grad2 = model2.threshold.grad.clone()
    
    print(f"Arctan Grad: {grad1}, Sigmoid Grad: {grad2}")
    assert grad1 != grad2

@pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
def test_monitor_plif():
    from tether.utils.monitor import Monitor
    n_neurons = 5
    n_steps = 10
    
    model = nn.Sequential(
        PLIF(n_neurons, store_traces=True)
    ).cuda()
    
    monitor = Monitor(model)
    monitor.enable_voltage_monitoring(True)
    
    x = torch.rand(n_steps, 1, n_neurons).cuda()
    model(x)
    
    traces = monitor.get_voltage_traces()
    assert len(traces) == 1
    # Check shape: (Time, Batch, Neurons)
    assert list(traces.values())[0].shape == (n_steps, 1, n_neurons)
