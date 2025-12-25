import pandas as pd
import awkward as ak
from collections import OrderedDict
from ...bookkeeping.keys import GEPCellKeys, CellMapKeys, ClusterKeys
from ...utils.slicing_utils import copy_all_fields_except
from ...physics.clustering import get_cluster_phi_centers

class ClusterDiscriminants:
    """
    Various discriminants on clusters
    """

    def __init__(self, clusters, params):
        """
        Clusters are an awkward array of size N*M*K where 
        - N is the number of events, 
          - M (varying) goes over the clusters in an event
            - K (varying) goes over the individual cells in a cluster
        """
        self.clusters = clusters
        self.params = params 
        self.cluster_type = self.determine_type(clusters)

    @staticmethod
    def determine_type(obj):
        if isinstance(obj, pd.DataFrame):
            return "pd"
        elif isinstance(obj, ak.Array):
            return "ak"
        else:
            raise TypeError(f"Unsupported type: {type(obj)}")

    def sum(self):
        """
        Sum over all cells in a cluster
        Clusters are an awkward array of size N*M*K where 
        - N is the number of events, 
          - M (varying) goes over the clusters in an event
            - K (varying) goes over the individual cells in a cluster
        Or a pandas Dataframe with the columns "entry", "subentry", "GEPCells_et".
        The sum will be computed by groupbing over "entry" and "subentry" and applying a sum function over
        the "GEPCells_et" column
        """
        if self.cluster_type == "ak":
            return ak.sum(self.clusters[GEPCellKeys()["et"]], axis=2)
        return self.clusters.groupby(["entry", "subentry"]).sum()[GEPCellKeys()["et"]].values

    @classmethod
    def get_map(cls):
        return OrderedDict([(ClusterKeys()["et"], lambda *args, **kwargs: ClusterDiscriminants(*args, **kwargs).sum())])

    @classmethod
    def get_discriminant_keys(cls):
        return list(cls.get_map().keys())

    def compute(self):
        """
        Compute the cluster discriminants. Clusters are ractangular regions of cells which are formed before calling this
        method (e.g. by produce_clusters). They are provided in the constructor
    
        returns an awkward array
        """
        phi_key = CellMapKeys(self.clusters)["phi"]
        eta_key = CellMapKeys(self.clusters)["eta"]
        clus_phi = get_cluster_phi_centers(self.clusters, phi_key)
        clus_eta = ak.mean(self.clusters[eta_key], axis=2)
        discrs = []
        for i,(k, f) in enumerate(self.get_map().items()):
            discr = f(self.clusters, self.params)
            discrs.append(discr)

        result = ak.Array(dict(zip(list(self.get_map().keys()) + [ClusterKeys()[x] for x in ["phi", "eta"]], discrs + [clus_phi, clus_eta])))
        return copy_all_fields_except(result, self.clusters, CellMapKeys(self.clusters).values())

