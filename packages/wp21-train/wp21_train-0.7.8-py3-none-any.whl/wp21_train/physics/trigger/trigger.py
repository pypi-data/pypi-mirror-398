import pandas as pd 
import numpy as np
import awkward as ak
from ..matching import match_arrays_by_dR

class Trigger:
    def __init__(self, name):
        self.name = name
        self.ref_eta_key = None
        self.ref_phi_key = None
        self.ref_pt_key = None
        self._cuts = pd.DataFrame()

    def set_ref_keys(self, ref_eta_key, ref_phi_key, ref_pt_key):
        """
        Set the eta, phi and et field names for the reference objects for the turn-on curves,
        e.g. truth objects.
        """
        self.ref_eta_key = ref_eta_key
        self.ref_phi_key = ref_phi_key
        self.ref_pt_key = ref_pt_key

    def get_cuts(self):
        raise NotImplementedError("Must implement get_cuts in Trigger subclass")

    def is_passed(self):
        raise NotImplementedError("Must implement is_passed in Trigger subclass")

    def counts(self, data):
        passed = self.is_passed(data)
        return ak.sum(ak.any(passed, axis=1))

    def efficiency(self, data, eta_key, phi_key, dR_cutoff=0.2, bins=np.arange(0, 120000, 2000)):
        """
        Generic method to compute the efficiency. Requires:
        - data - an awkward array containing the reference object fields for eta,phi,et as given in set_ref_keys.
                Also must contain all RoI-related fields required to perform the cuts, in addition to their eta and phi information
                for reference object-RoI dR matching.
        - eta_key - the field name of the eta coordinate for the RoI to use 
        - phi_key - the field name of the phi coordinate for the RoI to use 
        - dR_cutoff - dR matching window
        """

        assert None not in [self.ref_eta_key, self.ref_phi_key, self.ref_pt_key], "Must call set_ref_keys before generating efficiency curve"

        lkm = [self.ref_phi_key, self.ref_eta_key, self.ref_pt_key]
        rkm = list(self.get_cuts()["name"].values) + [eta_key, phi_key]

#        truth_taus_within_efex_range = replace_ak_fields(array_sig, lkm.values(), truth_in_efex_range_mask)[list(lkm.values()) + list(rkm.values())]
        roi_matched_to_ref = match_arrays_by_dR(data[lkm + rkm], dR_cutoff=dR_cutoff, left_keys = lkm,
                                                                     left_phi=self.ref_phi_key, left_eta=self.ref_eta_key, right_keys=rkm, 
                                                                     right_phi=phi_key, right_eta=eta_key)

        passing = data[lkm][ak.flatten(ak.fill_none(self.is_passed(roi_matched_to_ref), [False], axis=1), axis=2)]

        # Digitize the truth vis. pt for numerator and denominator and produce counts per pT bin for each
        numer_hist, bin_edges = np.histogram(ak.flatten(passing[self.ref_pt_key]), bins)
        denom_hist,_ = np.histogram(ak.flatten(data[self.ref_pt_key]), bins)

        # Compute efficiency curve
        efficiency = (numer_hist/denom_hist)

        eff_curve = pd.DataFrame({"numerator": numer_hist, "denominator": denom_hist, "pt": bin_edges[:-1], "efficiency": numer_hist/denom_hist})
        return eff_curve



    def __repr__(self):
        return self.name

