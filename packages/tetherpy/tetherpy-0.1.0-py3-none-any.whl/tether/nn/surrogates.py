import torch
import torch.nn as nn

class Surrogate(nn.Module):
    def __init__(self, alpha=2.0, trainable=False):
        super().__init__()
        self.alpha = nn.Parameter(torch.tensor(float(alpha)), requires_grad=trainable)
    
    def get_id(self):
        raise NotImplementedError

class Arctan(Surrogate):
    """
    Arctan surrogate gradient:
    f'(x) = 1 / (1 + (alpha * pi * x)^2)
    """
    def get_id(self):
        return 0

class Sigmoid(Surrogate):
    """
    Sigmoid surrogate gradient:
    f'(x) = alpha * sigmoid(x) * (1 - sigmoid(x))
    where x is scaled input.
    """
    def get_id(self):
        return 1

class FastSigmoid(Surrogate):
    """
    Fast Sigmoid (approx) surrogate gradient:
    f'(x) = 1 / (1 + |alpha * x|)^2
    """
    def get_id(self):
        return 2
