import os, json
from dataclasses import asdict
from wp21_train.savers.json_adapter import json_adapter
from wp21_train.utils.utility import _merge_missing

class Evaluator:
    def __init__(self, TrialRecord, trainer, meta_path, out_path):
        sorted_trials = sorted(TrialRecord, key=lambda r: r.score.score, reverse=False)
        self.trials = sorted_trials
        self.trainer = trainer
        self.meta_path = meta_path
        self.out_path = out_path

    def save_models(self):
        for i, trial in enumerate(self.trials):
            self.trainer.save_model(trial.model, self.meta_path, f"model_{i}")
    
    def save_loss(self, trials):
        os.makedirs(self.meta_path, exist_ok=True)
        file_path  = os.path.join(self.meta_path, "history.json")

        models = []
        for i, tr in enumerate(trials):
            hist = getattr(tr, "history", {}) or {}
            loss = list(hist.get("loss", []))
            val  = list(hist.get("val_loss", []))

            n = max(len(loss), len(val))
            while len(loss) < n: loss.append(None)
            while len(val)  < n: val.append(None)

            models.append({
                "name": f"model_{i}",
                "loss": loss,
                "val_loss": val,
                "params": getattr(tr, "params"),
                "score": asdict(getattr(tr, "score")),
            })
        
        with open(file_path, "w") as f:
            json.dump(models, f, indent=2)

    def dump_config_json(self):
        os.makedirs(self.out_path, exist_ok=True)

        top = self.trials[:5]
        for i, trial in enumerate(top):
            config_path = os.path.join(self.out_path, f"config_{i}")

            params = dict(trial.params)
            params = _merge_missing(params, self.trainer.data)
            json_adapter(config_path, params, self.trainer.meta).write_data()

    def save_info(self, verbose=1):
        if verbose == 1:
            self.save_loss(self.trials[:5])
            self.dump_config_json()
        
        if verbose == 2:
            self.save_loss(self.trials)
            self.dump_config_json()

        if verbose == 3:
            self.save_loss(self.trials)
            self.dump_config_json()
            self.save_models()
