class Model:
    def __init__(self):
        self.layers = []

    def add(self, layer):
        self.layers.append(layer)

    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x

    def parameters(self):
        params = []
        for layer in self.layers:
            if hasattr(layer, "parameters"):
                params.extend(layer.parameters())
        return params

    def fit(self, x_data, y_data, loss_fn, optimizer, epochs=1000, verbose=100):
        step = 0
        while step < epochs:
            total_loss = None

            for x, y in zip(x_data, y_data):
                y_pred = self.forward(x)[0]
                loss = loss_fn(y_pred, y)
                total_loss = loss if total_loss is None else total_loss + loss

            total_loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            if verbose and step % verbose == 0:
                print("epoch:", step, "loss:", round(total_loss.value, 6))

            step += 1
