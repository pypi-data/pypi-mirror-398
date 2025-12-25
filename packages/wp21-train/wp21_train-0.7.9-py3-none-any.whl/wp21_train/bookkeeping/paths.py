class Paths:
    """
    Bookkeeping class for all paths
    """
    default_path = "/workspace/samples/resimulated_fex_truth_all_cell_data/"
    cellmap_path = "/workspace/samples/cell_map/CaloCells.root"

    @classmethod
    def get_sample_path(cls):
        return cls.default_path

    @classmethod
    def get_cellmap_path(cls):
        return cls.cellmap_path

