from .keys import ETEtaPhiKeys, extend_keys
from .keys import CombineDestKeys

class ClusterKeys(ETEtaPhiKeys):
    """
    Base class for keys of cluster-based discriminant. Assuming sum, phi, eta are always required
    """
    def __init__(self, data=None, **kwargs):
        super().__init__(data, [["clus_sum", "clus_eta", "clus_phi"]], **kwargs)

# TODO: pass the target keys to extend_keys as well, so that they don't have to be provided in the constructor
@extend_keys(['sum_core', 'sum_env', 'isol'])
class ClusWithIsolationKeys(ETEtaPhiKeys):
    """
    Class for clusters in which the central energy deposition is isolated
    """
    def __init__(self, data=None, **kwargs):
#        super().___init__(data, [[ClusterKeys()[k] for k in ["et", "eta", "phi"]] + ["clus_sum_core", "clus_sum_env", "clus_isol"]])
        super().__init__(data, [CombineDestKeys(data, [ClusterKeys]).all_key_values + ["clus_sum_core", "clus_sum_env", "clus_isol"]])
