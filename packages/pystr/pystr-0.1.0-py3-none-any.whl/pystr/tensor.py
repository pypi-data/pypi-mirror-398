from math import exp
from .autograd import Node

class Tensor:
    def __init__(self, value):
        self.node = Node(float(value))

    @property
    def value(self):
        return self.node.value

    @property
    def grad(self):
        return self.node.grad

    def backward(self):
        self.node.backward()

    def __add__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)

        def grad_fn(g):
            return g, g

        out = Tensor(0)
        out.node = Node(
            self.value + other.value,
            parents=(self.node, other.node),
            grad_fn=grad_fn
        )
        return out

    def __sub__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)

        def grad_fn(g):
            return g, -g

        out = Tensor(0)
        out.node = Node(
            self.value - other.value,
            parents=(self.node, other.node),
            grad_fn=grad_fn
        )
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)

        def grad_fn(g):
            return g * other.value, g * self.value

        out = Tensor(0)
        out.node = Node(
            self.value * other.value,
            parents=(self.node, other.node),
            grad_fn=grad_fn
        )
        return out

    def __truediv__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)

        def grad_fn(g):
            return g / other.value, -g * self.value / (other.value ** 2)

        out = Tensor(0)
        out.node = Node(
            self.value / other.value,
            parents=(self.node, other.node),
            grad_fn=grad_fn
        )
        return out

    def __pow__(self, power):
        power = power if isinstance(power, Tensor) else Tensor(power)

        def grad_fn(g):
            return g * power.value * (self.value ** (power.value - 1)), \
                   g * (self.value ** power.value) * exp(power.value * 0)

        out = Tensor(0)
        out.node = Node(
            self.value ** power.value,
            parents=(self.node, power.node),
            grad_fn=grad_fn
        )
        return out

    def relu(self):
        v = self.value

        def grad_fn(g):
            return (g if v > 0 else 0.0,)

        out = Tensor(0)
        out.node = Node(
            max(0.0, v),
            parents=(self.node,),
            grad_fn=grad_fn
        )
        return out

    def sigmoid(self):
        v = 1 / (1 + exp(-self.value))

        def grad_fn(g):
            return (g * v * (1 - v),)

        out = Tensor(0)
        out.node = Node(
            v,
            parents=(self.node,),
            grad_fn=grad_fn
        )
        return out

    def tanh(self):
        v = (exp(self.value) - exp(-self.value)) / (exp(self.value) + exp(-self.value))

        def grad_fn(g):
            return (g * (1 - v * v),)

        out = Tensor(0)
        out.node = Node(
            v,
            parents=(self.node,),
            grad_fn=grad_fn
        )
        return out
