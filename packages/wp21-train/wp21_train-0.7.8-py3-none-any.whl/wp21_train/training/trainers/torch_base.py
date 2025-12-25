import os
import torch
import torch.nn as nn
from wp21_train.training.trainers.base import TrainerBase

class TorchTrainerBase(TrainerBase):
    backend = "torch"

    def get_weights(self):
        return self.model.state_dict()

    def save_model(self, model, meta_path, name):
        os.makedirs(meta_path, exist_ok=True)
        path = os.path.join(meta_path, name + ".onnx")
        device = next(model.parameters()).device
        model.eval()
        input_tensor = self.dataset.x_train[:1].contiguous().to(device)
        torch.onnx.export(model, input_tensor, path, opset_version=17)

    @staticmethod
    def _make_optimiser(model, name, lr):
        if name in ("adam", "adamw"):
            opt_cls = torch.optim.AdamW if name == "adamw" else torch.optim.Adam
            return opt_cls(params = model.parameters(), lr=lr)
        if name == "sgd":
            return torch.optim.SGD(params = model.parameters(), lr=lr, momentum=0.9)
        
        return torch.optim.Adam(params = model.parameters(), lr=lr)
    
    @staticmethod
    def define_loss(loss):
        if loss == "sparse_categorical_crossentropy":
            crit = nn.CrossEntropyLoss()
            return crit, torch.long
        if loss == "bce": 
            crit = nn.BCEWithLogitsLoss()
            return crit, torch.float32
        if loss == "mse": 
            crit = nn.MSELoss()
            return crit, torch.float32