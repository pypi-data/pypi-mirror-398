import math
from pystr.tensor import Tensor

class Sigmoid:
    def __call__(self, x):
        out = []
        for xi in x:
            val = 1.0 / (1.0 + math.exp(-xi.value))
            y = Tensor(val)

            def _backward(xi=xi, y=y):
                xi.grad += y.value * (1.0 - y.value) * y.grad

            y._backward = _backward
            y._prev = [xi]
            out.append(y)
        return out
