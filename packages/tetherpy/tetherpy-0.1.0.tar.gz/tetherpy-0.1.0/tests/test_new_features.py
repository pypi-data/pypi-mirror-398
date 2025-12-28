import torch
import pytest
from tether import ALIF, LIF
from tether.utils.monitor import Monitor
from tether.data import rate_encoding

@pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
def test_alif_run():
    batch_size = 2
    n_neurons = 10
    n_steps = 50
    
    x = torch.rand(n_steps, batch_size, n_neurons).cuda()
    
    layer = ALIF(n_neurons, store_traces=True).cuda()
    spikes = layer(x)
    
    assert spikes.shape == x.shape
    assert layer.v_seq.shape == x.shape
    assert layer.a_seq.shape == x.shape
    
    print(f"ALIF Firing Rate: {layer.firing_rate}")

@pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
def test_monitor():
    batch_size = 2
    n_neurons = 10
    n_steps = 20
    
    model = torch.nn.Sequential(
        LIF(n_neurons, store_traces=True),
        ALIF(n_neurons, store_traces=True)
    ).cuda()
    
    monitor = Monitor(model)
    monitor.enable_voltage_monitoring(True)
    
    x = torch.rand(n_steps, batch_size, n_neurons).cuda()
    model(x)
    
    rates = monitor.get_firing_rates()
    traces = monitor.get_voltage_traces()
    
    assert len(rates) == 2
    assert len(traces) == 2
    print("Monitor Rates:", rates)

def test_encoding():
    x = torch.tensor([0.0, 0.5, 1.0])
    n_steps = 10
    spikes = rate_encoding(x, n_steps)
    assert spikes.shape == (n_steps, 3)
