from ...bookkeeping.keys import GEPCellKeys, TauEFEXKeys

class ClusteringConfig:
    def __init__(self, **kwargs):
        self.cluster_r_phi = kwargs.get("cluster_r_phi", 0.15)
        self.cluster_r_eta = kwargs.get("cluster_r_eta", 0.15)
        self.sampling_layers = kwargs.get("sampling_layers", None)

        self.other_keys = kwargs.get("other_keys", self.get_other_keys())
        self.this_keys = kwargs.get("this_keys", self.get_this_keys())

    def get_this_keys(self):
        """
        Set the keys (names of branches) of the cells.
        Can be overridden in inheriting class.
        """
        return GEPCellKeys()

    def get_other_keys(self):
        """
        Set the keys (names of branches) of the seed information in the data.
        Must be implemented by inheriting class.
        """
        raise NotImplementedError("Must implement get_other_keys in inheriting class")

    def update(self, **kwargs):
        self.cluster_r_phi = kwargs.get("cluster_r_phi", self.cluster_r_phi)
        self.cluster_r_eta = kwargs.get("cluster_r_eta", self.cluster_r_eta)


class ClusteringConfigEFEX(ClusteringConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_other_keys(self):
        return TauEFEXKeys


