def save(model, path):
    values = [p.value for p in model.parameters()]
    with open(path, "w") as f:
        for v in values:
            f.write(str(v) + "\n")


def load(model, path):
    with open(path) as f:
        values = [float(x.strip()) for x in f.readlines()]
    for p, v in zip(model.parameters(), values):
        p.node.value = v
