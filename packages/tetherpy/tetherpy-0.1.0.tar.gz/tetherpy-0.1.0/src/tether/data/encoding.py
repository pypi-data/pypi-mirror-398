import torch
from torch.utils.data import Dataset

class SpikingDatasetWrapper(Dataset):
    """
    Wraps a standard dataset and applies an encoding function to the input.
    """
    def __init__(self, dataset: Dataset, encode_fn):
        self.dataset = dataset
        self.encode_fn = encode_fn

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        x, y = self.dataset[idx]
        return self.encode_fn(x), y

def rate_encoding(x: torch.Tensor, n_steps: int, gain: float = 1.0) -> torch.Tensor:
    """
    Convert continuous values to spike trains using rate encoding (Bernoulli).
    
    Parameters
    ----------
    x : torch.Tensor
        Input tensor with continuous values (usually in [0, 1]).
    n_steps : int
        Number of time steps to simulate.
    gain : float
        Scaling factor for firing probability.

    Returns
    -------
    torch.Tensor
        Spike tensor with shape (n_steps, *x.shape).
    """
    shape = (n_steps,) + x.shape
    prob = torch.clamp(x * gain, 0.0, 1.0)
    # Expand prob to time dimension
    prob = prob.unsqueeze(0).expand(shape)
    
    # Generate spikes
    spikes = torch.rand(shape, device=x.device) < prob
    return spikes.float()

def latency_encoding(x: torch.Tensor, n_steps: int, tau: float = 1.0, threshold: float = 0.01) -> torch.Tensor:
    """
    Convert continuous values to spike trains using latency encoding.
    Higher values fire earlier.
    
    Parameters
    ----------
    x : torch.Tensor
        Input tensor.
    n_steps : int
        Number of time steps.
    tau : float
        Time constant.
    threshold : float
        Threshold below which no spike is generated.

    Returns
    -------
    torch.Tensor
        Spike tensor with shape (n_steps, *x.shape).
    """
    # Calculate fire time: t_f = tau * ln(x / (x - theta)) ? 
    # Or simplified: t_f = (1 - x) * n_steps
    
    # Linear latency:
    # 1.0 -> step 0
    # 0.0 -> step n_steps-1
    
    x = torch.clamp(x, 0.0, 1.0)
    fire_step = ((1.0 - x) * (n_steps - 1)).long()
    
    spikes = torch.zeros((n_steps,) + x.shape, device=x.device)
    
    # Create a grid of time steps
    time_grid = torch.arange(n_steps, device=x.device).reshape((n_steps,) + (1,) * x.ndim)
    
    # Spike where time matches fire_step and x > threshold
    active = x > threshold
    spikes = (time_grid == fire_step) & active.unsqueeze(0)
    
    return spikes.float()
