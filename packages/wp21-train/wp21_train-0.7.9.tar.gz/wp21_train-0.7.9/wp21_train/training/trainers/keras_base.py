import os, tf2onnx
import tensorflow as tf
from wp21_train.training.trainers.base import TrainerBase


class KerasTrainerBase(TrainerBase):
    backend = "keras"

    def save_model(self, model, meta_path, name):
        os.makedirs(meta_path, exist_ok=True)
        path = os.path.join(meta_path, name + ".onnx")
        tf2onnx.convert.from_keras(model, opset=17, output_path=path)

    @staticmethod
    def _make_optimizer(name, lr):
        if name in ("adam", "adamw"):
            opt_cls = (
                tf.keras.optimizers.AdamW
                if name == "adamw"
                else tf.keras.optimizers.Adam
            )
            return opt_cls(learning_rate=lr)
        if name == "sgd":
            return tf.keras.optimizers.SGD(learning_rate=lr, momentum=0.9)

        return tf.keras.optimizers.Adam(learning_rate=lr)
