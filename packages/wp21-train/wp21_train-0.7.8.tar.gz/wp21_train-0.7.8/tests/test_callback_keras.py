#This test requires a Keras installation (preferably to happen within the container)
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.datasets import mnist
from tensorflow.keras.callbacks import Callback
from wp21_train.callbacks.base_callback import base_callback

import os

class customCallback(Callback, base_callback):
    def __init__(self, project_name, notes = ""):
        Callback     .__init__(self)
        base_callback.__init__(self, project_name, notes)

    def on_train_begin(self, logs = None):
        base_callback.on_train_begin(self, logs)

    def on_train_end(self, logs = None):
        base_callback.on_train_end(self, logs)

def test_callback_keras():

    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train = x_train.astype('float32') / 255.0
    x_test  = x_test .astype('float32') / 255.0
    x_train = x_train[..., None]
    x_test  = x_test[..., None]

    model = models.Sequential([
        layers.Input(shape=(28,28,1)),
        layers.Conv2D(16,3, activation='relu'),
        layers.MaxPooling2D(),
        layers.Flatten(),
        layers.Dense(10, activation='softmax')])

    model.compile(optimizer='adam',
                  loss     ='sparse_categorical_crossentropy',
                  metrics  =['accuracy'])

    my_callback = customCallback("mnist_test","Testing the wp21_train callback")

    model.fit(
        x_train, y_train,
        epochs = 10,
        batch_size = 64,
        validation_split=0.1,
        callbacks=[my_callback])

    #print(my_callback._meta_data)
    assert my_callback._meta_data, "No meta-data have been produced from training"
    
    from wp21_train.savers.json_adapter import json_adapter
    from wp21_train.savers.root_adapter import root_adapter

    json_saver = json_adapter("train_data", my_callback._data, my_callback._meta_data)

    my_data = {}
    my_meta = {}
    my_data['train0'] = my_callback._data
    my_meta['train0'] = my_callback._meta_data

    root_saver = root_adapter("train_data", my_data, my_meta)

    json_saver.write_data()
    root_saver.write_data()

    assert os.path.isfile('train_data.json'), "JSON file not produced"
    assert os.path.isfile("train_data.root"), "ROOT file not produced"
