import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader
from types import SimpleNamespace
from wp21_train.training.trainers.torch_base import TorchTrainerBase

class TorchTrainer(TorchTrainerBase):
    def compile(self, params):
        self.model = self.model_function()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def fit(self, params):
        lr = params.get("lr")
        opt_name = params.get("optimiser").lower()
        optimiser = self._make_optimiser(self.model, opt_name, lr)

        batch_size = params.get("batch_size")
        epochs = params.get("epochs")

        train = DataLoader(TensorDataset(self.dataset.x_train, self.dataset.y_train), batch_size=batch_size, shuffle=True)
        val   = DataLoader(TensorDataset(self.dataset.x_val, self.dataset.y_val), batch_size=batch_size)

        loss_fn, target_dtype = self.define_loss(params.get("loss").lower())
        history = {"loss": [], "val_loss": []}

        for _ in range(epochs):
            self.model.train()
            t_sum = t_num = 0
            for xb, yb in train:
                xb = xb.to(self.device) 
                yb = yb.to(self.device, dtype=target_dtype)

                optimiser.zero_grad()
                loss = loss_fn(self.model(xb), yb)
                loss.backward(); optimiser.step()

                t_sum += loss.item() * xb.size(0); t_num += xb.size(0)
            history["loss"].append(t_sum / t_num)

            self.model.eval()
            v_sum = v_num = 0
            with torch.no_grad():
                for xb, yb in val:
                    xb = xb.to(self.device)
                    yb = yb.to(self.device, dtype=target_dtype)
                    v_loss = loss_fn(self.model(xb), yb)
                    v_sum += v_loss.item() * xb.size(0); v_num += xb.size(0)
            history["val_loss"].append(v_sum / v_num)

        return SimpleNamespace(history=history)