from dataclasses import dataclass, field, InitVar
from typing import Any, Dict, List
from wp21_train.training.searchers.grid_search import GridSearch
from wp21_train.training.searchers.random_search import RandomSearch
from wp21_train.project import PerformanceSummary

@dataclass
class ScoreBase:
    score: float = field(init=False)


@dataclass
class LossScore(ScoreBase):
    loss_score: InitVar[float]

    def __post_init__(self, loss_score):
        self.score = loss_score

@dataclass 
class PhysicsScore(ScoreBase):
    performance: List[PerformanceSummary]
    def __post_init__(self):
        self.score = -self.performance[0].rate

@dataclass
class TrialRecord:
    params: Dict[str, Any]
    score: ScoreBase
    history: Dict[str, List[float]]
    model: List[Any]

class TunerBase:
    def __init__(self, mode, trainer):
        self.trials: List[TrialRecord] = []

        if mode == "qat":
            self.data = trainer.data
            num_trials = int(trainer.meta["quantizer_trials"])
        else:
            self.data = self._ignore_quant(trainer.data)
            num_trials = int(trainer.meta["trials"])

        search = trainer.meta.get("search")
        if search == "grid":
            self.strategy = GridSearch(self.data)
        elif search == "random":
            self.strategy = RandomSearch(self.data, num_trials=num_trials, seed=42)

        self.trainer = trainer
        self.exhausted = False

    def prepare_model_parameters(self):
        if self.exhausted:
            return False
        params = self.strategy.next()
        if params is None:
            self.exhausted = True
            return False

        self.params = params
        return True

    def run(self):
        while self.prepare_model_parameters():
            self._run_once()

    def _run_once(self):
        """
        Implement a fit of the model using the currently
        selected hyperparameters (self.params) and extend the
        list of trials (self.trials) with relevant information.
        Must be implemented by inheriting classes.
        """
        raise NotImplementedError("Tuner must implement _run_once")

    @staticmethod
    def _ignore_quant(d):
        return {k: v for k, v in d.items() if "quantizer" not in k.lower()}


class LossTuner(TunerBase):
    def _run_once(self):
        self.trainer.compile(self.params)
        history = self.trainer.fit(self.params)

        hist = {
            "loss": history.history.get("loss"),
            "val_loss": history.history.get("val_loss"),
        }

        rec = TrialRecord(
            params=self.params,
            score=LossScore(hist["loss"][-1]),
            history=hist,
            model=self.trainer.model,
        )
        self.trials.append(rec)


class PhysicsTuner(TunerBase):
    def _run_once(self):
        self.trainer.compile(self.params)
        history = self.trainer.fit(self.params)

        hist = {"loss": history.history.get("loss"), "val_loss": history.history.get("val_loss")}

        rec = TrialRecord(
            params = self.params,
            score = self.compute_physics_score(self.trainer.model, self.params),
            history = hist,
            model = self.trainer.model,
        )
        self.trials.append(rec)

    def compute_physics_score(self, model, params):
        raise NotImplementedError("compute_physics_score must be implemented in your project")



