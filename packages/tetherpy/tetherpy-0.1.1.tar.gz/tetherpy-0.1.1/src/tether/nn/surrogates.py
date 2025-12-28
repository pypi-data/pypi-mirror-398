import torch
import torch.nn as nn

class Surrogate(nn.Module):
    """
    Base class for surrogate gradient functions used in Spiking Neural Networks.

    Surrogate gradients allow for backpropagation through the non-differentiable 
    Heaviside step function used for spike generation.

    Parameters
    ----------
    alpha : float, optional
        Scaling parameter that controls the steepness/width of the surrogate derivative.
        Default is 2.0.
    trainable : bool, optional
        If True, `alpha` becomes a learnable parameter. Default is False.
    """
    def __init__(self, alpha=2.0, trainable=False):
        super().__init__()
        self.alpha = nn.Parameter(torch.tensor(float(alpha)), requires_grad=trainable)
    
    def get_id(self):
        """
        Return the integer ID corresponding to the surrogate type used in Triton kernels.
        
        Returns
        -------
        int
            Surrogate type ID.
        """
        raise NotImplementedError

class Arctan(Surrogate):
    """
    Arctan surrogate gradient.

    The surrogate derivative is given by:
    .. math::
        f'(x) = \\frac{1}{1 + (\\alpha \\pi x)^2}

    where x is the normalized membrane potential (v - threshold).
    """
    def get_id(self):
        return 0

class Sigmoid(Surrogate):
    """
    Sigmoid surrogate gradient.

    The surrogate function is a sigmoid, and its derivative is:
    .. math::
        f'(x) = \\alpha \\cdot \\sigma(\\alpha x) \\cdot (1 - \\sigma(\\alpha x))

    where :math:`\\sigma` is the logistic sigmoid function and x is the membrane potential gap.
    """
    def get_id(self):
        return 1

class FastSigmoid(Surrogate):
    """
    Fast Sigmoid (approximated) surrogate gradient.
    
    Uses a computationally cheaper approximation of the sigmoid derivative:
    .. math::
        f'(x) = \\frac{1}{(1 + |\\alpha x|)^2}
        
    This avoids expensive exponential operations.
    """
    def get_id(self):
        return 2
