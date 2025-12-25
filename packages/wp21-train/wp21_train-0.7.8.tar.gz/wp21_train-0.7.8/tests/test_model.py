from torch import nn
import tensorflow as tf

from HGQ.utils.utils import (
    get_default_paq_conf,
    get_default_kq_conf,
    set_default_paq_conf,
    set_default_kq_conf,
)
from HGQ.layers import HDense, HQuantize


def keras_mlp():
    inputs = tf.keras.Input(shape=(784,), name="pixels")
    x = tf.keras.layers.Dense(128, activation="relu", name="hidden")(inputs)
    logits = tf.keras.layers.Dense(10, name="logits")(x)
    outputs = tf.keras.layers.Activation("softmax", name="softmax")(logits)
    return tf.keras.Model(inputs, outputs, name="mnist_float")


class TorchMLP(nn.Module):
    def __init__(self, in_dim=784, hidden=128, out_dim=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )

    def forward(self, x):
        return self.net(x)


def torch_mlp(**kwargs):
    return TorchMLP(**kwargs)


def hgq_mlp(bitwidth=16, beta=0):
    paq_conf = dict(get_default_paq_conf())
    kq_conf = dict(get_default_kq_conf())

    paq_conf["init_bw"] = bitwidth
    kq_conf["init_bw"] = bitwidth
    paq_conf["trainable"] = False
    kq_conf["trainable"] = False
    paq_conf["regularizer"] = None
    kq_conf["regularizer"] = None

    set_default_paq_conf(paq_conf)
    set_default_kq_conf(kq_conf)

    inputs = tf.keras.Input(shape=(784,))
    x = HQuantize(beta=beta)(inputs)
    # x = inputs
    x = HDense(128, activation="relu", beta=beta)(x)
    logits = HDense(10, beta=beta)(x)
    outputs = tf.keras.layers.Activation("softmax")(logits)
    return tf.keras.Model(inputs, outputs)
