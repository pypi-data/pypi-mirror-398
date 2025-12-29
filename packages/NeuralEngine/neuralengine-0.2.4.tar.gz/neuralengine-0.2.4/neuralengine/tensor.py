import neuralengine.config as cf
from itertools import accumulate


autograd_enabled: bool = True

class Tensor:
    """Core Tensor class for autograd and computation."""
    def __init__(self, data, requires_grad: bool=False, dtype=cf.nu.float32, _operation=None):
        """
        @param data: Input data for the tensor.
        @param requires_grad: Whether to track gradients for this tensor.
        @param dtype: Data type of the tensor.
        """
        global autograd_enabled
        self.data = array(data, dtype=dtype)
        self.requires_grad = requires_grad if autograd_enabled else False
        self.shape = self.data.shape
        self.dtype = dtype
        self._operation = _operation
        if self.requires_grad:
            self.grad = cf.nu.zeros_like(self.data)
            self._children = []

        if hasattr(_operation, '__self__'):
            for _, attr in _operation.__self__.__dict__.items():
                if isinstance(attr, Tensor) and attr.requires_grad:
                    attr._children.append(self)
                elif isinstance(attr, list):
                    for t in attr:
                        if isinstance(t, Tensor) and t.requires_grad:
                            t._children.append(self)

    def __repr__(self) -> str:
        """String representation of the tensor."""
        return f"Tensor(data={self.data}, dtype={self.dtype.__name__}, requires_grad={self.requires_grad})"

    def __add__(self, other):
        """New = A + B"""
        return Add(self, other)()
    
    def __radd__(self, other):
        """New = B + A"""
        return self + other
    
    def __iadd__(self, other):
        """A += B"""
        return self + other
    
    def __sub__(self, other):
        """New = A - B"""
        return self + (-1 * other)
    
    def __rsub__(self, other):
        """New = B - A"""
        return (-1 * self) + other
    
    def __isub__(self, other):
        """A -= B"""
        return self + (-1 * other)
    
    def __mul__(self, other):
        """New = A * B"""
        return Multiply(self, other)()

    def __rmul__(self, other):
        """New = B * A"""
        return self * other
    
    def __imul__(self, other):
        """A *= B"""
        return self * other
    
    def __truediv__(self, other):
        """New = A / B"""
        return Divide(self, other)()

    def __rtruediv__(self, other):
        """New = B / A"""
        return Divide(other, self)()

    def __itruediv__(self, other):
        """A /= B"""
        return self / other
    
    def __neg__(self):
        """New = -A"""
        return -1 * self
    
    def __pow__(self, power):
        """New = A ** B"""
        return Power(self, power)()

    def __rpow__(self, base):
        """New = B ** A"""
        return Power(base, self)()

    def __matmul__(self, other):
        """New = A @ B"""
        return MatrixMul(self, other)()
    
    def __rmatmul__(self, other):
        """New = B @ A"""
        return MatrixMul(other, self)()

    def __getitem__(self, index):
        """New = A[index]"""
        return Slice(self, index)()
    
    def __setitem__(self, index, value):
        """A[index] = value"""
        return SetSlice(self, index, value)()

    def __eq__(self, value):
        """New = A == B"""
        return self.data == array(value)
    
    def __ne__(self, value):
        """New = A != B"""
        return self.data != array(value)

    def __gt__(self, other):
        """New = A > B"""
        return self.data > array(other)
    
    def __ge__(self, other):
        """New = A >= B"""
        return self.data >= array(other)
    
    def __lt__(self, other):
        """New = A < B"""
        return self.data < array(other)
    
    def __le__(self, other):
        """New = A <= B"""
        return self.data <= array(other)

    def sum(self, axis=-1, keepdims=False):
        """sum over axis.
        @param axis: Axis to sum over
        @param keepdims: Keep reduced dimensions
        """
        return Summation(self, axis, keepdims)()
    
    def max(self, axis=-1, keepdims=False):
        """max element over axis.
        @param axis: Axis to max element
        @param keepdims: Keep reduced dimensions
        """
        return Maximum(self, axis, keepdims)()
    
    def min(self, axis=-1, keepdims=False):
        """min element over axis.
        @param axis: Axis to min element
        @param keepdims: Keep reduced dimensions
        """
        return Minimum(self, axis, keepdims)()
    
    def mean(self, axis=-1, keepdims=False):
        """mean over axis.
        @param axis: Axis to mean over
        @param keepdims: Keep reduced dimensions
        """
        return Mean(self, axis, keepdims)()
    
    def var(self, axis=-1, keepdims=False):
        """variance over axis.
        @param axis: Axis to variance over
        @param keepdims: Keep reduced dimensions
        """
        return Variance(self, axis, keepdims)()
    
    def transpose(self, *axes):
        """Transpose the tensor.
        @param axes: New axes order
        """
        return Transpose(self, axes)()
    
    def reshape(self, *shape):
        """Reshape the tensor.
        @param shape: New shape for the tensor
        """
        return Reshape(self, shape)()
    
    def masked_fill(self, mask, fill):
        """Fill elements where mask is True with fill value.
        @param mask: Boolean mask to select elements
        @param fill: Value to fill where mask is True
        """
        return MaskedFill(fill, mask, self)()

    def zero_grad(self) -> None:
        """Reset gradients to zero."""
        if self.requires_grad:
            self.grad = cf.nu.zeros_like(self.data)

    def backward(self) -> None:
        """Compute gradients for the entire computation graph."""
        if self.requires_grad:
            self.grad = cf.nu.ones_like(self.data)
            if self._operation: self._operation()

    def _backward(self, child):
        """internal method to handle backward pass."""
        for i, c in enumerate(self._children):
            if c is child:
                del self._children[i]
                break
        if self.requires_grad and not self._children:
            if self._operation: self._operation()

    def to(self, device: cf.Device):
        """Move the tensor to the specified device.
        @param device: The device to move to, either CPU or CUDA
        """
        if device == cf.Device.CPU:
            if not cf._has_cuda or isinstance(self.data, cf.np.ndarray): return self
            transfer_fn = cf.cp.asnumpy
        elif device == cf.Device.CUDA:
            if not cf._has_cuda:
                raise RuntimeError("Cupy is not installed or no CUDA device is available.")
            if isinstance(self.data, cf.cp.ndarray): return self
            transfer_fn = cf.cp.asarray
        else:
            raise ValueError("device must be either Device.CPU or Device.CUDA")

        for attr in ['data', 'grad', 'm', 'v', 'velocity']:
            if hasattr(self, attr):
                setattr(self, attr, transfer_fn(getattr(self, attr)))   
        return self



class Add:
    def __init__(self, a, b):
        self.a = a if isinstance(a, Tensor) else Tensor(a)
        self.b = b if isinstance(b, Tensor) else Tensor(b)

    def __call__(self):
        requires_grad = self.a.requires_grad or self.b.requires_grad
        operation = self._deriv if requires_grad else None

        self.result = Tensor(self.a.data + self.b.data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(a + b)/∂a = 1, ∂(a + b)/∂b = 1
        if self.a.requires_grad:
            grad = self.result.grad
            self.a.grad += _reshape_grad(grad, self.a.shape, self.result.grad.shape) # rescale grad to match a's shape
            self.a._backward(self.result)
        if self.b.requires_grad:
            grad = self.result.grad
            self.b.grad += _reshape_grad(grad, self.b.shape, self.result.grad.shape) # rescale grad to match b's shape
            self.b._backward(self.result)


class Multiply:
    def __init__(self, a, b):
        self.a = a if isinstance(a, Tensor) else Tensor(a)
        self.b = b if isinstance(b, Tensor) else Tensor(b)

    def __call__(self):
        requires_grad = self.a.requires_grad or self.b.requires_grad
        operation = self._deriv if requires_grad else None

        self.result = Tensor(self.a.data * self.b.data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(a·b)/∂a = b, ∂(a·b)/∂b = a
        if self.a.requires_grad:
            grad = self.result.grad * self.b.data
            self.a.grad += _reshape_grad(grad, self.a.shape, self.result.grad.shape) # rescale grad to match a's shape
            self.a._backward(self.result)
        if self.b.requires_grad:
            grad = self.result.grad * self.a.data
            self.b.grad += _reshape_grad(grad, self.b.shape, self.result.grad.shape) # rescale grad to match b's shape
            self.b._backward(self.result)


class Divide:
    def __init__(self, a, b):
        self.a = a if isinstance(a, Tensor) else Tensor(a)
        self.b = b if isinstance(b, Tensor) else Tensor(b)

    def __call__(self):
        requires_grad = self.a.requires_grad or self.b.requires_grad
        operation = self._deriv if requires_grad else None

        self.result = Tensor(self.a.data / self.b.data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(a/b)/∂a = 1/b, ∂(a/b)/∂b = -a/b²
        if self.a.requires_grad:
            grad = self.result.grad / self.b.data
            self.a.grad += _reshape_grad(grad, self.a.shape, self.result.grad.shape) # rescale grad to match a's shape
            self.a._backward(self.result)
        if self.b.requires_grad:
            grad = -self.result.grad * (self.a.data / (self.b.data ** 2))
            self.b.grad += _reshape_grad(grad, self.b.shape, self.result.grad.shape) # rescale grad to match b's shape
            self.b._backward(self.result)


class Power:
    def __init__(self, base, exponent):
        self.base = base if isinstance(base, Tensor) else Tensor(base)
        self.exponent = exponent if isinstance(exponent, Tensor) else Tensor(exponent)

    def __call__(self):
        requires_grad = self.base.requires_grad or self.exponent.requires_grad
        operation = self._deriv if requires_grad else None

        self.result = Tensor(self.base.data ** self.exponent.data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(a^b)/∂a = b·a^{b-1}, ∂(a^b)/∂b = a^b·ln(a)
        if self.base.requires_grad:
            grad = self.result.grad * (self.exponent.data * (self.base.data ** (self.exponent.data - 1)))
            self.base.grad += _reshape_grad(grad, self.base.shape, grad.shape) # rescale grad to match base's shape
            self.base._backward(self.result)
        if self.exponent.requires_grad:
            grad = self.result.grad * (self.base.data ** self.exponent.data) * cf.nu.log(self.base.data)
            self.exponent.grad += _reshape_grad(grad, self.exponent.shape, grad.shape) # rescale grad to match exponent's shape
            self.exponent._backward(self.result)


class MatrixMul:
    def __init__(self, a, b):
        self.a = a if isinstance(a, Tensor) else Tensor(a)
        self.b = b if isinstance(b, Tensor) else Tensor(b)

    def __call__(self):
        requires_grad = self.a.requires_grad or self.b.requires_grad
        operation = self._deriv if requires_grad else None

        self.result = Tensor(self.a.data @ self.b.data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(A·B)/∂A = dL/dZ · Bᵗ, ∂(A·B)/∂B = Aᵗ · dL/dZ
        if self.a.requires_grad:
            grad = self.result.grad @ self.b.data.swapaxes(-1, -2)
            self.a.grad += _reshape_grad(grad, self.a.shape, grad.shape, matmul=True) # rescale grad to match a's shape
            self.a._backward(self.result)
        if self.b.requires_grad:
            grad = self.a.data.swapaxes(-1, -2) @ self.result.grad
            self.b.grad += _reshape_grad(grad, self.b.shape, grad.shape, matmul=True) # rescale grad to match b's shape
            self.b._backward(self.result)


class Logarithm:
    def __init__(self, tensor):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        self.result = Tensor(cf.nu.log(self.tensor.data), requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(ln(x))/∂x = 1/x
        if self.tensor.requires_grad:
            grad = self.result.grad / self.tensor.data
            self.tensor.grad += grad
            self.tensor._backward(self.result)


class SquareRoot:
    def __init__(self, tensor):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        self.result = Tensor(cf.nu.sqrt(self.tensor.data), requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(√x)/∂x = 1/(2√x)
        if self.tensor.requires_grad:
            grad = (0.5 / self.result.data) * self.result.grad
            self.tensor.grad += grad
            self.tensor._backward(self.result)


class Exponential:
    def __init__(self, tensor):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        self.result = Tensor(cf.nu.exp(self.tensor.data), requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(e^x)/∂x = e^x
        if self.tensor.requires_grad:
            grad = self.result.data * self.result.grad
            self.tensor.grad += grad
            self.tensor._backward(self.result)


class Absolute:
    def __init__(self, tensor):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        self.result = Tensor(cf.nu.abs(self.tensor.data), requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(|x|)/∂x = sign(x)
        if self.tensor.requires_grad:
            grad = cf.nu.sign(self.tensor.data) * self.result.grad
            self.tensor.grad += grad
            self.tensor._backward(self.result)


class Summation:
    def __init__(self, tensor, axis=-1, keepdims=False):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)
        self.axis = axis
        self.keepdims = keepdims

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        data = cf.nu.sum(self.tensor.data, axis=self.axis, keepdims=self.keepdims)

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(Σxᵢ)/∂xᵢ = 1
        if self.tensor.requires_grad:
            grad = self.result.grad
            if not self.keepdims: # expand grad to match tensor's shape
                grad = cf.nu.expand_dims(grad, axis=self.axis)
                
            self.tensor.grad += cf.nu.ones_like(self.tensor.data) * grad
            self.tensor._backward(self.result)


class Maximum:
    def __init__(self, tensor, axis=-1, keepdims=False):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)
        self.axis = axis
        self.keepdims = keepdims

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        data = cf.nu.max(self.tensor.data, axis=self.axis, keepdims=self.keepdims)

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # Gradient is distributed among all max elements
        if self.tensor.requires_grad:
            grad = self.result.grad
            max = self.result.data
            if not self.keepdims: # expand grad and max to match tensor's shape
                grad = cf.nu.expand_dims(grad, axis=self.axis)
                max = cf.nu.expand_dims(max, axis=self.axis)

            mask = (self.tensor.data == max).astype(max.dtype)
            mask /= cf.nu.sum(mask, axis=self.axis, keepdims=True)

            self.tensor.grad += mask * grad
            self.tensor._backward(self.result)


class Minimum:
    def __init__(self, tensor, axis=-1, keepdims=False):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)
        self.axis = axis
        self.keepdims = keepdims

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        data = cf.nu.min(self.tensor.data, axis=self.axis, keepdims=self.keepdims)

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # Gradient is distributed among all min elements
        if self.tensor.requires_grad:
            grad = self.result.grad
            min = self.result.data
            if not self.keepdims: # expand grad and min to match tensor's shape
                grad = cf.nu.expand_dims(grad, axis=self.axis)
                min = cf.nu.expand_dims(min, axis=self.axis)

            mask = (self.tensor.data == min).astype(min.dtype)
            mask /= cf.nu.sum(mask, axis=self.axis, keepdims=True)

            self.tensor.grad += mask * grad
            self.tensor._backward(self.result)


class Mean:
    def __init__(self, tensor, axis=-1, keepdims=False):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)
        self.axis = axis
        self.keepdims = keepdims

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        data = cf.nu.mean(self.tensor.data, axis=self.axis, keepdims=self.keepdims)

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(mean(x))/∂xᵢ = 1/N
        if self.tensor.requires_grad:
            grad = self.result.grad / self.tensor.shape[self.axis]
            if not self.keepdims: # expand grad to match tensor's shape
                grad = cf.nu.expand_dims(grad, axis=self.axis)

            self.tensor.grad += cf.nu.ones_like(self.tensor.data) * grad
            self.tensor._backward(self.result)


class Variance:
    def __init__(self, tensor, axis=-1, keepdims=False):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)
        self.axis = axis
        self.keepdims = keepdims

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        data = cf.nu.var(self.tensor.data, axis=self.axis, keepdims=self.keepdims)

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # ∂(Var(x))/∂xᵢ = 2/N·(xᵢ - mean(x))
        if self.tensor.requires_grad:
            mean = cf.nu.mean(self.tensor.data, axis=self.axis, keepdims=True)
            grad = (2 / self.tensor.shape[self.axis]) * (self.tensor.data - mean)
            grad *= self.result.grad if self.keepdims else cf.nu.expand_dims(self.result.grad, axis=self.axis)
            self.tensor.grad += grad
            self.tensor._backward(self.result)


class Transpose:
    def __init__(self, tensor, axes=None):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)
        self.axes = tuple(range(len(self.tensor.shape) - 1, -1, -1)) if not axes else axes

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        data = cf.nu.transpose(self.tensor.data, axes=self.axes)

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # Gradient is transposed back using inverse axes
        if self.tensor.requires_grad:
            inverse_axes = cf.nu.argsort(self.axes)
            grad = cf.nu.transpose(self.result.grad, axes=inverse_axes)
            self.tensor.grad += grad
            self.tensor._backward(self.result)


class Reshape:
    def __init__(self, tensor, shape):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)
        self.shape = shape

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        data = cf.nu.reshape(self.tensor.data, self.shape)

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # Gradient is reshaped back to input shape
        if self.tensor.requires_grad:
            grad = cf.nu.reshape(self.result.grad, self.tensor.shape)
            self.tensor.grad += grad
            self.tensor._backward(self.result)


class Concatenate:
    def __init__(self, tensors, axis=0):
        self.tensors = [t if isinstance(t, Tensor) else Tensor(t) for t in tensors]
        self.axis = axis

    def __call__(self):
        requires_grad = any(t.requires_grad for t in self.tensors)
        operation = self._deriv if requires_grad else None

        data = cf.nu.concatenate([t.data for t in self.tensors], axis=self.axis)

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # Gradient is split and distributed to each tensor according to their shape along axis
        split_indices = list(accumulate([t.data.shape[self.axis] for t in self.tensors[:-1]]))
        grad = cf.nu.split(self.result.grad, split_indices, axis=self.axis)

        for i, tensor in enumerate(self.tensors):
            if tensor.requires_grad:
                tensor.grad += grad[i]
                tensor._backward(self.result)


class Stack:
    def __init__(self, tensors, axis=0):
        self.tensors = [t if isinstance(t, Tensor) else Tensor(t) for t in tensors]
        self.axis = axis

    def __call__(self):
        requires_grad = any(t.requires_grad for t in self.tensors)
        operation = self._deriv if requires_grad else None

        data = cf.nu.stack([t.data for t in self.tensors], axis=self.axis)

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # Gradient is split and reshaped to each tensor according to their shape
        grad = cf.nu.split(self.result.grad, len(self.tensors), axis=self.axis)

        for i, tensor in enumerate(self.tensors):
            if tensor.requires_grad:
                tensor.grad += grad[i].reshape(tensor.shape)
                tensor._backward(self.result)


class MaskedFill:
    def __init__(self, tensor, condition, value):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)
        self.condition = condition
        self.value = value if isinstance(value, Tensor) else Tensor(value)

    def __call__(self):
        requires_grad = self.tensor.requires_grad or self.value.requires_grad
        operation = self._deriv if requires_grad else None

        data = cf.nu.where(self.condition, self.tensor.data, self.value.data)

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result
    
    def _deriv(self):
        # Gradient is distributed to tensor where condition is True, to value where False
        if self.tensor.requires_grad:
            grad = cf.nu.where(self.condition, self.result.grad, 0) # Only propagate grad where condition is True
            self.tensor.grad += grad
            self.tensor._backward(self.result)

        if self.value.requires_grad:
            grad = cf.nu.where(self.condition, 0, self.result.grad) # Only propagate grad where condition is False
            self.value.grad += grad
            self.value._backward(self.result)


class Slice:
    def __init__(self, tensor, index):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)
        self.index = index.astype(cf.nu.int32) if isinstance(index, cf.nu.ndarray) else index

    def __call__(self):
        requires_grad = self.tensor.requires_grad
        operation = self._deriv if requires_grad else None

        self.result = Tensor(self.tensor.data[self.index], requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # Gradient is placed at the sliced indices
        if self.tensor.requires_grad:
            grad = cf.nu.zeros_like(self.tensor.data)
            grad[self.index] = self.result.grad
            self.tensor.grad += grad
            self.tensor._backward(self.result)


class SetSlice:
    def __init__(self, tensor, index, value):
        self.tensor = tensor if isinstance(tensor, Tensor) else Tensor(tensor)
        self.index = index.astype(cf.nu.int32) if isinstance(index, cf.nu.ndarray) else index
        self.value = value if isinstance(value, Tensor) else Tensor(value)

    def __call__(self):
        requires_grad = self.tensor.requires_grad or self.value.requires_grad
        operation = self._deriv if requires_grad else None

        data = self.tensor.data.copy()
        data[self.index] = self.value.data

        self.result = Tensor(data, requires_grad=requires_grad, _operation=operation)
        return self.result

    def _deriv(self):
        # Gradient is placed at the non-sliced indices
        if self.tensor.requires_grad:
            grad = self.result.grad.copy()
            grad[self.index] = 0
            self.tensor.grad += grad
            self.tensor._backward(self.result)
        # Gradient is placed at the sliced indices
        if self.value.requires_grad:
            grad = self.result.grad[self.index]
            self.value.grad += grad
            self.value._backward(self.result)


class NoGrad:
    """Context manager to disable gradient tracking."""
    def __enter__(self):
        global autograd_enabled
        self.prev = autograd_enabled
        autograd_enabled = False

    def __exit__(self, *_):
        global autograd_enabled
        autograd_enabled = self.prev



def array(data, dtype=cf.nu.float32):
    """Convert data to a numpy array if it is not already.
    @param data: Input data to convert.
    @param dtype: Desired data type of the output array.
    """
    if isinstance(data, Tensor):
        return data.data.astype(dtype)
    return cf.nu.asarray(data, dtype=dtype)


def _reshape_grad(grad, input_shape, out_grad_shape, matmul=False):
    """Reshape the gradient to match the input shape."""
    
    grad_dim = len(out_grad_shape)
    in_dim = len(input_shape)
    for _ in range(grad_dim - in_dim):
        grad = grad.sum(axis=0)

    if matmul:
        return grad

    for n, dim in enumerate(input_shape):
        if dim == 1:
            grad = grad.sum(axis=n, keepdims=True)

    return grad