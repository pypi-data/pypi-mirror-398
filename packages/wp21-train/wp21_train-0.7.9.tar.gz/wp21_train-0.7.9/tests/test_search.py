import wp21_train as train
import os


def test_base_search():
    test_dir = os.path.dirname(__file__)
    test_file = os.path.join(test_dir, "test_config")
    data, meta = train.savers.json_adapter(test_file).read_data()

    data = data["data"]
    data = {k: v for k, v in data.items() if "quantizer" not in k.lower()}
    base_search = train.training.searchers.SearchBase(data)

    assert base_search.total == (
        len(data["lr"]) * len(data["batch_size"]) * len(data["epochs"])
    ), "Grid size does not match"

    def collect_combos(searcher):
        keys = tuple(searcher.space.keys())
        combos = []
        while True:
            p = searcher.next()
            if p is None:
                break
            combos.append(tuple(p[k] for k in keys))
        return combos

    grid_search = train.training.searchers.GridSearch(data)
    combos = collect_combos(grid_search)

    assert (
        len(combos) == grid_search.total
    ), f"expected {grid_search.total}, got {len(combos)}"
    assert len(set(combos)) == len(combos), "Duplicate grid combination found"

    trials = int(meta["meta"]["trials"])
    random_search = train.training.searchers.RandomSearch(data, trials)
    rcombos = collect_combos(random_search)

    assert len(rcombos) == trials, f"expected {trials}, got {len(rcombos)}"
    assert len(set(rcombos)) == len(rcombos), "Duplicate random combination found"
