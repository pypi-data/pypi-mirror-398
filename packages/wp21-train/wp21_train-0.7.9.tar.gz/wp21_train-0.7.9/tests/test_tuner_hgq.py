import os
import glob
from test_model import hgq_mlp
from test_data import *
import wp21_train as train


def test_tuner_hgq():
    test_dir = os.path.dirname(__file__)
    test_file = os.path.join(test_dir, "test_config")

    ds = DataSet()
    ds.load()

    trainer = train.training.trainers.HGQTrainer(test_file, ds, hgq_mlp)
    tune = train.training.LossTuner("hat", trainer)
    tune.run()

    meta_dir = os.path.join(test_dir, "meta")
    out_dir = os.path.join(test_dir, "out")
    eval = train.training.Evaluator(
        tune.trials, trainer, meta_path=meta_dir, out_path=out_dir
    )
    eval.save_info(verbose=3)

    out_files = [
        f for f in os.listdir(out_dir) if os.path.isfile(os.path.join(out_dir, f))
    ]

    # Configs of top 5
    assert (
        len(out_files) == 5
    ), f"Expected 5 files in {out_dir}, found {len(out_files)}: {out_files}"

    out_file = os.path.join(out_dir, "config_0")
    in_data, in_meta = train.savers.json_adapter(test_file).read_data()
    out_data, out_meta = train.savers.json_adapter(out_file).read_data()

    # Same config
    assert set(in_data["data"].keys()) == set(
        out_data["data"].keys()
    ), "Data keys differ between in and out config"
    assert set(in_meta["meta"].keys()) == set(
        out_meta["meta"].keys()
    ), "Meta keys differ between in and out config"

    # Loss history
    history_path = os.path.join(meta_dir, "history.json")
    assert os.path.exists(history_path), f"{history_path} not found"

    # Models
    keras_files = glob.glob(os.path.join(meta_dir, "*.keras"))
    assert (
        len(keras_files) == 6
    ), f"Expected 6 .keras files in {meta_dir}, found {len(keras_files)}: {keras_files}"

    # ---------------------QAT--------------------
    # start qat training with one of the configs from the hat
    test_file_qat = out_file

    trainer_qat = train.training.trainers.HGQTrainer(test_file_qat, ds, hgq_mlp)
    tune_qat = train.training.LossTuner("qat", trainer_qat)
    tune_qat.run()

    meta_dir_qat = os.path.join(test_dir, "meta_qat")
    out_dir_qat = os.path.join(test_dir, "out_qat")
    eval_qat = train.training.Evaluator(
        tune_qat.trials, trainer_qat, meta_path=meta_dir_qat, out_path=out_dir_qat
    )
    eval_qat.save_info(verbose=3)

    out_files_qat = [
        f
        for f in os.listdir(out_dir_qat)
        if os.path.isfile(os.path.join(out_dir_qat, f))
    ]

    # Should be 3 files
    assert (
        len(out_files_qat) == 3
    ), f"Expected 3 files in {out_dir_qat}, found {len(out_files_qat)}: {out_files_qat}"

    out_file_qat = os.path.join(out_dir_qat, "config_0")
    in_data_qat, in_meta_qat = train.savers.json_adapter(test_file_qat).read_data()
    out_data_qat, out_meta_qat = train.savers.json_adapter(out_file_qat).read_data()

    # Same config
    assert set(in_data_qat["data"].keys()) == set(
        out_data_qat["data"].keys()
    ), "Data keys differ between in and out config"
    assert set(in_meta_qat["meta"].keys()) == set(
        out_meta_qat["meta"].keys()
    ), "Meta keys differ between in and out config"

    # Loss history
    history_path_qat = os.path.join(meta_dir_qat, "history.json")
    assert os.path.exists(history_path_qat), f"{history_path_qat} not found"

    # Models
    keras_files_qat = glob.glob(os.path.join(meta_dir_qat, "*.keras"))
    assert (
        len(keras_files_qat) == 3
    ), f"Expected 3 .keras files in {meta_dir_qat}, found {len(keras_files_qat)}: {keras_files_qat}"
