import os
import pickle as pkl
import neuralengine.config as cf
from itertools import chain
from ..tensor import Tensor, NoGrad, array
from .layers import Layer, Mode, Flatten, LSTM
from .optim import Optimizer
from .loss import Loss


class Model:
    """A class to build and train a neural network model.
    Allows for defining the model architecture, optimizer, loss function, and metrics.
    The model can be trained and evaluated.
    """

    def __init__(self, input_size: tuple | int, optimizer: Optimizer = None, loss: Loss = None, metrics=()):
        """
        @param input_size: Tuple or int, shape of input data samples (int if 1D).
        @param optimizer: Optimizer instance.
        @param loss: Loss instance.
        @param metrics: List/tuple of Metric or Loss instances or func(x, y) → dict[str, float | np.ndarray].
        """

        self.input_size = input_size

        if not isinstance(optimizer, Optimizer):
            raise ValueError("optimizer must be an instance of Optimizer class")
        self.optimizer = optimizer

        if not isinstance(loss, Loss):
            raise ValueError("loss must be an instance of Loss class")
        self.loss = loss

        self.metrics = metrics if isinstance(metrics, (list, tuple)) else (metrics,)


    def __call__(self, *layers: Layer) -> None:
        """
        Allows the model to be called with layers to build the model.
        @param layers: Variable number of Layer instances to add to the model.
        """
        self.build(*layers)


    def build(self, *layers: Layer) -> None:
        """
        Builds the model by adding layers.
        @param layers: Variable number of Layer instances to add to the model.
        """

        self.parameters, prevLayer = {}, None
        for i, layer in enumerate(layers):

            if not isinstance(layer, Layer):
                raise ValueError("All layers must be instances of Layer class")
            
            # If stacking LSTM layers, update input size and output selection
            if isinstance(layer, LSTM) and isinstance(prevLayer, LSTM):
                out_size = prevLayer.out_size
                if prevLayer.attention:
                    if prevLayer.enc_size: out_size += prevLayer.enc_size
                    else: out_size += prevLayer.out_size
                if prevLayer.bidirectional: out_size *= 2
                self.input_size = (*prevLayer.in_size[:-1], out_size)
                prevLayer.return_seq = True
                if not 0 in prevLayer.use_output:
                    if prevLayer.return_state: prevLayer.use_output = (0, 1, 2)
                    else: prevLayer.use_output = (0,)
            prevLayer = layer

            if layer.in_size is None:
                layer.in_size = self.input_size
            self.input_size = layer.out_size if hasattr(layer, 'out_size') else self.input_size
            if isinstance(layer, Flatten):
                self.input_size = int(cf.nu.prod(array(self.input_size)))

            self.parameters[f"layer_{i}"] = list(layer.parameters()) # Collect parameters from the layer
            
        self.layers = layers
        self.optimizer.parameters = list(chain.from_iterable(self.parameters.values()))


    @classmethod
    def load_model(cls, filepath: str) -> 'Model':
        """
        Loads the model from a file.
        @param filepath: Path to the file from which the model will be loaded.
        @return: Loaded Model instance.
        """
        filepath = filepath if filepath.endswith('.pkl') else filepath + '.pkl'
        with open(filepath, 'rb') as file:
            model = pkl.load(file)

        if not isinstance(model, cls):
            raise ValueError("Loaded object is not a Model instance")

        device = cf.get_device()
        for layer in model.layers:
            layer.to(device)
        return model


    def load_params(self, filepath: str) -> None:
        """
        Loads the model parameters from a file.
        @param filepath: Path to the file from which model parameters will be loaded.
        """
        filepath = filepath if filepath.endswith('.pkl') else filepath + '.pkl'
        with open(filepath, 'rb') as file:
            params = pkl.load(file)

        device = cf.get_device()
        for i in range(len(self.layers)):
            layer_old = self.parameters.get(f"layer_{i}", [])
            layer_new = params.get(f"layer_{i}", [])

            if len(layer_old) != len(layer_new): 
                print(f"Skipping layer_{i} parameter load due to mismatch.")
                continue

            for p_old, p_new in zip(layer_old, layer_new):
                if p_old.shape != p_new.shape:
                    print(f"Skipping parameter load due to shape mismatch: {p_old.shape} vs {p_new.shape}")
                    continue 
                p_old.data = p_new.to(device).data.copy()


    def save(self, filename: str, weights_only: bool = False) -> None:
        """
        Saves the model or model parameters to a file.
        @param filename: Name of the file where model will be saved.
        @param weights_only: If True, saves only weights; else saves entire model structure.
        """
        filename = filename if filename.endswith('.pkl') else filename + '.pkl'
        filepath = os.path.join(os.getcwd(), filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'wb') as file:
            if weights_only: pkl.dump(self.parameters, file)
            else: pkl.dump(self, file)


    def train(self, x, y, epochs: int = 10, batch_size: int = 64, seed: int = None, ckpt_interval: int = None):
        """
        Trains the model on data.
        @param x: Input data, shape (N, features)
        @param y: Target data, shape (N, target_features)
        @param epochs: Number of epochs
        @param batch_size: Batch size (None for full batch)
        @param seed: Seed for random shuffling
        @param ckpt_interval: Interval (in epochs) to save checkpoints
        """

        for layer in self.layers:
            layer.mode = Mode.TRAIN

        x, y = array(x), array(y)

        if batch_size is None:
            batch_size = x.shape[0]
        if batch_size <= 0 or batch_size > x.shape[0]:
            raise ValueError("batch_size must be a positive integer ≤ number of samples")

        for i in range(epochs):

            loss_val, metric_vals = 0, {}
            cf.nu.random.seed(seed)
            shuffle_indices = cf.nu.random.permutation(x.shape[0])
            x, y = x[shuffle_indices], y[shuffle_indices] # Shuffle data

            for j in range(0, x.shape[0], batch_size):
                x_batch = x[j:j + batch_size]
                y_batch = y[j:j + batch_size]

                # Forward pass
                for layer in self.layers:
                    x_batch = layer(x_batch)
                    # For stacked LSTM, pass outputs accordingly
                    if isinstance(layer, LSTM): x_batch = x_batch[layer.use_output[0]]
                    
                # Compute loss
                loss = self.loss(x_batch, y_batch)
                loss_val += self.loss.loss_val

                loss.backward() # Backward pass

                # Compute metrics
                for metric in self.metrics:
                    metric_val = metric(x_batch, y_batch)
                    if isinstance(metric, Loss):
                        key = metric.__class__.__name__
                        metric_vals[key] = metric_vals.get(key, 0.0) + metric.loss_val
                        continue
                    for key, value in metric_val.items():
                        if value is None: continue
                        metric_vals[key] = metric_vals.get(key, 0.0) + value

                # Update parameters
                self.optimizer.step()
                self.optimizer.reset_grad() # Reset gradients

            loss_val /= (x.shape[0] / batch_size) # Average loss over batches
            output_strs = [f"Epoch {i + 1}/{epochs}", f"Loss: {loss_val:.4f}"]

            for key, value in metric_vals.items():
                value /= (x.shape[0] / batch_size) # Average metric over batches
                if isinstance(value, (cf.nu.ndarray)) and value.ndim == 1:
                    value = value.mean(keepdims=False)
                output_strs.append(f"{key}: {value:.4f}")

            # Save checkpoint
            if ckpt_interval and (i + 1) % ckpt_interval == 0:
                self.save(f"checkpoints/model_epoch_{i + 1}.pkl", weights_only=True)
                output_strs.append("Checkpoint saved")

            print(*output_strs, sep=", ")


    def eval(self, x, y) -> Tensor:
        """
        Evaluates the model on data.
        @param x: Input data, shape (N, features)
        @param y: Target data, shape (N, target_features)
        @return: Output tensor after evaluation
        """

        for layer in self.layers:
            layer.mode = Mode.EVAL

        # Forward pass
        with NoGrad():
            z = x
            for layer in self.layers:
                z = layer(z)
                # For stacked LSTM, pass outputs accordingly
                if isinstance(layer, LSTM): z = z[layer.use_output[0]]

            self.loss(z, y) # Compute loss

        # Compute metrics
        cm = False
        for metric in self.metrics:
            metric(z, y)
            cm = metric.cm if hasattr(metric, 'cm') else cm

        print(f"Evaluation: (Loss) {self.loss}", *self.metrics, sep=", ")
        if cm is not False:
            print(f"Confusion Matrix:\n{cm}")
        return z