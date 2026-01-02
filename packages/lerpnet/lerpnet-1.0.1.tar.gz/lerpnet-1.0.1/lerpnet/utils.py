from .trainer import NeuralNetworkTrainer
from .predictor import NeuralNetworkPredictor

def create_and_train(xs, ys, output_dir='output', **kwargs):
    trainer = NeuralNetworkTrainer(xs, ys, output_dir)
    for k, v in kwargs.items():
        trainer.set_parameter(k, v)
    return trainer.run_training()

def load_and_predict(model_path=None, norm_path=None, weights_json_path=None, xs=None):
    predictor = NeuralNetworkPredictor(
        model_path=model_path,
        norm_path=norm_path,
        weights_json_path=weights_json_path
    )
    return predictor.predict(xs) if xs is not None else predictor
