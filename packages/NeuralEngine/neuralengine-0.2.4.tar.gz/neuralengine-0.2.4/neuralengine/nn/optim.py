import neuralengine.config as cf
from ..tensor import Tensor


class Optimizer:
    """Base class for all optimizers."""
    def __init__(self):
        self._params = None

    @property
    def parameters(self) -> list[Tensor]:
        """The parameters of the optimizer."""
        return self._params
    
    @parameters.setter
    def parameters(self, params: list[Tensor]) -> None:
        if any(not isinstance(param, Tensor) for param in params):
            raise ValueError("params must be a iterable of Tensor objects")
        
        self._params = params
        self._initialize_parameters()

    def _initialize_parameters(self) -> None:
        """Initializes optimizer-specific states. To be implemented by subclasses."""
        pass

    def step(self) -> None:
        """Performs a single optimization step. To be implemented by subclasses."""
        raise NotImplementedError("step() must be implemented in subclasses")

    def reset_grad(self) -> None:
        """Resets the gradients of all parameters to zero."""
        for param in self._params:
            param.zero_grad()


class SGD(Optimizer):
    """Stochastic Gradient Descent (SGD) optimizer."""
    def __init__(self, lr: float = 1e-2, reg: float = 0, momentum: float = 0, nesterov: bool = False):
        """
        @param lr: Learning rate
        @param reg: L2 regularization
        @param momentum: Momentum factor
        @param nesterov: Use Nesterov momentum
        """

        super().__init__()
        self.lr = lr
        self.reg = reg
        self.momentum = momentum
        self.nesterov = nesterov

    def _initialize_parameters(self) -> None:
        """Initializes velocity for momentum."""
        if self.momentum > 0:
            for param in self._params:
                param.velocity = cf.nu.zeros_like(param.data)

    def step(self) -> None:
        """Updates the parameters using gradients and learning rate."""
        for param in self._params:
            # grad = ∂L/∂w + λw (L2 regularization)
            grad = param.grad + self.reg * param.data
            if self.momentum > 0:
                v_prev = param.velocity
                # velocity update: v = μ · v_prev + grad
                param.velocity = self.momentum * v_prev + grad
                if self.nesterov:
                    # Nesterov update: grad = (1 + μ) · v - μ · v_prev
                    grad = (1 + self.momentum) * param.velocity - self.momentum * v_prev
                else:
                    grad = param.velocity
            # SGD update: w = w - η · grad
            param.data -= self.lr * grad


class Adam(Optimizer):
    """Adam optimizer. Switches to RMSProp if only one beta is provided."""
    def __init__(self, lr: float = 1e-3, betas: tuple[float, float] | float = (0.9, 0.99), eps: float = 1e-7, reg: float = 0):
        """
        @param lr: Learning rate
        @param betas: (beta_m, beta_v) for Adam, beta_v for RMSProp
        @param eps: Numerical stability
        @param reg: L2 regularization
        """

        super().__init__()
        self.lr = lr
        betas = betas if isinstance(betas, (list, tuple)) else (betas,)
        self.beta_m = betas[0] if len(betas) == 2 else None
        self.beta_v = betas[-1]
        self.eps = eps
        self.reg = reg
        self.t = 0

    def _initialize_parameters(self) -> None:
        """Initializes m and v states for Adam/RMSProp."""
        for param in self._params:
            param.v = cf.nu.zeros_like(param.data)
            if self.beta_m:
                param.m = cf.nu.zeros_like(param.data)

    def step(self) -> None:
        """
        Updates the parameters using Adam optimization algorithm.
        RMSProp algorithm is used if only one beta is provided.
        """

        self.t += 1
        for param in self._params:
            # grad = ∂L/∂w + λw (L2 regularization)
            grad = param.grad + self.reg * param.data
            # v = β_v · v_prev + (1 - β_v) · grad²
            param.v = (param.v * self.beta_v + (1 - self.beta_v) * cf.nu.square(grad))
            v_hat = param.v / (1 - self.beta_v ** self.t)
            if self.beta_m:
                # m = β_m · m_prev + (1 - β_m) · grad
                param.m = (param.m * self.beta_m + (1 - self.beta_m) * grad)
                m_hat = param.m / (1 - self.beta_m ** self.t)
                # Adam update: w = w - η · m̂ / (√v̂ + ε)
                update = (self.lr * m_hat) / (cf.nu.sqrt(v_hat) + self.eps)
            else:
                # RMSProp update: w = w - η · grad / (√v̂ + ε)
                update = (self.lr * grad) / (cf.nu.sqrt(v_hat) + self.eps)
            param.data -= update