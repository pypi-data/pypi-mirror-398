import awkward as ak
import numpy as np
from matplotlib import pyplot as plt
from ...bookkeeping.keys import CellMapKeys

def plot_cluster_size(clusters):
    key_eta = CellMapKeys(clusters)["eta"]
    key_phi = CellMapKeys(clusters)["phi"]
    eta_size = ak.flatten(ak.max(clusters[key_eta], axis=2)-ak.min(clusters[key_eta], axis=2), axis=None)
    phi_size = ak.flatten(ak.max(clusters[key_phi], axis=2)-ak.min(clusters[key_phi], axis=2), axis=None)

    plt.figure()
    plt.hist(eta_size, bins=100)
    plt.title("Clusters size ($\\eta$)")
    plt.savefig("clusters_eta_size.png", dpi=300, bbox_inches='tight')
    plt.close()
 
    plt.figure()
    plt.hist(phi_size, bins=100)
    plt.title("Clusters size ($\\phi$)")
    plt.savefig("clusters_phi_size.png", dpi=300, bbox_inches='tight')
    plt.close()


def plot_cluster_non_zeros(clusters):
    n_non_zero = ak.flatten(ak.num(clusters[CellMapKeys(clusters)["et"]][clusters[CellMapKeys(clusters)["et"]]>0],axis=2))
    plt.figure()
    plt.hist(n_non_zero, bins=100)
    plt.title("Number of nonzero cells")
    plt.savefig("clusters_n_non_zero.png", dpi=300, bbox_inches='tight')
    plt.close()

def plot_cell_et(clusters):
    et = ak.flatten(clusters[CellMapKeys(clusters)["et"]], axis=None)
    plt.figure()
    plt.hist(et, bins=100)
    plt.title("Cell $E_T$")
    plt.yscale("log")
    plt.savefig("cell_et.png", dpi=300, bbox_inches='tight')
    plt.close()

def assert_cluster_size(clusters, expected_eta, expected_phi):
    key_eta = CellMapKeys(clusters)["eta"]
    key_phi = CellMapKeys(clusters)["phi"]
    eta_size = ak.flatten(ak.max(clusters[key_eta], axis=2)-ak.min(clusters[key_eta], axis=2), axis=None)
    phi_size = ak.flatten(ak.max(clusters[key_phi], axis=2)-ak.min(clusters[key_phi], axis=2), axis=None)

    expected_eta *= 2
    expected_phi *= 2
    assert (np.median(eta_size) - expected_eta)/expected_eta < 0.2, "Too many clusters have a size which is larger than the expected size (eta)"
    assert (np.median(phi_size) - expected_phi)/expected_phi < 0.2, "Too many clusters have a size which is larger than the expected size (phi)"
