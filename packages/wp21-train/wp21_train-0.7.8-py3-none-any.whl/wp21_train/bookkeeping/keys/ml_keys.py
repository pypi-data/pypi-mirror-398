from .cluster_keys import ClusterKeys
from .keys import ETEtaPhiKeys
from .keys import  extend_keys, CombineDestKeys

@extend_keys(["score"])
class MLKeys(ETEtaPhiKeys):
    def __init__(self, data=None, **kwargs):
        super().__init__(data, [CombineDestKeys(data, [ClusterKeys]).all_key_values + ["clus_score"]], **kwargs)

