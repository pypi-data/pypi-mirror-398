from typing import Tuple
import pytest
import tensorflow as tf
import torch
import os
from test_physics import make_project, bg_data, sig_data, cell_map, data_folder
from wp21_train.data import Sample


def mnist() -> Tuple[tuple, tuple, tuple]:
    (x_tr, y_tr), (x_te, y_te) = tf.keras.datasets.mnist.load_data()
    x_tr = x_tr.reshape(-1, 784).astype("float32") / 255.0
    x_te = x_te.reshape(-1, 784).astype("float32") / 255.0
    tf.random.set_seed(42)
    x_train, x_val = x_tr[:-5000], x_tr[-5000:]
    y_train, y_val = y_tr[:-5000], y_tr[-5000:]

    return (x_train, y_train), (x_val, y_val), (x_te, y_te)


class DataSet:
    def __init__(self):
        self.x_train = None
        self.y_train = None
        self.x_val = None
        self.y_val = None

    def load(self):
        (x_tr, y_tr), (x_va, y_va), _ = mnist()
        self.x_train = x_tr
        self.y_train = y_tr
        self.x_val = x_va
        self.y_val = y_va


class TorchDataSet:
    def __init__(self):
        self.x_train = None
        self.y_train = None
        self.x_val = None
        self.y_val = None

    def load(self):
        (x_tr, y_tr), (x_va, y_va), _ = mnist()
        self.x_train = torch.as_tensor(x_tr, dtype=torch.float32)
        self.y_train = torch.as_tensor(y_tr, dtype=torch.long)
        self.x_val = torch.as_tensor(x_va, dtype=torch.float32)
        self.y_val = torch.as_tensor(y_va, dtype=torch.long)

def test_get_sample_names(bg_data, sig_data, cell_map):
    project = make_project(bg_data, sig_data, cell_map)
    assert isinstance(project.get_sample_names('sig'), list)
    assert isinstance(project.get_sample_names('bg'), list)

    project = make_project(bg_data, sig_data, cell_map, sig_short="sig_test")
    assert project.get_sample_names('sig')[0] == 'sig_test'
    assert project.get_sample_names('bg')[0] is None

    project = make_project(bg_data, sig_data, cell_map, bg_short="bg_test")
    assert project.get_sample_names('sig')[0] is None 
    assert project.get_sample_names('bg')[0] == 'bg_test'

    project = make_project(bg_data, sig_data, cell_map, bg_short="bg_test", sig_short = "sig_test")
    assert project.get_sample_names('sig')[0] == 'sig_test'
    assert project.get_sample_names('bg')[0] == 'bg_test'
    

def test_sample():
    with pytest.raises(FileNotFoundError) as excinfo:
        Sample.from_ds_name("foldeR", "PhPy8EG_A14_ttbar_hdamp258p75_dil", 140, os.path.join(data_folder, "sample_mapping.json"))

    assert "foldeR" in str(excinfo.value)

