class Node:
    def __init__(self, value, parents=(), grad_fn=None):
        self.value = value
        self.parents = parents
        self.grad_fn = grad_fn
        self.grad = 0.0

    def backward(self, grad=1.0):
        self.grad += grad
        if self.grad_fn:
            grads = self.grad_fn(grad)
            for parent, g in zip(self.parents, grads):
                parent.backward(g)
