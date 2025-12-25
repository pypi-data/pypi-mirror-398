import awkward as ak
import numpy as np
import pandas as pd
import json
import os
import uproot
import pickle
from dataclasses import asdict
from .data import DataLoader, Sample
from .bookkeeping.paths import Paths
from .bookkeeping.keys import CellMapKeys
from .physics.clustering import Clustering
from .physics.clustering import diagnostics
from .physics.matching import match_clusters_by_dR
from .physics.performance import PerformanceSummary
from .utils.slicing_utils import copy_fields

class Project:
    """
    Base class for all projects
    """
    def __init__(self, name, description, mu, **parameters):
        self.n_events = {'sig': parameters.pop('n_sig_events'), 'bg': parameters.pop('n_bg_events')}
        self.samples_short = {'sig': parameters.pop('sig_short', None), 'bg':parameters.pop('bg_short', None)}
        self.sample_path = parameters.pop('sample_path', Paths.get_sample_path())
        self.cellmap_path = parameters.pop('cellmap_path', Paths.get_cellmap_path())
        self.sample_mapping_path = parameters.pop('sample_mapping_path')
        self.name = name
        self.parameters = parameters
        self.description = description
        self.mu = mu
        self.bg_data = self.__load("bg") 
        self.sig_data = self.__load("sig")
        self.performance_evaluator = None

    def __load(self, sig_or_bg):
        key = f"pickle_{sig_or_bg}"
        if key in self.parameters:
            pickle_path = self.parameters[key]
            if os.path.isfile(pickle_path):
                data = pickle.load(open(pickle_path, "rb"))
            else:
                data = self.get_preprocessed_data(sig_or_bg)
                pickle.dump(data, open(pickle_path, "wb"))
        else:
            data = self.get_preprocessed_data(sig_or_bg)
        return data
 
    def __not_impl_error_msg(self, fname):
        return f"Must implement {fname} in your project class"

    def get_sample_names(self, sig_or_bg):
        return [self.samples_short[sig_or_bg]]

    def load_raw_data(self, sig_or_bg, n_events, path=Paths.get_sample_path()):
        # TODO support multiple samples
        return [DataLoader(Sample.from_ds_name(path, s, mu=self.mu, sample_mapping_path=self.sample_mapping_path)).load(n_events=n_events) for s in self.get_sample_names(sig_or_bg)][0]

    def load_raw_cellmap(self, path=Paths.get_cellmap_path()):
        cell_map = uproot.open(path)['caloCellsMap'].arrays()
        return cell_map

    def get_preprocessed_data(self, sig_or_bg):
        raise NotImplementedError(self.__not_impl_error_msg("get_preprocessed_data"))

    def get_baseline_rate(self, data=None):
        if data is None:
            data = self.bg_data
        baseline_trigger = self.get_baseline_trigger()
        return baseline_trigger.counts(data)

    def get_baseline_efficiency(self, truth_data, eta_key, phi_key, dR_window=0.2, bins=np.arange(0, 120000, 2000)):
        baseline_trigger = self.get_baseline_trigger()
        curve = baseline_trigger.efficiency(truth_data, eta_key=eta_key, phi_key=phi_key, dR_cutoff=dR_window, bins=bins)
        return curve

    def get_baseline_trigger(self):
        raise NotImplementedError(self.__not_impl_error_msg("get_baseline_trigger"))

    def save_baseline_performance(self, out_folder, out_fname="baseline_performance.json"):
        full_path = os.path.join(out_folder, out_fname)
        counts = int(self.performance_evaluator.baseline_counts)
        eff = self.performance_evaluator.baseline_eff.to_dict(orient='list')
        trig_name = str(self.get_baseline_trigger())
        ps = PerformanceSummary(eff, counts, trig_name)

        with open(full_path, "w") as f:
            json.dump(asdict(ps), f, indent=2)

class SeededRectangularClusters(Project):
    """
    Base class for all projects that rely on clustering around seeds.
    A discriminants class instance can be provided, which is used to compute the discriminants
       on the fly as part of the preprocessing of data
    """
    def __init__(self, name, description, mu, **parameters):
        """
        Expects:
           - clus_cfg - instance of the ClusteringConfig class or its derivative
        """
        self.clus_cfg = parameters.pop("clus_cfg")
        self.discriminants = parameters.pop("discriminants", None)
        self.discriminant_params = parameters.pop("discriminant_params", {})
        self.fields_to_keep = parameters.pop("fields_to_keep", None)
        super().__init__(name, description, mu, **parameters)

    def update_discriminant_params(self, new_params):
        self.discriminant_params = new_params

    def get_discriminant_keys(self):
        assert self.discriminants is not None, "No discriminants set"
        return self.discriminants.get_discriminant_keys()

    def compute_discriminants(self, clusters, keep_clusters=False):
        if self.discriminants is not None:
            discr = self.discriminants(clusters, self.discriminant_params).compute()
            if keep_clusters:
                return merge_disjoint_fields([clusters, discr])
            return discr
        return clusters

    def get_preprocessed_data(self, sig_or_bg):
        data = self.load_raw_data(sig_or_bg, self.n_events[sig_or_bg], self.sample_path)
        cell_map = self.load_raw_cellmap(self.cellmap_path)
        clusters = Clustering(self.clus_cfg).cluster(data, cell_map)
        diagnostics.plot_cluster_size(clusters)
        diagnostics.assert_cluster_size(clusters, self.clus_cfg.cluster_r_eta, self.clus_cfg.cluster_r_phi)
        diagnostics.plot_cluster_non_zeros(clusters)
        diagnostics.plot_cell_et(clusters)
        if self.fields_to_keep:
            # fields_to_keep is a list of fields to keep
            clusters = copy_fields(clusters, data, self.fields_to_keep)

        return clusters
 
    def _get_signal_for_training(self, truth_keys_cls, seed_keys_cls, dR_cutoff=0.2):
        """
        Get signal data for ML model training. Returns a NxC array of N clusters. Each cluster is formed
        around a seed which is truth matched. The keys for the truth objects and seed objects are provided
        using the key class types truth_keys_cls, seed_keys_cls. The matching is done withing a dR of dR_cutoff.

        C is the typical size of the cluster. Cluster may vary in size but for now we assume that the ajority have the same
        size and that is computed by looking at the median of cluster sizes
        """
        truth_phi_key = truth_keys_cls(self.sig_data)["phi"]
        truth_eta_key = truth_keys_cls(self.sig_data)["eta"]
        lkm = [truth_phi_key, truth_eta_key]

        seed_phi_key = seed_keys_cls(self.sig_data)["phi"]
        seed_eta_key = seed_keys_cls(self.sig_data)["eta"]
        cells_key = CellMapKeys(self.sig_data)["et"]
        rkm = [seed_phi_key, seed_eta_key, cells_key]

        clusters_matched_to_ref = match_clusters_by_dR(self.sig_data[lkm + rkm], dR_cutoff=dR_cutoff, left_keys = lkm,
                                                                     left_phi=truth_phi_key, left_eta=truth_eta_key, right_keys=rkm, 
                                                                     right_phi=seed_phi_key, right_eta=seed_eta_key)


        expected_cluster_size = np.median(ak.flatten(ak.num(clusters_matched_to_ref[cells_key], axis=-1), axis=None)).astype(int) 

        with_nones = ak.flatten(ak.flatten(ak.pad_none(clusters_matched_to_ref[cells_key], expected_cluster_size, axis=-1), axis=1), axis=0).to_numpy().data
        return pd.DataFrame(with_nones).dropna().values

    def _get_background_for_training(self):
        cells_key = CellMapKeys(self.bg_data)["et"]
        expected_cluster_size = np.median(ak.flatten(ak.num(self.bg_data[cells_key], axis=-1), axis=None)).astype(int)
        with_nones = ak.flatten(ak.flatten(ak.pad_none(self.bg_data["GEPCells_et"], expected_cluster_size, axis=-1), axis=1), axis=0).to_numpy().data
        return pd.DataFrame(with_nones).dropna().values
