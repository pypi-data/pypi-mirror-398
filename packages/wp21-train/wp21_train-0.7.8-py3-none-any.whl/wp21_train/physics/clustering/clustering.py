import pandas as pd
import awkward as ak
import numpy as np
import vector
from collections import OrderedDict
from ...bookkeeping.keys import GEPCellKeys, ClusterKeys, CellMapKeys
from ...utils.slicing_utils import replace_ak_fields, copy_fields, copy_all_fields_except, produce_mask_discrete_field
from ...utils.slicing_utils import filter_fields_by_discrete_field, rename_fields, add_zero_fields
from .backends import cluster_cpp_openmp
from .clustering_config import ClusteringConfigEFEX

def phi_border_mask(clusters, phi_key):
    mask = (ak.any(clusters[phi_key]<0, axis=2) & ak.any(clusters[phi_key]>0, axis=2)) & ak.any(np.abs(clusters[phi_key])>3, axis=2)
    return mask

def get_cluster_phi_centers(clusters, phi_key):
    """
    Get phi centers of clusters from the phi values supplied in the phi_key field.
    This is not trivial because phi has a discontinuity in pi->-pi and this complicates the computation
    """
    vector.register_awkward()
    #Separate two cases - when the pi->-pi border passes through the cluster and when it doesn't
    mask = phi_border_mask(clusters, phi_key)

    # pi->-pi border doesn't pass through cluster, then things are trivial
    # take the mean of the phi values
    phi_centers_noborder=ak.mean(ak.mask(clusters[phi_key],~mask), axis=2)

    # pi->-pi border does pass through cluster. Then need to look separately at
    # positive and negative phis, compute their means separately, combine them so that
    # the resulting phi angle is not in the -pi - pi range and use vector's Momentum2D functinality
    # to bring it back into the range.
    clusters_with_border=ak.mask(clusters[phi_key], mask)
    # Separate cells with negative and positive phis
    mask_negative = (clusters_with_border<0)
    # number of cells with non-negative phis
    num_neg = ak.num(clusters_with_border[mask_negative], axis=2)
    # number of cells with negative phis
    num_pos = ak.num(clusters_with_border[~mask_negative], axis=2)
    # Combine the means of the negative and positive part. Resulting phi will be arbitrary (not in -pi - pi range)
    centers_phi_border=((num_neg*ak.mean((ak.mask(clusters_with_border, mask_negative) + 2*np.pi), axis=2) + 
                         num_pos*ak.mean((ak.mask(clusters_with_border, ~mask_negative)), axis=2))/(num_neg+num_pos))

    # This converts arbitraty angle to -pi - pi range
    vec_centers_phi_border = ak.with_name(add_zero_fields(ak.zip({"phi": centers_phi_border}), ["pt"]), "Momentum2D")
    phi_centers_border = vec_centers_phi_border.deltaphi(ak.zeros_like(vec_centers_phi_border))

    # Combine the two cases (with border and without)
    phi_centers = (ak.fill_none(phi_centers_noborder, 0) + ak.fill_none(phi_centers_border, 0))
    return phi_centers

class Clustering:
    def __init__(self, clus_cfg=ClusteringConfigEFEX(sampling_layers=[2])):
        self.clus_cfg = clus_cfg

    def cluster(self, data, cell_map, backend="openmp"):
        if backend == "openmp":
            return self.produce_clusters_cpp(data, cell_map)
        else:
            raise ValueError(f"Unsupported backend {backend}")

    def produce_clusters_cpp(self, data, cell_map):
        clus_cfg = self.clus_cfg
        mask = produce_mask_discrete_field(cell_map, CellMapKeys(cell_map)["sampling"], clus_cfg.sampling_layers)
        cells = cell_map[CellMapKeys(cell_map).values()][mask]
        seeds = data[clus_cfg.other_keys().values()]
    
        cells_phi = ak.to_numpy(ak.flatten(cells[CellMapKeys(cell_map)["phi"]]))
        cells_eta = ak.to_numpy(ak.flatten(cells[CellMapKeys(cell_map)["eta"]]))
        cells_sampling  = ak.to_numpy(ak.flatten(cells[CellMapKeys(cell_map)["sampling"]]))
        cells_id  = ak.to_numpy(ak.flatten(cells[CellMapKeys(cell_map)["id"]]))
        
        seeds_phi = ak.to_numpy(ak.flatten([s[clus_cfg.other_keys()["phi"]] for s in seeds]))
        seeds_eta = ak.to_numpy(ak.flatten([s[clus_cfg.other_keys()["eta"]] for s in seeds]))
        
        gepcells_id = ak.to_numpy(ak.flatten(data[GEPCellKeys()["id"]]))
        gepcells_et = ak.to_numpy(ak.flatten(data[GEPCellKeys()["et"]]))
        
        shape_gepcells = ak.num(data[GEPCellKeys()["phi"]])
        shape_seeds = ak.num(data[clus_cfg.other_keys()["phi"]])
       
        # Call the fast C++ implementation
        res = cluster_cpp_openmp(
            cells_phi, cells_eta, cells_sampling, cells_id, 
            seeds_phi, seeds_eta, shape_seeds,
            gepcells_id, gepcells_et, shape_gepcells,
            phi_delta=clus_cfg.cluster_r_phi, eta_delta=clus_cfg.cluster_r_eta
        )
        
        to_zip = {}
        for k in ["et", "eta", "phi", "sampling", "id"]:
            v = ak.unflatten(ak.unflatten(ak.Array(res.__getattribute__(k)), ak.flatten(res.shape)), ak.num(res.shape))
            to_zip[CellMapKeys(cell_map)[k]] = v
      
        clusters=ak.Array(to_zip)
    
        # This sorts the cells so that they are arranged geometrically.
        # Since the eta/phi values slightly change even in the same eta/phi trip,
        # Digitization is performed first so that simple sorting can be done
        coords_idx = []
        for c in ["eta", "phi"]:
            key = CellMapKeys(cell_map)[c]
            gran_key = CellMapKeys(cell_map)[f"{c}_gran"]
            delta = ak.min(cells[gran_key])/5.0
            coord_min, coord_max = ak.min(cells[key]), ak.max(cells[key])
            
            # Create bin edges
            bins = np.arange(coord_min, coord_max + delta, delta)
        
            flat1 = ak.flatten(clusters[key])
            counts1 = ak.num(clusters[key])
            
            flat2 = np.digitize(ak.flatten(flat1), bins)-1
            flat2 = np.clip(flat2, 0, len(bins) - 2)  # keep inside range
            counts2 = ak.num(flat1)
            
            coords_idx.append(ak.unflatten(ak.unflatten(flat2, counts2), counts1))
        
        
        sorted_clusters = ak.with_field(clusters, coords_idx[0], "cells_eta_d")
        sorted_clusters = ak.with_field(sorted_clusters, coords_idx[1], "cells_phi_d")
        
        idx = ak.argsort(sorted_clusters["cells_eta_d"])
        sorted_clusters=sorted_clusters[idx]
        idx = ak.argsort(sorted_clusters["cells_phi_d"])
        sorted_clusters=sorted_clusters[idx]
        idx = ak.argsort(sorted_clusters[CellMapKeys(cell_map)["sampling"]])
        sorted_clusters=sorted_clusters[idx]

        # There is a problem around the -pi -> + pi border. Suppose we have a cluster with the border passing through it.
        # Assuming for simplicity phi values of 0,1,2,3,-3,-2,-1:
        # Clusters are formed counter clockwise in phi:
        #                       pi/2      
        #
        #                 +pi           +0
        #                 ---------------
        #                 -pi           -0
        #                        
        #                       -pi/2
        # If the 0 border passes through a cluster, everything is ok, sorting yields a cluster -2,-1,0,1,2.
        # When the +pi->-pi border passes through a cluster, the cluster should be 2,3,-3,-2. However,
        # sorting would yield -3,-2,2,3. So we need to swap the negative and positive sides in such occurrences
        # to get the correct sorting:

        phi_key = CellMapKeys(cell_map)["phi"]
        # Mask to get all clusters which are crossed by the pi border
        mask = phi_border_mask(sorted_clusters, phi_key) 
        # Negative side of cluster
        mask_lt0 = mask & (sorted_clusters[phi_key] < 0)
        # Positive side of cluster
        mask_gt0 = mask & (sorted_clusters[phi_key] > 0)

        # indices of cells in negative clusters
        idx_left = ak.local_index(sorted_clusters[phi_key])[mask_lt0]
        # indices of cells in positive clusters
        idx_right = ak.local_index(sorted_clusters[phi_key])[mask_gt0]
        # Indices of all other cells
        idx_others = ak.local_index(sorted_clusters[phi_key][~(mask_lt0 | mask_gt0)])
        # Swap negative and positive
        sorted_clusters = sorted_clusters[ak.concatenate([idx_right, idx_others, idx_left], axis=2)]

        # Append the seeds used for the clustering and rename the cells et field, since it's 
        #  taken from the GEP cells (realistic integer values) and not from the cell map (float values)
        sorted_clusters = copy_fields(sorted_clusters, data, clus_cfg.other_keys().values(),
                                      rename_map = {CellMapKeys(cell_map)["et"]:GEPCellKeys()["et"]})

        return sorted_clusters
    
    def map_cells_to_gep_et_awkward(clusters_cellmap, gep_cells_per_event, fallback=0):
        """
        Awkward-driven approach that works for event -> clusters -> cells nested layout.
        Returns ak.Array with same nested structure as clusters_cellmap['cells_ID'].
        """
        def map_one_event(event_clusters, gep_ids, gep_ets):
            lookup = {gid: get for gid, get in zip(gep_ids, gep_ets)}
            return [[lookup.get(cid, fallback) for cid in cluster] for cluster in event_clusters]
    
        ev_clusters = ak.to_list(clusters_cellmap["cells_ID"])
        ev_gep_ids  = ak.to_list(gep_cells_per_event["GEPCells_ID"])
        ev_gep_ets  = ak.to_list(gep_cells_per_event["GEPCells_et"])
    
        out = [map_one_event(c, g_ids, g_ets) for c, g_ids, g_ets in zip(ev_clusters, ev_gep_ids, ev_gep_ets)]
        return ak.Array(out)
    
    def produce_merged_cluster_df_with_isol(data, core_eta, core_phi, env_eta, env_phi, has_truth=True, clus_cfg=ClusteringConfigEFEX(sampling_layers=[2])):#, cluster_r_phi=core_phi, cluster_r_eta=core_eta)):
        clus_cfg.update(cluster_r_phi=core_phi, cluster_r_eta=core_eta)
        core_cluster = produce_merged_cluster_df(data, has_truth=has_truth, clus_cfg=clus_cfg)
        clus_cfg.update(cluster_r_phi=env_phi, cluster_r_eta=env_eta)
        cluster = produce_merged_cluster_df(data, has_truth=has_truth, clus_cfg=clus_cfg)
        cluster["core"] = core_cluster[ClusterKeys()["et"]]
        cluster.rename({ClusterKeys()["et"]: "env"}, axis=1, inplace=True)
        cluster["isol"] = cluster["env"]-cluster["core"]
        cluster["isol_frac"] = cluster["core"]/cluster["env"]
        return cluster
    

