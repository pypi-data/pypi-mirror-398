import math
import random
import os
import json
from typing import List, Union, Optional, Dict, Any
import pickle
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import csv


class Value:    
    def __init__(self, data, _children=(), _op='', label=''):
        self.data = data
        self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(_children)
        self._op = _op
        self.label = label

    def __repr__(self):
        return f"Value(data={self.data})"

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), '+')
        def _backward():
            self.grad += out.grad
            other.grad += out.grad
        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), '*')
        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out

    def __pow__(self, other):
        assert isinstance(other, (int, float)), "only supporting int/float powers"
        out = Value(self.data**other, (self,), f'**{other}')
        def _backward():
            self.grad += other * (self.data ** (other - 1)) * out.grad
        out._backward = _backward
        return out

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        return self * other**-1

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + (-other)

    def __radd__(self, other):
        return self + other

    def __rsub__(self, other):
        return Value(other) - self

    def tanh(self):
        x = self.data
        t = (math.exp(2*x) - 1)/(math.exp(2*x) + 1)
        out = Value(t, (self,), 'tanh')
        def _backward():
            self.grad += (1 - t**2) * out.grad
        out._backward = _backward
        return out

    def exp(self):
        x = self.data
        out = Value(math.exp(x), (self,), 'exp')
        def _backward():
            self.grad += out.data * out.grad
        out._backward = _backward
        return out

    def backward(self):
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)
        build_topo(self)
        self.grad = 1.0
        for node in reversed(topo):
            node._backward()


class Neuron:
    
    def __init__(self, nin):
        self.w = [Value(random.uniform(-1, 1)) for _ in range(nin)]
        self.b = Value(random.uniform(-1, 1))

    def __call__(self, x):
        act = sum((wi * xi for wi, xi in zip(self.w, x)), self.b)
        out = act.tanh()
        return out

    def parameters(self):
        return self.w + [self.b]


class Layer:
    
    def __init__(self, nin, nout):
        self.neurons = [Neuron(nin) for _ in range(nout)]

    def __call__(self, x):
        outs = [n(x) for n in self.neurons]
        return outs[0] if len(outs) == 1 else outs

    def parameters(self):
        return [p for neuron in self.neurons for p in neuron.parameters()]
    
    def get_weights_and_biases(self):
        n_neurons = len(self.neurons)
        n_inputs = len(self.neurons[0].w)
        
        weights = [[0.0 for _ in range(n_neurons)] for _ in range(n_inputs)]
        biases = [0.0 for _ in range(n_neurons)]
        
        for j, neuron in enumerate(self.neurons):
            biases[j] = neuron.b.data
            for i, w in enumerate(neuron.w):
                weights[i][j] = w.data
        
        return weights, biases


class MLP:
    def __init__(self, nin, nouts):
        sz = [nin] + nouts
        self.layers = [Layer(sz[i], sz[i+1]) for i in range(len(nouts))]

    def __call__(self, x):
        for layer in self.layers:
            x = layer(x)
        return x

    def parameters(self):
        return [p for layer in self.layers for p in layer.parameters()]

    def reset_parameters(self):
        for p in self.parameters():
            p.data = random.uniform(-1, 1)
    
    def get_all_weights_and_biases(self):
        layers_data = []
        for layer in self.layers:
            weights, biases = layer.get_weights_and_biases()
            layers_data.append({
                "w": weights,
                "b": biases
            })
        return layers_data


class NeuralNetworkTrainer:
    
    def __init__(self, xs, ys, output_dir='output'):
        self.xs_original = xs
        self.ys_original = ys
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Validate data
        self._validate_and_prepare_data()
        
        # Default parameters (can be changed by user)
        self.params = {
            'architecture': [4, 4, 1],
            'normalization_method': 'max',
            'lr_finder_steps': 1000,
            'training_epochs': 3000,
            'model_filename': 'model.pkl',
            'norm_filename': 'norm_constants.json',
            'weights_filename': 'model_weights.json',
            'show_plots': True
        }
        
        # Create model
        self.model = MLP(self.input_dim, self.params['architecture'])
        
    def _validate_and_prepare_data(self):
        if len(self.xs_original) != len(self.ys_original):
            raise ValueError(f"Error: xs ({len(self.xs_original)}) and ys ({len(self.ys_original)}) must have same length")
        
        # Convert to numpy arrays
        xs_array = np.array(self.xs_original, dtype=float)
        ys_array = np.array(self.ys_original, dtype=float)
        
        # Get input dimension
        if xs_array.ndim == 1:
            self.input_dim = 1
            xs_array = xs_array.reshape(-1, 1)
        else:
            self.input_dim = xs_array.shape[1]
        
        # Flatten ys if needed
        if ys_array.ndim > 1:
            ys_array = ys_array[:, 0]
        
        self.xs_array = xs_array
        self.ys_array = ys_array
    
    def set_parameter(self, param_name, value):
        if param_name in self.params:
            self.params[param_name] = value
        else:
            raise ValueError(f"Unknown parameter: {param_name}")
    
    def get_parameter(self, param_name):
        return self.params.get(param_name)
    
    def normalize_data(self):
        method = self.params['normalization_method']
        
        if method == 'max':
            x_max = np.max(np.abs(self.xs_array))
            y_max = np.max(np.abs(self.ys_array))
            
            self.xs_norm = self.xs_array / x_max
            self.ys_norm = self.ys_array / y_max
            
            self.norm_constants = {
                'method': 'max',
                'x_max': float(x_max),
                'y_max': float(y_max)
            }
            
        elif method == 'minmax':
            x_min = np.min(self.xs_array, axis=0)
            x_max = np.max(self.xs_array, axis=0)
            y_min = np.min(self.ys_array)
            y_max = np.max(self.ys_array)
            
            self.xs_norm = (self.xs_array - x_min) / (x_max - x_min + 1e-8)
            self.ys_norm = (self.ys_array - y_min) / (y_max - y_min + 1e-8)
            
            self.norm_constants = {
                'method': 'minmax',
                'x_min': x_min.tolist(),
                'x_max': x_max.tolist(),
                'y_min': float(y_min),
                'y_max': float(y_max)
            }
        
        # Convert to list format for MLP
        self.xs = self.xs_norm.tolist()
        self.ys = self.ys_norm.tolist()
        
        return self.norm_constants
    
    def find_learning_rate(self, lr_start=1e-3, lr_end=1.0):
        self.model.reset_parameters()
        
        # Create learning rates on log scale
        steps = self.params['lr_finder_steps']
        lre = np.linspace(np.log10(lr_start), np.log10(lr_end), steps)
        lrs = 10 ** lre
        
        lr_list = []
        loss_list = []
        best_lr = lrs[0]
        best_loss = float('inf')
        
        for i in range(steps):
            # Forward pass
            ypred = [self.model(x) for x in self.xs]
            loss = sum((yout - ygt)**2 for ygt, yout in zip(self.ys, ypred))
            
            # Backward pass
            for p in self.model.parameters():
                p.grad = 0.0
            loss.backward()
            
            # Update with current learning rate
            lr = lrs[i]
            for p in self.model.parameters():
                p.data += -lr * p.grad
            
            # Store results
            lr_list.append(lr)
            loss_list.append(loss.data)
            
            # Update best LR
            if loss.data < best_loss:
                best_loss = loss.data
                best_lr = lr
        
        self.best_lr = best_lr
        self.lr_list = lr_list
        self.loss_list = loss_list
        
        return best_lr
    
    def train(self, learning_rate=None):
        if learning_rate is None:
            learning_rate = self.best_lr
        
        self.model.reset_parameters()
        
        epochs = self.params['training_epochs']
        losses, rmses, mapes, r2s = [], [], [], []
        actual_vs_predicted = []
        
        for epoch in range(epochs):
            # Forward pass
            ypred = [self.model(x) for x in self.xs]
            loss = sum((yout - ygt)**2 for ygt, yout in zip(self.ys, ypred))
            
            # Backward pass
            for p in self.model.parameters():
                p.grad = 0.0
            loss.backward()
            
            # Update weights
            for p in self.model.parameters():
                p.data += -learning_rate * p.grad
            
            # Calculate metrics
            y_true = [y for y in self.ys]
            y_pred = [y.data for y in ypred]
            
            mse = sum((yt - yp)**2 for yt, yp in zip(y_true, y_pred)) / len(self.ys)
            rmse = math.sqrt(mse)
            
            epsilon = 1e-8
            mape = sum(abs((yt - yp) / (yt + epsilon)) for yt, yp in zip(y_true, y_pred)) / len(self.ys)
            
            y_mean = sum(y_true) / len(y_true)
            ss_tot = sum((yt - y_mean)**2 for yt in y_true)
            ss_res = sum((yt - yp)**2 for yt, yp in zip(y_true, y_pred))
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # Store metrics
            losses.append(loss.data)
            rmses.append(rmse)
            mapes.append(mape)
            r2s.append(r2)
            
            # Store actual vs predicted for last epoch
            if epoch == epochs - 1:
                for x_orig, y_orig, y_pred_norm in zip(self.xs_original, self.ys_original, ypred):
                    if self.norm_constants['method'] == 'max':
                        y_pred_denorm = y_pred_norm.data * self.norm_constants['y_max']
                    else:
                        y_pred_denorm = y_pred_norm.data * (self.norm_constants['y_max'] - self.norm_constants['y_min']) + self.norm_constants['y_min']
                    
                    actual_vs_predicted.append({
                        'input': x_orig,
                        'actual': y_orig,
                        'predicted': y_pred_denorm
                    })
        
        self.training_history = {
            'losses': losses,
            'rmses': rmses,
            'mapes': mapes,
            'r2s': r2s,
            'learning_rate': learning_rate,
            'final_loss': losses[-1],
            'final_r2': r2s[-1]
        }
        
        self.actual_vs_predicted = actual_vs_predicted
        
        return self.training_history
    
    def save_model(self):
        # Prepare model data
        params = [p.data for p in self.model.parameters()]
        
        model_data = {
            'model_params': params,
            'architecture': self.params['architecture'],
            'input_dim': self.input_dim,
            'training_history': self.training_history
        }
        
        model_path = os.path.join(self.output_dir, self.params['model_filename'])
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        norm_path = os.path.join(self.output_dir, self.params['norm_filename'])
        with open(norm_path, 'w') as f:
            json.dump(self.norm_constants, f, indent=2)
        
        weights_path = os.path.join(self.output_dir, self.params['weights_filename'])
        self.save_weights_json(weights_path)
        
        csv_path = os.path.join(self.output_dir, 'actual_vs_predicted.csv')
        self.save_actual_vs_predicted_csv(csv_path)
        
        self._generate_plots()
        
        return model_path, norm_path, weights_path
    
    def save_weights_json(self, filepath):
        layers_data = self.model.get_all_weights_and_biases()
        
        json_data = {
            "model_info": {
                "input_dim": self.input_dim,
                "architecture": self.params['architecture'],
                "normalization": self.norm_constants,
                "training_info": {
                    "learning_rate": self.best_lr,
                    "final_loss": self.training_history['final_loss'],
                    "final_r2": self.training_history['final_r2']
                }
            },
            "layers": layers_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(json_data, f, indent=2)
    
    def save_actual_vs_predicted_csv(self, filepath):
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Input', 'Actual', 'Predicted', 'Error', 'Error_Percent'])
            
            for item in self.actual_vs_predicted:
                input_str = str(item['input'][0]) if len(item['input']) == 1 else str(item['input'])
                actual = item['actual']
                predicted = item['predicted']
                error = actual - predicted
                error_percent = (abs(error) / (abs(actual) + 1e-8)) * 100
                
                writer.writerow([input_str, actual, predicted, error, error_percent])
    
    def _generate_plots(self):
        if hasattr(self, 'lr_list') and hasattr(self, 'loss_list'):
            plt.figure(figsize=(10, 6))
            best_idx = np.argmin(self.loss_list)
            best_lr = self.lr_list[best_idx]
            best_loss = self.loss_list[best_idx]
            
            plt.plot(self.lr_list, self.loss_list, 'b-', linewidth=2)
            plt.scatter(best_lr, best_loss, color='red', s=100)
            plt.xscale('log')
            plt.xlabel('Learning Rate')
            plt.ylabel('Loss')
            plt.title('Learning Rate Finder')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'learning_rate_finder.png'), dpi=150)
            plt.close()
        
        if hasattr(self, 'training_history'):
            epochs = list(range(self.params['training_epochs']))
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            
            axes[0, 0].plot(epochs, self.training_history['losses'], color='blue', linewidth=2)
            axes[0, 0].set_xlabel('Epoch')
            axes[0, 0].set_ylabel('Loss')
            axes[0, 0].set_title('Training Loss')
            axes[0, 0].grid(True, alpha=0.3)
            
            axes[0, 1].plot(epochs, self.training_history['rmses'], color='green', linewidth=2)
            axes[0, 1].set_xlabel('Epoch')
            axes[0, 1].set_ylabel('RMSE')
            axes[0, 1].set_title('Root Mean Square Error')
            axes[0, 1].grid(True, alpha=0.3)
            
            axes[1, 0].plot(epochs, self.training_history['mapes'], color='orange', linewidth=2)
            axes[1, 0].set_xlabel('Epoch')
            axes[1, 0].set_ylabel('MAPE')
            axes[1, 0].set_title('Mean Absolute Percentage Error')
            axes[1, 0].grid(True, alpha=0.3)
            
            axes[1, 1].plot(epochs, self.training_history['r2s'], color='red', linewidth=2)
            axes[1, 1].set_xlabel('Epoch')
            axes[1, 1].set_ylabel('R2 Score')
            axes[1, 1].set_title('R2 Score')
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'training_metrics.png'), dpi=150)
            plt.close()
        
        if hasattr(self, 'actual_vs_predicted'):
            plt.figure(figsize=(10, 6))
            actuals = [item['actual'] for item in self.actual_vs_predicted]
            predictions = [item['predicted'] for item in self.actual_vs_predicted]
            
            plt.scatter(actuals, predictions, color='blue', alpha=0.6)
            
            # Add perfect prediction line
            min_val = min(min(actuals), min(predictions))
            max_val = max(max(actuals), max(predictions))
            plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction')
            
            plt.xlabel('Actual Values')
            plt.ylabel('Predicted Values')
            plt.title('Actual vs Predicted Values')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'actual_vs_predicted.png'), dpi=150)
            plt.close()
    
    def run_training(self):
        print("Starting neural network training...")
        print(f"Data points: {len(self.xs_original)}")
        print(f"Architecture: MLP({self.input_dim}, {self.params['architecture']})")
        print(f"Output directory: {self.output_dir}")
        print("-" * 50)
        
        print("Step 1: Normalizing data...")
        self.normalize_data()
        
        print("Step 2: Finding optimal learning rate...")
        best_lr = self.find_learning_rate()
        print(f"  Best learning rate: {best_lr:.6f}")
        
        print(f"Step 3: Training model ({self.params['training_epochs']} epochs)...")
        history = self.train(learning_rate=best_lr)
        print(f"  Final loss: {history['final_loss']:.6f}")
        print(f"  Final R2: {history['final_r2']:.6f}")
        
        print("Step 4: Saving model and results...")
        model_path, norm_path, weights_path = self.save_model()
        
        print("-" * 50)
        print("Training completed successfully!")
        print(f"Model saved: {model_path}")
        print(f"Normalization constants: {norm_path}")
        print(f"Weights JSON (for C++): {weights_path}")
        print(f"Output files in: {self.output_dir}")
        
        return model_path, norm_path, weights_path


class NeuralNetworkPredictor:
    
    def __init__(self, model_path=None, norm_path=None, weights_json_path=None):
        
        if weights_json_path:
            with open(weights_json_path, 'r') as f:
                self.json_data = json.load(f)
            
            self.input_dim = self.json_data['model_info']['input_dim']
            self.architecture = self.json_data['model_info']['architecture']
            self.norm_constants = self.json_data['model_info']['normalization']
            self.layers_data = self.json_data['layers']
            
            # Create model
            self.model = MLP(self.input_dim, self.architecture)
            
            # Load weights and biases from JSON data
            self._load_weights_from_json()
            
        elif model_path and norm_path:
            # Load from pickle file (legacy method)
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            with open(norm_path, 'r') as f:
                self.norm_constants = json.load(f)
            
            self.model = MLP(model_data['input_dim'], model_data['architecture'])
            
            # Load parameters
            params = self.model.parameters()
            for p, saved_p in zip(params, model_data['model_params']):
                p.data = saved_p
            
            self.training_history = model_data.get('training_history', {})
        else:
            raise ValueError("Either provide weights_json_path OR both model_path and norm_path")
    
    def _load_weights_from_json(self):
        for layer_idx, layer in enumerate(self.model.layers):
            json_layer = self.layers_data[layer_idx]
            
            json_weights = json_layer['w']  # [input_dim][neuron_count]
            json_biases = json_layer['b']   # [neuron_count]
            
            # Update each neuron in the layer
            for neuron_idx, neuron in enumerate(layer.neurons):
                # Update bias
                neuron.b.data = json_biases[neuron_idx]
                
                # Update weights
                for weight_idx, _ in enumerate(neuron.w):
                    # Note: json_weights[input_idx][neuron_idx]
                    neuron.w[weight_idx].data = json_weights[weight_idx][neuron_idx]
    
    def predict(self, x):
        if isinstance(x, (int, float)):
            x = [[x]]
        elif isinstance(x, list) and isinstance(x[0], (int, float)):
            x = [x]
        
        # Normalize input
        x_array = np.array(x, dtype=float)
        
        if self.norm_constants['method'] == 'max':
            x_norm = x_array / self.norm_constants['x_max']
        else:  # minmax
            x_min = np.array(self.norm_constants['x_min'])
            x_max = np.array(self.norm_constants['x_max'])
            x_norm = (x_array - x_min) / (x_max - x_min + 1e-8)
        
        predictions = []
        for xi in x_norm:
            pred_norm = self.model(xi.tolist())
            
            if self.norm_constants['method'] == 'max':
                pred = pred_norm.data * self.norm_constants['y_max']
            else:  # minmax
                pred = pred_norm.data * (self.norm_constants['y_max'] - self.norm_constants['y_min']) + self.norm_constants['y_min']
            
            predictions.append(pred)
        
        return predictions[0] if len(predictions) == 1 else predictions
    
    def evaluate(self, xs, ys):
        predictions = []
        actuals = []
        
        for x, y in zip(xs, ys):
            pred = self.predict(x)
            predictions.append(pred)
            actuals.append(y)
        
        # Calculate metrics
        predictions_np = np.array(predictions)
        actuals_np = np.array(actuals)
        
        mse = np.mean((predictions_np - actuals_np)**2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(predictions_np - actuals_np))
        mape = np.mean(np.abs((predictions_np - actuals_np) / (actuals_np + 1e-8))) * 100
        
        y_mean = np.mean(actuals_np)
        ss_tot = np.sum((actuals_np - y_mean)**2)
        ss_res = np.sum((actuals_np - predictions_np)**2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'r2': r2,
            'predictions': predictions,
            'actuals': actuals
        }
    
    def export_simple_json(self, filepath):
        layers_data = self.model.get_all_weights_and_biases()
        
        with open(filepath, 'w') as f:
            json.dump(layers_data, f, indent=2)


# Convenience functions for easy use
def create_and_train(xs, ys, output_dir='output', **kwargs):
    trainer = NeuralNetworkTrainer(xs, ys, output_dir)
    
    # Set any custom parameters
    for key, value in kwargs.items():
        if key in ['architecture', 'normalization_method', 'lr_finder_steps', 
                   'training_epochs', 'model_filename', 'norm_filename', 'weights_filename']:
            trainer.set_parameter(key, value)
    
    return trainer.run_training()


def load_and_predict(model_path=None, norm_path=None, weights_json_path=None, xs=None):
    predictor = NeuralNetworkPredictor(
        model_path=model_path,
        norm_path=norm_path,
        weights_json_path=weights_json_path
    )
    
    if xs is not None:
        return predictor.predict(xs)
    else:
        return predictor