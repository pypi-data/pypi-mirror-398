from wp21_train.training.searchers.base_search import SearchBase
from wp21_train.utils.utility import _params_at
from wp21_train.utils.logger import log_message
import random


class RandomSearch(SearchBase):
    def __init__(self, data, num_trials: int, seed: int = 42):
        super().__init__(data)

        if (num_trials > self.total) and (self.total > 1):
            raise ValueError(
                f"num_trials ({num_trials}) exceeds grid size ({self.total})."
            )

        self._rng = random.Random(seed)
        self._indices = list(range(self.total))
        self._rng.shuffle(self._indices)
        self._indices = self._indices[:num_trials]
        self._pos = 0

    def next(self):
        if self._pos >= len(self._indices):
            return None
        idx = self._indices[self._pos]
        self._pos += 1
        return _params_at(self.space, idx)
