import torch
from torch.utils.data import Dataset, DataLoader
from tether.data import SpikingDatasetWrapper, rate_encoding

class SimpleDataset(Dataset):
    def __init__(self):
        self.data = torch.rand(10, 5) # 10 samples, 5 features
        self.targets = torch.randint(0, 2, (10,))
    
    def __len__(self):
        return 10
    
    def __getitem__(self, idx):
        return self.data[idx], self.targets[idx]

def test_spiking_dataset_wrapper():
    dataset = SimpleDataset()
    n_steps = 5
    
    # Wrap it
    spiking_ds = SpikingDatasetWrapper(
        dataset, 
        encode_fn=lambda x: rate_encoding(x, n_steps=n_steps)
    )
    
    assert len(spiking_ds) == 10
    
    # Get item
    x_spike, y = spiking_ds[0]
    # Check shape: (Time, Features)
    assert x_spike.shape == (n_steps, 5)
    assert y == dataset.targets[0]
    
    # DataLoader check
    dl = DataLoader(spiking_ds, batch_size=2)
    batch_x, batch_y = next(iter(dl))
    
    # Batch shape: (Batch, Time, Features)
    assert batch_x.shape == (2, n_steps, 5)
