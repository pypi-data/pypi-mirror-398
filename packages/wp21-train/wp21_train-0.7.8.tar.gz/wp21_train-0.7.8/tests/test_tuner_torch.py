import os
import glob
import wp21_train as train
from test_model import torch_mlp
from test_data import *

def test_tuner_torch():
    test_dir  = os.path.dirname(__file__)
    test_file = os.path.join(test_dir, "test_config")

    ds = TorchDataSet()
    ds.load()
    
    trainer = train.training.trainers.TorchTrainer(test_file, ds, torch_mlp)
    tune = train.training.LossTuner("hat", trainer)
    tune.run()
    
    meta_dir = os.path.join(test_dir, "meta")
    out_dir = os.path.join(test_dir, "out")
    eval = train.training.Evaluator(tune.trials, trainer, meta_path = meta_dir, out_path = out_dir)
    eval.save_info(verbose = 3)  

    out_files = [f for f in os.listdir(out_dir) if os.path.isfile(os.path.join(out_dir, f))]

    # Configs of top 5
    assert len(out_files) == 5, f"Expected 5 files in {out_dir}, found {len(out_files)}: {out_files}"

    out_file = os.path.join(out_dir, "config_0")
    in_data, in_meta = train.savers.json_adapter(test_file).read_data()
    out_data, out_meta = train.savers.json_adapter(out_file).read_data()

    # Same config
    assert set(in_data["data"].keys()) == set(out_data["data"].keys()), "Data keys differ between in and out config"
    assert set(in_meta["meta"].keys()) == set(out_meta["meta"].keys()), "Meta keys differ between in and out config"

    # Loss history
    history_path = os.path.join(meta_dir, "history.json")
    assert os.path.exists(history_path), f"{history_path} not found"

    # Models
    onnx_files = glob.glob(os.path.join(meta_dir, "*.onnx"))
    assert len(onnx_files) == 6, f"Expected 6 .onnx files in {meta_dir}, found {len(onnx_files)}: {onnx_files}"
