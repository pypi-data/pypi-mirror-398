# __init__.py

from wp21_train.utils.version import __version__
from .base import TrainerBase
from .hgq_trainer import HGQTrainer

__all__ = [
    "TrainerBase",
    "KerasTrainerBase",
    "TorchTrainerBase",
    "KerasTrainer",
    "TorchTrainer",
    "__version__",
    "HGQTrainer",
]

def __getattr__(name):
    if name in ("KerasTrainerBase", "KerasTrainer"):
        try:
            from .keras_base    import KerasTrainerBase
            from .keras_trainer import KerasTrainer
        except ImportError as e:
            raise ImportError("Keras trainers require Tensorflow. Install with: pip install 'wp21_train[tensorflow]'") from e
        return {"KerasTrainerBase": KerasTrainerBase, "KerasTrainer": KerasTrainer}[name]

    if name in ("TorchTrainerBase", "TorchTrainer"):
        try:
            from .torch_base    import TorchTrainerBase
            from .torch_trainer import TorchTrainer
        except ImportError as e:
            raise ImportError("Torch trainers require pyTorch. Install with: pip install 'wp21_train[pytorch]'") from e
        return {"TorchTrainerBase": TorchTrainerBase, "TorchTrainer": TorchTrainer}[name]

    raise AttributeError(f"module {__name__} has no attribute {name}")
