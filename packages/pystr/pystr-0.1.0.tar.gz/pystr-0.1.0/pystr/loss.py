class MSE:
    def __call__(self, y_pred, y_true):
        diff = y_pred - y_true
        return diff * diff


class MAE:
    def __call__(self, y_pred, y_true):
        diff = y_pred - y_true
        return diff.relu() + (-diff).relu()
