import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List
from tqdm import tqdm
import os
import json

@dataclass 
class PerformanceSummary:
    efficiency: Dict[str, List[float]]
    rate: int
    trigger: str

class PerformanceEvaluator:
    def __init__(self, discriminants, eff_pt_points, baseline_counts, baseline_eff):
        self.discriminants = discriminants
        self.eff_pt_points = eff_pt_points
        self.evaluation_df = None
        self.baseline_counts = baseline_counts
        self.baseline_eff = baseline_eff
        self.evaluations = None

    def evaluate(self, trigger_grid, bg_arr, sig_arr, roi_eta_key, roi_phi_key):
        """
        Produce a dataframe from the TriggerGrid instance with the efficiency, counts and area under curve
        """
        evaluations = trigger_grid.evaluate(bg_arr, sig_arr, roi_eta_key, roi_phi_key)

        header = []

        df = list(evaluations.values())[0][0].get_cuts()
        discriminants = [d for d in self.discriminants if d in df["name"]]
        for d in discriminants:
            prefix = "_sec_"
            is_primary = df.loc[df["name"]==d]["is_primary"].iloc[0]
            if is_primary:
                prefix = "_prim_"
            name = prefix + d    
            header.append(name)
            if not is_primary:
                header.append(f"{name}_min")
                header.append(f"{name}_max")
            
        for eff_pt in self.eff_pt_points:
            header.append(f"eff_{eff_pt}")
        
        header.append("area_turnon")
        header.append("counts")
        header.append("name")
        
        rows = []
        for name,v in tqdm(evaluations.items()):
            row = []
            trigger, rate, eff = v
            eff_map = eff.set_index("pt")["efficiency"].to_dict()
            cuts_df = trigger.get_cuts().set_index("name")
            for d in discriminants:
                cut, mn ,mx, is_primary = cuts_df.loc[d, ["cut", "min", "max", "is_primary"]]
                row.append(cut)
                if not is_primary:
                    row+=[mn,mx]
            for eff_pt in self.eff_pt_points:
                row.append(eff_map.get(eff_pt, np.nan))
        
            row.append(np.nansum(list(eff_map.values())))
            row.append(rate)
            row.append(name)
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.columns = header
        self.evaluation_df = df
        self.evaluations = evaluations

    def any(self, use_area=True):
        # TODO THIS IMPLEMENTATION IS BAD. It's meant to very roughly answer the question
        # If any trigger is better than the reference in terms of rate and/or efficiency.
        # A proper implementation should probably use a p-value. Something like:
        # Assume poisson distribution for count, count_ref with lambda,lambda_ref, respectively
        # Null hypothesis: lambda > lambda_ref (our algo is worse in terms of rate)
        # What is the p-value of having count at least as low as observed.
        # This should be combined together with the efficiency to form a combined p-value for
        # "Assuming our trigger is worse, what is the probability to get count and efficiency
        # at least as extreme as that observed"
        baseline_turnon_area = self.baseline_eff["efficiency"].sum()
        counts_slack = np.sqrt(self.baseline_counts) # assmuing poisson counts
        query=[f"(counts<={self.baseline_counts+counts_slack})"] # Very rough and incorrect comparison

        if use_area:
            epsilon = baseline_turnon_area * 0.1 # Made up 10% value
            query.append(f"area_turnon>{baseline_turnon_area-epsilon}")
        else:
            epsilon = 0.01 # Some made up allowed slack in efficiency
            for eff_pt in self.eff_pt_points:
                baseline_eff_pt = self.baseline_eff.loc[self.baseline_eff["pt"]==eff_pt]["efficiency"].values[0]
                key = f"eff_{eff_pt}"
                query.append(f"({key}>={str(baseline_eff_pt-epsilon)})")
        
        query='&'.join(query)
        return len(self.evaluation_df.query(query))>0

        
