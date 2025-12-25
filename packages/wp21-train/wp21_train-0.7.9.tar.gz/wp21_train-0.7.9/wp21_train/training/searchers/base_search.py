from wp21_train.utils.utility import _grid_size

class SearchBase:
    def __init__(self, data):
        self.space = dict(data)
        self.total = _grid_size(self.space)

    def next(self):
        raise NotImplementedError