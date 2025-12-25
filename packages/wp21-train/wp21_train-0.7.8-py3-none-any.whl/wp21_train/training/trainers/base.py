from abc import ABC, abstractmethod
from wp21_train.savers.json_adapter import json_adapter

class TrainerBase(ABC):
    backend = None 

    def __init__(self, config, dataset, model_function, **kwargs):
        data, meta = json_adapter(config).read_data()
        self.meta = meta["meta"]
        self.data = data["data"]
        self.dataset = dataset
        self.model_function = model_function
        self.model = None
        self.cfg = dict(kwargs)

    @abstractmethod
    def compile(self, params):
        raise NotImplementedError

    @abstractmethod
    def fit(self, params):
        raise NotImplementedError

    @abstractmethod
    def save_model(self, weights, name):
        raise NotImplementedError