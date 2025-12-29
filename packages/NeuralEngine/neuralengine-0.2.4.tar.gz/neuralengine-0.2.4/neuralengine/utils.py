import neuralengine.config as cf
from .tensor import *


def tensor(data, requires_grad: bool = False) -> Tensor:
    """
    Creates a Tensor from data.
    @param data: Input data
    @param requires_grad: Track gradients
    """
    return Tensor(data, requires_grad=requires_grad)

def zeros(shape, requires_grad: bool = False) -> Tensor:
    """
    Creates a Tensor of zeros.
    @param shape: Shape of tensor
    @param requires_grad: Track gradients
    """
    data = cf.nu.zeros(shape)
    return Tensor(data, requires_grad=requires_grad)

def ones(shape, requires_grad: bool = False) -> Tensor:
    """
    Creates a Tensor of ones.
    @param shape: Shape of tensor
    @param requires_grad: Track gradients
    """
    data = cf.nu.ones(shape)
    return Tensor(data, requires_grad=requires_grad)

def rand(shape, requires_grad: bool = False) -> Tensor:
    """
    Creates a Tensor with random values (uniform).
    @param shape: Shape of tensor
    @param requires_grad: Track gradients
    """
    data = cf.nu.random.rand(*shape)
    return Tensor(data, requires_grad=requires_grad)

def randn(shape, xavier: bool = False, requires_grad: bool = False) -> Tensor:
    """
    Creates a Tensor with random values (normal).
    @param shape: Shape of tensor
    @param xavier: Use Xavier scaling
    @param requires_grad: Track gradients
    """
    data = cf.nu.random.randn(*shape)
    if xavier:
        # Xavier scaling: data / √(first dimension)
        data /= cf.nu.sqrt(shape[0])
    return Tensor(data, requires_grad=requires_grad)

def randint(low: int = 0, high: int = 9, shape: tuple = (1,), requires_grad: bool = False) -> Tensor:
    """
    Creates a Tensor with random integers.
    @param low: Minimum value
    @param high: Maximum value
    @param shape: Shape of tensor
    @param requires_grad: Track gradients
    """
    data = cf.nu.random.randint(low, high, size=shape)
    return Tensor(data, dtype=cf.nu.int32, requires_grad=requires_grad)

def zeros_like(tensor: Tensor, requires_grad: bool = None) -> Tensor:
    """
    Creates a zeros Tensor with same shape as input.
    @param tensor: Reference tensor
    @param requires_grad: Track gradients
    """
    shape = tensor.shape
    return zeros(shape, tensor.requires_grad if requires_grad is None else requires_grad)

def ones_like(tensor: Tensor, requires_grad: bool = None) -> Tensor:
    """
    Creates a ones Tensor with same shape as input.
    @param tensor: Reference tensor
    @param requires_grad: Track gradients
    """
    shape = tensor.shape
    return ones(shape, tensor.requires_grad if requires_grad is None else requires_grad)

def rand_like(tensor: Tensor, requires_grad: bool = None) -> Tensor:
    """
    Creates a random Tensor with same shape as input. (uniform)
    @param tensor: Reference tensor
    @param requires_grad: Track gradients
    """
    shape = tensor.shape
    return rand(shape, tensor.requires_grad if requires_grad is None else requires_grad)

def randn_like(tensor: Tensor, xavier: bool = False, requires_grad: bool = None) -> Tensor:
    """
    Creates a random normal Tensor with same shape as input. (normal)
    @param tensor: Reference tensor
    @param xavier: Use Xavier scaling
    @param requires_grad: Track gradients
    """
    shape = tensor.shape
    return randn(shape, xavier, tensor.requires_grad if requires_grad is None else requires_grad)

def randint_like(tensor: Tensor, low: int = 0, high: int = 9, requires_grad: bool = None) -> Tensor:
    """
    Creates a random integer Tensor with same shape as input.
    @param tensor: Reference tensor
    @param low: Minimum value
    @param high: Maximum value
    @param requires_grad: Track gradients
    """
    shape = tensor.shape
    return randint(low, high, shape, tensor.requires_grad if requires_grad is None else requires_grad)

def sum(tensor: Tensor, axis: int = -1, keepdims: bool = False) -> Tensor:
    """
    Sum over axis.
    @param tensor: Input tensor
    @param axis: Axis to sum
    @param keepdims: Keep reduced dims
    """
    return tensor.sum(axis=axis, keepdims=keepdims)

def max(tensor: Tensor, axis: int = -1, keepdims: bool = False) -> Tensor:
    """
    Max over axis.
    @param tensor: Input tensor
    @param axis: Axis to max
    @param keepdims: Keep reduced dims
    """
    return tensor.max(axis=axis, keepdims=keepdims)

def min(tensor: Tensor, axis: int = -1, keepdims: bool = False) -> Tensor:
    """
    Min over axis.
    @param tensor: Input tensor
    @param axis: Axis to min
    @param keepdims: Keep reduced dims
    """
    return tensor.min(axis=axis, keepdims=keepdims)

def mean(tensor: Tensor, axis: int = -1, keepdims: bool = False) -> Tensor:
    """
    Mean over axis.
    @param tensor: Input tensor
    @param axis: Axis to mean
    @param keepdims: Keep reduced dims
    """
    return tensor.mean(axis=axis, keepdims=keepdims)

def var(tensor: Tensor, axis: int = -1, keepdims: bool = False) -> Tensor:
    """
    Variance over axis.
    @param tensor: Input tensor
    @param axis: Axis to variance
    @param keepdims: Keep reduced dims
    """
    return tensor.var(axis=axis, keepdims=keepdims)

def log(tensor: Tensor) -> Tensor:
    """
    Elementwise natural logarithm.
    @param tensor: Input tensor
    """
    return Logarithm(tensor)()

def sqrt(tensor: Tensor) -> Tensor:
    """
    Elementwise square root.
    @param tensor: Input tensor
    """
    return SquareRoot(tensor)()

def exp(tensor: Tensor) -> Tensor:
    """
    Elementwise exponential.
    @param tensor: Input tensor
    """
    return Exponential(tensor)()

def abs(tensor: Tensor) -> Tensor:
    """
    Elementwise absolute value.
    @param tensor: Input tensor
    """
    return Absolute(tensor)()

def concat(*tensors: Tensor, axis: int = 0) -> Tensor:
    """
    Concatenates tensors along axis.
    @param tensors: Tensors to concatenate
    @param axis: Axis to concatenate
    """
    return Concatenate(tensors, axis)()

def stack(*tensors: Tensor, axis: int = 0) -> Tensor:
    """
    Stacks tensors along axis.
    @param tensors: Tensors to stack
    @param axis: Axis to stack
    """
    return Stack(tensors, axis)()

def where(condition, tensor: Tensor, value) -> Tensor:
    """
    Elementwise selection: if condition then tensor else value.
    @param condition: Boolean mask
    @param tensor: Tensor to select
    @param value: Value to fill where condition is False
    """
    return MaskedFill(tensor, condition, value)()

def clip(tensor: Tensor, min, max) -> Tensor:
    """
    Clips tensor values to [min, max].
    @param tensor: Input tensor
    @param min: Minimum value
    @param max: Maximum value
    """
    # min/max clipping
    tensor = tensor.masked_fill(tensor < min, min)
    tensor = tensor.masked_fill(tensor > max, max)
    return tensor

def one_hot(labels, num_classes: int | None = None) -> Tensor:
    """
    Converts integer labels to one-hot encoding.
    @param labels: Integer labels
    @param num_classes: Number of classes
    """
    labels = array(labels, dtype=cf.nu.int32)
    if num_classes is None:
        num_classes = int(cf.nu.max(labels) + 1)
    # one-hot encoding: eye(num_classes)[labels]
    encoded = cf.nu.eye(num_classes)[labels]
    return Tensor(encoded, dtype=cf.nu.int32)