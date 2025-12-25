from wp21_train.utils.version import __version__
import time

class base_callback:

    def __init__(self, project_name: str, extra_notes: str = ""):
        self._data      = {}
        self._meta_data = {}
        self._meta_data['project_name']  = project_name
        self._meta_data['project_notes'] = extra_notes
        self._meta_data['train_date']    = int(time.time())
        self._meta_data['train_start']   = None
        self._meta_data['train_end']     = None

    def on_train_begin(self, logs: dict = None):
        self._meta_data['train_start'] = time.time()

    def on_train_end(self, logs: dict = None):
        self._meta_data['train_end']  = time.time()
        self._meta_data['total_time'] = self._meta_data['train_end'] - self._meta_data['train_start']

    def on_epoch_begin(self, epoch: int, logs: dict = None):
        pass

    def on_epoch_end(self, epoch: int, logs: dict = None):
        pass

    def on_train_batch_begin(self, batch: int, logs: dict = None):
        pass

    def on_train_batch_end(self, batch: int, logs: dict = None):
        pass

    def on_test_begin(self, logs: dict = None):
        pass

    def on_test_end(self, logs: dict = None):
        pass

    def on_test_batch_begin(self, batch: int, logs: dict = None):
        pass

    def on_test_batch_end(self, batch: int, logs: dict = None):
        pass

    def on_predict_begin(self, logs: dict = None):
        pass

    def on_predict_end(self, logs: dict = None):
        pass

    def on_predict_batch_begin(self, batch: int, logs: dict = None):
        pass

    def on_predict_batch_end(self, batch: int, logs: dict = None):
        pass
