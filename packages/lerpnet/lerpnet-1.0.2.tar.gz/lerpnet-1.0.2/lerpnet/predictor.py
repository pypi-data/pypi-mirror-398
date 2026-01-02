import json, pickle
import numpy as np
from .mlp import MLP

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
