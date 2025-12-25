import os
import tensorflow as tf
from wp21_train.training.trainers.keras_base import KerasTrainerBase


class HGQTrainer(KerasTrainerBase):
    def save_model(self, model, meta_path, name):
        os.makedirs(meta_path, exist_ok=True)
        path = os.path.join(meta_path, name + ".keras")
        model.save(path)

    def compile(self, params):
        tf.keras.backend.clear_session()
        if "quantizer_bitwidth" in params.keys():
            bitwidth = params.get("quantizer_bitwidth")
            self.model = self.model_function(bitwidth=bitwidth)

        else:
            self.model = self.model_function()

        lr = params.get("lr")
        opt_name = params.get("optimiser")
        optimizer = self._make_optimizer(opt_name, lr)

        loss = params.get("loss")
        metrics = [params.get("metrics")]

        self.model.compile(optimizer=optimizer, loss=loss, metrics=metrics)

    def fit(self, params):
        epochs = params.get("epochs")
        batch_size = params.get("batch_size")

        history = self.model.fit(
            self.dataset.x_train,
            self.dataset.y_train,
            validation_data=(self.dataset.x_val, self.dataset.y_val),
            epochs=epochs,
            batch_size=batch_size,
            verbose=2,
            callbacks=[],
        )

        return history
