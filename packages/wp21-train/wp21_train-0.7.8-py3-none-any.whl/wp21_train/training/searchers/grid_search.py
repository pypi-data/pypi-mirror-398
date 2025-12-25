from wp21_train.training.searchers.base_search import SearchBase
from wp21_train.utils.utility import _iter_param_grid

class GridSearch(SearchBase):
    def __init__(self, data):
        super().__init__(data)
        self._iter = _iter_param_grid(self.space)

    def next(self):
        try:
            return next(self._iter)
        except StopIteration:
            return None