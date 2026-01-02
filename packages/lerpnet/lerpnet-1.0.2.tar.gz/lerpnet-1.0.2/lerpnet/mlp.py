import random
from .layer import Layer

class MLP:
    def __init__(self, nin, nouts):
        sizes = [nin] + nouts
        self.layers = [Layer(sizes[i], sizes[i+1]) for i in range(len(nouts))]

    def __call__(self, x):
        for layer in self.layers:
            x = layer(x)
        return x

    def parameters(self):
        return [p for l in self.layers for p in l.parameters()]

    def reset_parameters(self):
        for p in self.parameters():
            p.data = random.uniform(-1, 1)

    def get_all_weights_and_biases(self):
        return [{"w": w, "b": b} for w, b in
                (layer.get_weights_and_biases() for layer in self.layers)]
