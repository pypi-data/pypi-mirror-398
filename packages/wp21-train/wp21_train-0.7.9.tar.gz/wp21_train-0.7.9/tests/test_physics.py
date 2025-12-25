import vector
import numpy as np
import itertools
import pandas as pd
import os
import pytest
import awkward as ak
from collections import OrderedDict
from wp21_train.physics.trigger import RoITrigger
from wp21_train.project import SeededRectangularClusters
from wp21_train.physics.clustering import ClusteringConfigEFEX, ClusterDiscriminants, get_cluster_phi_centers
from wp21_train.utils.slicing_utils import add_zero_fields
from wp21_train.physics.trigger.baseline import EFEXTau
from wp21_train.physics.trigger import TriggerGrid
from wp21_train.bookkeeping.paths import Paths
from wp21_train.bookkeeping.keys import TauEFEXKeys, GEPCellKeys, CellMapKeys, TauTruthKeys
from wp21_train.bookkeeping.keys import ClusWithIsolationKeys, extend_keys, ETEtaPhiKeys, CombineDestKeys
from wp21_train.physics.performance import PerformanceEvaluator
from wp21_train.physics.plotting.turnon import Plotter

data_folder = os.path.join(os.path.dirname(os.path.normpath(os.path.abspath(__file__))), "data")

@pytest.fixture
def bg_data():
    return ak.from_parquet(os.path.join(data_folder, "bg_100.parquet"))

@pytest.fixture
def sig_data():
    return ak.from_parquet(os.path.join(data_folder, "sig_100.parquet"))

@pytest.fixture
def cell_map():
    return ak.from_parquet(os.path.join(data_folder, "cell_map.parquet"))

class ProjectTest(SeededRectangularClusters):
    def __init__(self, name, description, mu, **parameters):
        self.test_sig_data = parameters.pop("sig")
        self.test_bg_data = parameters.pop("bg")
        self.test_cellmap_data = parameters.pop("cell_map")
        self.baseline_trigger = parameters.pop("baseline_trigger")
        super().__init__(name, description, mu, **parameters)

    def get_baseline_trigger(self):
        return self.baseline_trigger

    #Override
    def load_raw_data(self, sig_or_bg, n_events, path=Paths.get_sample_path()):
        # TODO support multiple samples
        if sig_or_bg == "bg":
            return self.test_bg_data
        return self.test_sig_data

    def load_raw_cellmap(self, path=Paths.get_cellmap_path()):
        return self.test_cellmap_data


@extend_keys(['sum_core', 'sum_env', 'isol'])
class KeysForTests(ETEtaPhiKeys):
    def __init__(self, data=None, **kwargs):
        super().__init__(data, [['test_et'] + CombineDestKeys(data, [ClusWithIsolationKeys]).all_key_values[1:]] )

class TriggerTest(RoITrigger):
    def __init__(self):
        super().__init__("glTest")

    @classmethod
    def get_discriminants(cls, **kwargs):
        return [KeysForTests()["et"], KeysForTests()["isol"]]

class DiscriminantsTest(ClusterDiscriminants):
    def __init__(self, clusters, params):
        super().__init__(clusters, params)

    def sum_inner(self, radius):
        vector.register_awkward()
        eta_key = CellMapKeys(self.clusters)["eta"]
        radius_eta = radius_phi = radius
        center_eta = ak.mean(self.clusters[eta_key], axis=2)
        mask_eta = np.abs(self.clusters[eta_key] - center_eta) <= radius_eta

        # Phi is more tricky because of the pi->-pi border
        phi_key = CellMapKeys(self.clusters)["phi"]

        # Get the phi centers
        center_phi = get_cluster_phi_centers(self.clusters, phi_key)

        # Use the vector Momentum2D functionality to compute deltaphi of each cell and center
        vec2d_cells = ak.with_name(add_zero_fields(ak.zip({"phi":self.clusters[phi_key]}), ["pt"]), "Momentum2D")
        vec2d_centers = ak.with_name(add_zero_fields(ak.zip({"phi":center_phi}), ["pt"]), "Momentum2D")

        mask_phi = np.abs(vec2d_cells.deltaphi(vec2d_centers)) <= radius_phi
        

        mask_center = mask_phi & mask_eta
        return ak.sum(self.clusters[CellMapKeys(self.clusters)["et"]][mask_center], axis=2, mask_identity=True)

    def sum_small(self):
        return self.sum_inner(self.params["inner_r"])

    def sum_large(self):
        return self.sum_inner(self.params["outer_r"])

    def isol(self):
        sum_small = self.sum_small()
        sum_large = self.sum_large()
        res = sum_small/sum_large
        return res

    def efex_with_cluster(self):
        """
        Experimental discriminant - eFEX already has hadronic info.
        So we can append to it the EM info from the larger cluster and use that
        as the primary cut. This will increase the ET cut of course
        """
#        large_sum = self.sum_large()
        small_sum = self.sum_small()
        res = self.clusters[TauEFEXKeys()["et"]] + small_sum #large_sum
        return res

    def efex(self):
        return self.clusters[TauEFEXKeys()["et"]]

    @classmethod
    def get_map(cls):
        """
        Extend the discriminant to function map
        """
        parent_map = super().get_map()

        parent_map  = OrderedDict([(KeysForTests()["et"], lambda *args, **kwargs: cls(*args, **kwargs).efex()),\
                                        (KeysForTests()["sum_core"], lambda *args, **kwargs: cls(*args, **kwargs).sum_small()),\
                                        (KeysForTests()["sum_env"], lambda *args, **kwargs: cls(*args, **kwargs).sum_large()),\
                                        (KeysForTests()["isol"], lambda *args, **kwargs: cls(*args, **kwargs).isol())])
        return parent_map

def make_project(bg, sig, cm, **kwargs):
    ref_trigger = EFEXTau()

    truth_keys = [TauTruthKeys(sig)[k] for k in ["eta", "phi", "et"]]
    ref_trigger.set_ref_keys(*truth_keys)
    ref_trigger.set_primary_cut(TauEFEXKeys()["et"], 12000)
    ref_trigger.set_secondary_cut(TauEFEXKeys()["bdt"], 0)
 
    project = ProjectTest("testProj", "test project", 200, n_bg_events=100, n_sig_events=100, sig=sig,bg=bg, cell_map=cm, discriminants=DiscriminantsTest,\
                        discriminant_params={"inner_r": 0.0625, "outer_r": 0.175},\
                         clus_cfg=ClusteringConfigEFEX(cluster_r_phi=0.175, cluster_r_eta=0.175, sampling_layers=[2]), fields_to_keep=TauTruthKeys(None, process=False).get_all_dest_keys(),
                          baseline_trigger=ref_trigger, sample_mapping_path=os.path.join(data_folder, "sample_mapping.json"), **kwargs)

    return project

def test_seeded_rectangular_clusters_project(bg_data, sig_data, cell_map):
    project = make_project(bg_data, sig_data, cell_map)    
    assert len(project.sig_data) == len(project.bg_data) == 100, "Bad number of events in test samples"
    assert set(TauEFEXKeys().values()).issubset(set(project.bg_data.fields)), "No eFEX keys found in test sample"
    assert set(CellMapKeys(project.bg_data).values()).issubset(set(project.bg_data.fields)), "No cell map keys found in test sample"
    assert set(TauTruthKeys(project.sig_data).values()).issubset(set(project.sig_data.fields)), "No tau truth keys found in test sample"

def test_trigger_grid(bg_data, sig_data, cell_map):
    project = make_project(bg_data, sig_data, cell_map)
    trig = TriggerTest()
    truth_keys = [TauTruthKeys(project.sig_data)[k] for k in ["eta", "phi", "et"]]
    trig.set_ref_keys(*truth_keys)
    primary_key = KeysForTests()["et"]
    discr_key = ClusWithIsolationKeys()["isol"]
    sig_data = project.compute_discriminants(project.sig_data)
    bg_data = project.compute_discriminants(project.bg_data)
 
    et_cut = 5000
    et_resolution = 200
    et_values = np.arange(
        et_cut - 1000,
        et_cut + 2000,
        et_resolution
    )

    discr_min = 0
    discr_max = 1
    discr_resolution = 0.1
    discr_values = np.clip(np.arange(discr_min, discr_max + discr_resolution, discr_resolution), a_min=discr_min, a_max=discr_max)
    
    grid = list(itertools.product(et_values, discr_values))
    tg = TriggerGrid(TriggerTest)
    for et, discr in grid:
        trig.reset()
        trig.set_cuts(pd.DataFrame([[primary_key, et, None, None, True],[discr_key, discr, 0, 50000, False]],
                                  columns = ["name", "cut", "min", "max", "is_primary"]))
        tg.register_trigger(trig)

    eff_pt_points = [12000, 20000, 30000, 40000, 50000, 60000, 80000, 100000]
    discriminants = project.get_discriminant_keys()

    efex_km = TauEFEXKeys()
    baseline_efficiency = project.get_baseline_efficiency(sig_data, eta_key=efex_km["eta"], phi_key = efex_km["phi"])
    baseline_counts = project.get_baseline_rate(bg_data)

    performance = PerformanceEvaluator(discriminants, eff_pt_points, baseline_counts, baseline_efficiency)

    performance.evaluate(tg, bg_data, sig_data, efex_km["eta"], efex_km["phi"])
    assert len(performance.evaluation_df) == 165, "Unepected length of evaluation dataframe"
    assert set(performance.evaluation_df['counts'].unique()) == set([ 82,  0, 86, 16, 78, 72, 64, 51, 69, 36, 84, 80, 68, 76, 58, 47, 32,\
                                                                      15, 77, 81, 44, 56, 31, 73, 14, 49, 63, 39, 13, 29, 62, 71, 66, 53,\
                                                                      34, 24, 10, 57, 52, 59, 43, 22, 65, 55, 40, 30, 60, 20, 45,  8, 26,\
                                                                      33, 18, 50, 27,  7, 21, 48,  6, 42, 25 ])
    assert list(performance.evaluation_df.columns) == ['eff_12000', 'eff_20000', 'eff_30000', 'eff_40000', 'eff_50000',\
                                                              'eff_60000', 'eff_80000', 'eff_100000', 'area_turnon', 'counts',\
                                                              'name']


def test_turnon_plot():
    import json
    turnon = json.load(open(os.path.join(data_folder, "turnon.json"), "r"))
    turnon_df = pd.DataFrame(turnon)
    Plotter({"Baseline": turnon_df}).plot_curves(save_path="test_turnon.png")

    assert os.path.isfile("test_turnon.png")

