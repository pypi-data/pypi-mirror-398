from ..tensor import Tensor
from ..utils import *


class Loss:
    """Base class for all loss functions."""
    def __init__(self):
        self.loss_val = None

    def __call__(self, z, y, *args, **kwargs):
        """ Calls the loss compute method with the provided predictions and targets.
        @param z: Predictions (logits or outputs of the model).
        @param y: Ground truth labels.
        """
        z = z if isinstance(z, Tensor) else Tensor(z)
        y = y if isinstance(y, Tensor) else Tensor(y)
        loss = self.compute(z, y, *args, **kwargs)

        self.loss_val = loss.data.mean() if isinstance(loss, Tensor) else loss
        return loss

    def __repr__(self) -> str:
        """ Returns a string representation of the loss with its value if computed. """
        if self.loss_val is not None:
            return f"{self.__class__.__name__}: {self.loss_val:.4f}"
        else:
            return "No loss computed yet."
        
    def compute(self, z, y, *args, **kwargs):
        """ Computes the loss given predictions and targets. To be implemented by subclasses. """
        raise NotImplementedError("compute() must be implemented in subclasses")


class MSE(Loss):
    """Mean Squared Error loss."""
    def __init__(self):
        super().__init__()

    def compute(self, z, y):
        # MSE = 1/N Σ (z - y)²
        loss = (z - y) ** 2
        return mean(loss, axis=-1, keepdims=False)
    

class MAE(Loss):
    """Mean Absolute Error loss."""
    def __init__(self):
        super().__init__()

    def compute(self, z, y):
        # MAE = 1/N Σ |z - y|
        loss = abs(z - y)
        return mean(loss, axis=-1, keepdims=False)
    

class Huber(Loss):
    """Huber loss."""
    def __init__(self, delta: float = 1.0):
        """
        @param delta: Threshold for Huber loss
        """
        super().__init__()
        self.delta = delta

    def compute(self, z, y):
        # Huber: if |z - y| <= δ: 1/2 (z - y)² else: δ(|z - y| - 1/2 δ)
        diff = z - y
        abs_diff = abs(diff)
        loss = where(abs_diff <= self.delta, 0.5 * diff ** 2, self.delta * (abs_diff - 0.5 * self.delta))
        return mean(loss, axis=-1, keepdims=False)
    

class CrossEntropy(Loss):
    """Cross Entropy loss."""
    def __init__(self, binary: bool = False, eps: float = 1e-7):
        """
        @param binary: Whether to use binary cross entropy (default: False)
        @param eps: Small value for numerical stability
        """
        super().__init__()
        self.binary = binary
        self.eps = eps

    def compute(self, z, y):
        # Categorical Cross Entropy: -Σ y.log(p)
        z = clip(z, self.eps, 1 - self.eps)
        loss = -y * log(z)
        # Binary Cross Entropy: -Σ y.log(p) + (1 - y).log(1 - p)
        if self.binary:
            loss -= (1 - y) * log(1 - z)
        return sum(loss, axis=-1, keepdims=False)
    

class GaussianNLL(Loss):
    """Gaussian Negative Log Likelihood loss."""
    def __init__(self, eps: float = 1e-7):
        """
        @param eps: Small value for numerical stability
        """
        super().__init__()
        self.eps = eps

    def compute(self, z, y):
        # NLL = 1/2 (log(σ²) + ((y - μ)²) / σ²)
        mu, log_var = z[..., 0], z[..., 1]
        var = exp(log_var) + self.eps
        loss = 0.5 * (log_var + ((y - mu) ** 2) / var)
        return mean(loss, axis=-1, keepdims=False)
    

class KLDivergence(Loss):
    """Kullback-Leibler Divergence loss."""
    def __init__(self, eps: float = 1e-7):
        """
        @param eps: Small value for numerical stability
        """
        super().__init__()
        self.eps = eps

    def compute(self, z, y):
        # KL(y||z) = y.log(y / z)
        z = where(z <= 0, self.eps, z)
        y = where(y <= 0, self.eps, y)
        loss = y * log(y / z)
        return sum(loss, axis=-1, keepdims=False)