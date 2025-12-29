import neuralengine.config as cf
from ..tensor import array


class Metric:
    """Base class for all metrics."""
    def __init__(self):
        self.metric_val = None

    def __call__(self, z, y, *args, **kwargs):
        """ Calls the metric compute method with the provided predictions and targets.
        @param z: Predictions (logits or outputs of the model).
        @param y: Ground truth labels or targets.
        """
        z = z if isinstance(z, cf.nu.ndarray) else array(z)
        y = y if isinstance(y, cf.nu.ndarray) else array(y)
        metric_val = self.compute(z, y, *args, **kwargs)

        if not isinstance(metric_val, dict):
            raise ValueError("Metric compute method must return a dictionary.")
        
        self.metric_val = metric_val
        return self.metric_val

    def __repr__(self) -> str:
        """ Returns a string representation of the metric with its value if computed. """
        if self.metric_val is not None:

            metric_str = ""
            for key, value in self.metric_val.items():
                if value is None: continue
                if isinstance(value, (cf.nu.ndarray)) and value.ndim == 1:
                    value = value.mean(keepdims=False)
                metric_str += f"{key}: {value:.4f}, "
            return metric_str[:-2]
        
        else:
            return "No metric computed yet."


class RMSE(Metric):
    """Root Mean Squared Error metric."""
    def __init__(self):
        super().__init__()

    def compute(self, z, y):
        # mse = 1/N Σ (z - y)²
        mse = cf.nu.mean((z - y) ** 2)
        # rmse = √(mse)
        rmse = cf.nu.sqrt(mse)
        return {"RMSE": rmse}
    

class R2(Metric):
    """R2 Score metric."""
    def __init__(self):
        super().__init__()

    def compute(self, z, y):
        # ss_total = Σ (y - μ_y)²
        ss_total = cf.nu.sum((y - cf.nu.mean(y)) ** 2)
        # ss_residual = Σ (z - y)²
        ss_residual = cf.nu.sum((z - y) ** 2)
        # R² = 1 - (ss_residual / ss_total)
        r2 = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
        return {"R2 Score": r2}


class ClassificationMetrics(Metric):
    """Classification metrics: Accuracy, Precision, Recall, F1 Score, Confusion Matrix."""
    def __init__(self, num_classes: int = None, acc: bool = True, prec: bool = False, rec: bool = False, f1: bool = False, cm: bool = False):
        """
        @param num_classes: Number of classes for classification tasks.
        @param acc: Whether to compute accuracy.
        @param prec: Whether to compute precision.
        @param rec: Whether to compute recall.
        @param f1: Whether to compute F1 score.
        @param cm: Whether to compute confusion matrix. Only for evaluation mode.
        """
        super().__init__()
        self.num_classes = num_classes
        self.acc = acc
        self.prec = prec
        self.rec = rec
        self.f1 = f1
        self.cm = cm

    def compute(self, z, y):
        if self.num_classes is None:
            self.num_classes = max(z.shape[-1], y.shape[-1])
        # Convert logits/one-hot to class indices
        z = cf.nu.argmax(z, axis=-1)
        y = cf.nu.argmax(y, axis=-1)

        # Confusion matrix
        cm = cf.nu.zeros((self.num_classes, self.num_classes), dtype=cf.nu.int32)
        cf.nu.add.at(cm, (y, z), 1)
        # TP, FP, FN
        TP = cf.nu.diag(cm)
        FP = cf.nu.sum(cm, axis=0) - TP
        FN = cf.nu.sum(cm, axis=1) - TP

        acc, prec, rec, f1 = None, None, None, None
        if self.acc:
            # Accuracy = trace(cm) / sum(cm)
            acc = cf.nu.trace(cm) / cf.nu.sum(cm) if cf.nu.sum(cm) > 0 else 0
        if self.prec:
            # Precision = TP / (TP + FP)
            prec = cf.nu.zeros_like(TP, dtype=cf.nu.float32)
            cf.nu.divide(TP, TP + FP, out=prec, where=(TP + FP) != 0)
        if self.rec:
            # Recall = TP / (TP + FN)
            rec = cf.nu.zeros_like(TP, dtype=cf.nu.float32)
            cf.nu.divide(TP, TP + FN, out=rec, where=(TP + FN) != 0)
        if self.f1:
            # F1 = 2 * Precision * Recall / (Precision + Recall)
            f1 = cf.nu.zeros_like(TP, dtype=cf.nu.float32)
            cf.nu.divide(2 * prec * rec, prec + rec, out=f1, where=(prec + rec) != 0)
        if self.cm is not False:
            self.cm = cm

        return {
            "Accuracy": acc,
            "Precision": prec,
            "Recall": rec,
            "F1 Score": f1
        }