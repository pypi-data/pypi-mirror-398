class SGD:
    def __init__(self, params, lr=0.01, clip=None):
        self.params = params
        self.lr = lr
        self.clip = clip

    def step(self):
        for p in self.params:
            g = p.grad
            if self.clip is not None:
                g = max(-self.clip, min(self.clip, g))
            p.node.value -= self.lr * g

    def zero_grad(self):
        for p in self.params:
            p.node.grad = 0.0
