import awkward as ak
import pandas as pd
from .trigger import Trigger

class RoITrigger(Trigger):
    def __init__(self, name):
        super().__init__(name)
        self.reset()

    def reset(self):
        self._cuts = [] #pd.DataFrame(columns=["name", "cut", "min", "max", "is_primary"])
        self.primary_set = False

    @classmethod
    def get_discriminants(cls, **kwargs):
        raise NotImplementedError("get_discriminants should be implemented in deriving class")

    def get_cuts(self):
        if isinstance(self._cuts, list):
            self._cuts = pd.concat(self._cuts, ignore_index=True).astype({"is_primary": bool})
        return self._cuts

    def get_primary_cut(self):
        df = self._cuts
        if isinstance(df, list):
            df = pd.concat(self._cuts, ignore_index=True).astype({"is_primary": bool})
        return df.loc[df["is_primary"]==True]["cut"].values[0]

    def set_cuts(self, cuts_df):
        """
        Fast api to set cuts, no validation is performed
        """
        self._cuts = cuts_df

    def set_primary_cut(self, name: str, cut):
        """Define the primary cut. Only one allowed."""
        assert name in self.get_discriminants(), f"Discriminant {name} is not supported (must be one of {self.get_discriminants()})"

        self._cuts.append(pd.DataFrame.from_records([
                {"name": name, "cut": cut, "min": None, "max": None, "is_primary": True}]))

    def set_secondary_cut(self, name: str, cut, min_val=None, max_val=None):
        """Define a secondary cut with optional range restrictions."""
        assert name in self.get_discriminants(), f"Discriminant {name} is not supported (must be one of {self.get_discriminants()})"

        self._cuts.append(pd.DataFrame.from_records([
                {"name": name, "cut": cut, "min": min_val, "max": max_val, "is_primary": False}]))

    def is_passed(self, events: ak.Array) -> ak.Array:
        """
        Check if objects in events pass the RoI trigger.
        events: awkward Array with fields matching cut names.
        Returns an awkward Array of shape (N events,) with lists of booleans for each row
        corresponding to objects in the events array.
        """

        cuts = self.get_cuts()
        if cuts.empty:
            raise ValueError("No cuts defined.")

        primary_row = cuts[cuts["is_primary"]].iloc[0]
        primary_name, primary_cut = primary_row["name"], primary_row["cut"]

        # Apply primary cut first
        primary_mask = (events[primary_name]>primary_cut)

        # Loop through secondary cuts
        mask = primary_mask
        for _, row in cuts[~cuts["is_primary"]].iterrows():
            sec_name, sec_cut, min_val, max_val = row["name"], row["cut"], row["min"], row["max"]

            # Apply range restriction to primary variable
            in_range = ak.ones_like(events[primary_name], dtype=bool)
            if min_val is not None:
                in_range = in_range & (events[primary_name] >= min_val)
            if max_val is not None:
                in_range = in_range & (events[primary_name] < max_val)

            # Apply secondary cut only where range condition is satisfied
            sec_mask = (events[sec_name]>=sec_cut)
            mask = mask & (~in_range | sec_mask)

        return mask

    def __repr__(self):
        cuts = self.get_cuts()
        name = super().__repr__()

        # Primary cut: is_primary == True
        primary = cuts[cuts["is_primary"]].iloc[0]
        primary_repr = f"{primary['name']}={primary['cut']}"

        # Secondary cuts: is_primary == False
        secondaries = cuts[~cuts["is_primary"]]
        secondary_repr = ", ".join(
            f"{row['name']}:{row['cut']}:{row['min']}:{row['max']}"
            for _, row in secondaries.iterrows()
        )

        # Build final string
        if secondary_repr:
            return f"{name}({primary_repr}, {secondary_repr})"
        else:
            return f"{name}({primary_repr})"


