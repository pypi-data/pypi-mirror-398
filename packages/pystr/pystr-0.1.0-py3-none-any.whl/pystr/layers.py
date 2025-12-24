import random
from .tensor import Tensor

class Dense:
    def __init__(self, in_features, out_features):
        scale = (2 / in_features) ** 0.5
        self.weights = [
            [Tensor(random.uniform(-scale, scale)) for _ in range(in_features)]
            for _ in range(out_features)
        ]
        self.biases = [Tensor(0.0) for _ in range(out_features)]

    def __call__(self, inputs):
        outputs = []
        for w_row, b in zip(self.weights, self.biases):
            s = b
            for w, x in zip(w_row, inputs):
                s = s + w * x
            outputs.append(s)
        return outputs

    def parameters(self):
        params = []
        for row in self.weights:
            params.extend(row)
        params.extend(self.biases)
        return params
