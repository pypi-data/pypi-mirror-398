from collections import OrderedDict

"""
Utilities for bookkeeping keys (e.k.a. fields) in the awkward arrays/pandas dataframe columns used during analysis.
This includes management of fields based on the data - for example, if different versions of the data have different field names for the same value (e.g. the truth tau et),
these utilities will get the right value
Keys are indexed by generic names like "phi", "eta", "et", etc.
"""

def extend_keys(extra_keys):
    """
    Class decorator to extend the src_keys() instance method
    by appending extra keys on top of super().src_keys().
    """
    def decorator(cls):
        # keep reference to parent src_keys
        parent_src_keys = cls.src_keys

        def new_src_keys(self):
            return parent_src_keys(self) + extra_keys

        cls.src_keys = new_src_keys
        return cls
    return decorator

class CombineDestKeys(OrderedDict):
    """
    Combines the key values of a list of key component classes (to e.g. get all the relevant field names for GEPOutputReader ntuples)
    """
    def __init__(self, data, key_component_classes, all_dest_keys=False):
        self.all_key_values = []
        for k in key_component_classes:
            if all_dest_keys:
                self.all_key_values.extend(k(None, process=False).get_all_dest_keys())
            else:
                vals = k(data).selected_keys.values()
                self.all_key_values.extend(vals)
        if not all_dest_keys:
            assert len(set(self.all_key_values)) == len(self.all_key_values), f"Overlapping key values found, cannot combine {key_components}"
        self.all_key_values = list(self.all_key_values)

class KeysComponent:
    def __init__(self, data, dst_keys_versions, **kwargs):
        self.dst_keys_versions = dst_keys_versions
        process = True
        if "process" in kwargs and not kwargs["process"]:
            process = False

        if process:
            self.selected_keys = self.__get_keys_by_data(data)

    def src_keys(self):
        return []

    def __flatten(self, lst):
        result = []
        for item in lst:
            if isinstance(item, list):
                result.extend(self.__flatten(item))  # recursively flatten sublists
            else:
                result.append(item)  # keep strings or other non-list items as-is
        return result

    def get_all_dest_keys(self):
        all_key_values = []
        for d in self.dst_keys_versions:
            all_key_values.extend(self.__flatten(d))
        return all_key_values

    def __has_versions(self):
        return len(self.dst_keys_versions) > 1

    def __has_priorities(self):
        for key_versions in self.dst_keys_versions:
            for k in key_versions:
                if isinstance(k, list):
                    return True
        return False

    def determine_version(self, data):
        return 0

    def __get_keys_by_data(self, data):
        requires_data = self.__has_versions() or self.__has_priorities()

        if not requires_data:
            return OrderedDict(zip(self.src_keys(), self.dst_keys_versions[0]))

        assert data is not None, "To determine the correct keys data must be provided"

        version = self.determine_version(data)
        dst_keys  = self.dst_keys_versions[version]

        processed_dst_keys= []
        for k in dst_keys:
            if isinstance(k, list):
                processed_dst_keys.append(k)
            else:
                processed_dst_keys.append([k])
        final_key_map = OrderedDict()
        for n,k in zip(self.src_keys(), processed_dst_keys):
            found_variant = False
            for k_variant in k:
                if k_variant in data.fields:
                    found_variant = True
                    break
            if found_variant:
                final_key_map[n] = k_variant
        return OrderedDict(final_key_map)

    def values(self):
        return self.selected_keys.values()

    def keys(self):
        return self.src_keys()

    def __getitem__(self, src_keys):
        result = []
        if isinstance(src_keys, list):
            result = [self.selected_keys[k] for k in src_keys]
        else:
            result = self.selected_keys[src_keys]
        return result

@extend_keys(["et", "eta", "phi"])
class ETEtaPhiKeys(KeysComponent):
    def __init__(self, data, dst_keys_versions, **kwargs):
        super().__init__(data, dst_keys_versions, **kwargs)


