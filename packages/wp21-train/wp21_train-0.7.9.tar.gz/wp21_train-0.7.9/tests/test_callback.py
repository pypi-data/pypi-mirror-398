import wp21_train as train
import os

def test_callback_standalone():
    callback = train.callbacks.base_callback('my_test')
    callback.on_train_begin()
    callback.on_train_end()

    assert callback._meta_data, "Meta-data haven't been produced"
