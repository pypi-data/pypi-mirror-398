from .keys import ETEtaPhiKeys, CombineDestKeys, extend_keys

@extend_keys(['prongs'])
class TauTruthKeys(ETEtaPhiKeys):
    def __init__(self, data, **kwargs):
        super().__init__(data, [["tau_pt_vis", "tau_eta_vis", "tau_phi_vis", "tau_num_charged"], \
            ["truth_tau_pt_vis", "truth_tau_eta_vis", "truth_tau_phi_vis", "tau_num_charged"]], **kwargs)

    def determine_version(self, data):
        if "truth_tau_pt_vis" in data.fields:
            return 1
        return 0

@extend_keys(["bdt"])
class TauEFEXKeys(ETEtaPhiKeys):
    def __init__(self, data=None, **kwargs):
        super().__init__(data, [["L1_eTauxRoISim_et", "L1_eTauxRoISim_eta", "L1_eTauxRoISim_phi", "L1_eTauxRoISim_bdtScore"]], **kwargs)



@extend_keys(["sampling", "id"])
class CellKeys(ETEtaPhiKeys):
    def __init__(self, data, dst_keys_versions, **kwargs):
        super().__init__(data, dst_keys_versions, **kwargs)

class GEPCellKeys(CellKeys):
    def __init__(self, data=None, **kwargs):
        super().__init__(data, [["GEPCells_et", "GEPCells_eta", "GEPCells_phi", "GEPCells_sampling", "GEPCells_ID"]], **kwargs)

@extend_keys(["eta_gran", "phi_gran", "noise"])
class CellMapKeys(CellKeys):
    def __init__(self, data=None, **kwargs):
        # Prioritize GEP keys if they appear in the data (items that are lists are interpreted in decreasing priority)
        super().__init__(data, [[
            [GEPCellKeys(data)["et"], "cells_et"], 
            [GEPCellKeys(data)["eta"], "cells_eta"], 
            [GEPCellKeys(data)["phi"], "cells_phi"], 
            "cells_sampling", "cells_ID", "cells_etaGranularity", "cells_phiGranularity", "cells_totalNoise"]], **kwargs)

def all_gep_keys(data=None):
    all_versions = False
    if data is None:
        all_versions = True
    return CombineDestKeys(data, [GEPCellKeys, TauEFEXKeys, TauTruthKeys], all_dest_keys=all_versions).all_key_values

