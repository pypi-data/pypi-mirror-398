class ReLU:
    def __call__(self, inputs):
        return [x.relu() for x in inputs]

    def parameters(self):
        return []


class Sigmoid:
    def __call__(self, inputs):
        return [x.sigmoid() for x in inputs]

    def parameters(self):
        return []


class Tanh:
    def __call__(self, inputs):
        return [x.tanh() for x in inputs]

    def parameters(self):
        return []
