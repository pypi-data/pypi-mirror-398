import numpy as np
import awkward as ak

# Utilities for slixing awkward arrays

def replace_ak_fields(data, field_names, mask, other_data=None, keep_masked_as_nans=False):
    """
    Replace the fields given in field_names in the awkward array data
      with the same fields with the mask applied
      if other_data is provided, will read the fields from there
    """
    array = ak.copy(data)

    for k in field_names:
        if other_data is None:
            if keep_masked_as_nans:
                array = ak.with_field(array, ak.mask(data[k], mask), k)
            else:
                array = ak.with_field(array, data[k][mask], k)
        else:
            if keep_masked_as_nans:
                array = ak.with_field(array, ak.mask(other_data[k], mask), k)
            else:
                array = ak.with_field(array, other_data[k][mask], k)
    return array

def copy_fields(dst, src, field_names, rename_map=None):
    """
    Copy fields listed in field_name from src to dst.
    Here the assumption is that the first dimension spans the events
    and there is no broadcasting for the other dimensions, i.e.
    you can copy fields of arbitrary internal structure
    """

    existing_fields = [x for x in field_names if x in src.fields]
    to_zip_dict = dict(zip(ak.fields(dst), ak.unzip(dst)))
    to_zip_dict.update(dict(zip(existing_fields, ak.unzip(src[existing_fields]))))

    if rename_map is not None:
        for k,v in rename_map.items():
            to_zip_dict[v] = to_zip_dict.pop(k)
    
    return ak.zip(to_zip_dict, depth_limit=1)

def copy_all_fields_except(dst, src, except_fields):
    """
    Copy all fields from ak array src to dst except the fields listed in except_fields
    """
    out = dst

    for f in src.fields:
        
        if f in except_fields:
            continue

        out = ak.with_field(out, src[f], f)
    return out

def produce_mask_discrete_field(data, field_name, field_values):
    """
    Produce a mask that has true if field_name is any of the field_values (thus discrete)
    """
    mask = ( data[field_name] == field_values[0] )

    for fv in field_values:
        mask = mask | ( data[field_name] == fv)
    return mask

def filter_fields_by_discrete_field(data, field_name, field_values, other_field_names):
    """
    Select entries in data for which the field field_name is within the values field_values
    other_field_names are also filteres (assumed to be in same field group). 
    The rest of the fields are preserved.

    field_values - a list
    return - a modified copy of data
    """
    mask = produce_mask_discrete_field(data, field_name, field_values)
    return replace_ak_fields(data, list(set(other_field_names).union([field_name])), mask)

def above(data, key, all_keys, threshold):
    mask = (data[key] > threshold)
    return replace_ak_fields(data, all_keys, mask)

def remove_fields(data, fields):
    out = data
    for f in fields:
        out = ak.without_field(out, f)
    return out

def select_fields(data, fields):
    orig_fields = data.fields
    to_remove = list(set(orig_fields).difference(fields))
    out = remove_fields(data, to_remove)
    return out

def rename_fields(arr, mapping):
    fields = ak.fields(arr)
    return ak.zip({mapping.get(f, f): arr[f] for f in fields})

def add_const_fields(arr, field_names, value):
    fields = ak.fields(arr)
    intersection = set(field_names).intersection(arr.fields)
    assert len(intersection) == 0, f"Intersection between requested const fields and existing fields is not empty ({intersection})"
    mapping = {f: arr[f] for f in fields}
    for f in field_names:
        mapping[f] = value
    return ak.zip(mapping)

def add_zero_fields(arr, field_names):
    return add_const_fields(arr, field_names, 0)

def drop_nans_in_field_group(data, fields):
    """
    Selects the fields and drops any nan entry in all fields of the field group. A field group is a group of fields representing N objects.
    Each contains an array of N values with the i-th entry representing a feature of the i-th object.
    So if an object contains nan in one of its features, it will be dropped in all fields.
    """
    mask = np.isfinite(data[list(fields)[0]])
    for f in fields:
        mask = mask & (np.isfinite(data[f]))

    return data[fields][mask]
    

def merge_disjoint_fields(arrays):
    """
    Merge multiple Awkward Arrays with disjoint fields
    into a single Awkward Array of records.

    Rules:
    - All arrays must have the same length (event count).
    - Each must be a record array (fields).
    - If a field name exists in more than one array, raise ValueError.
    """
    if not arrays:
        return ak.Array([])

    # check lengths
    lengths = [len(arr) for arr in arrays]
    assert len(set(lengths)) == 1, f"Arrays must have the same length, got lengths {lengths}"

    merged_fields = {}
    for arr in arrays:
        for f in arr.fields:
            assert f not in merged_fields, f"Field name conflict: {f}"
            merged_fields[f] = arr[f]

    return ak.Array(merged_fields)


def restrict_contiguous_eta_range(data, restricting_eta_field, restricted_eta_field, restricted_fields, keep_masked_as_nans=False):
    """
    Restrict a field group (dest) to only contain objects with eta within the range of the source group.
       IMPORTANT: eta range is assumed to "contiguous", that is, the maximum and minimum are detected and these serve
        as the limits. Gaps in eta are not accounted for.
    For example, if we want to only look at truth taus covered by the eFEX eta range to compute eFEX efficiency curves.
    source_eta_field - eta field name of the restricting objects (e.g. eFEX RoI eta)
    restriucted_eta_field - eta field name of the restricted objects (e.g. truth tau eta)
    restricted_fields - all fields in the field group of the objects to be restricted
    """
    eta_min, eta_max = [f(data[restricting_eta_field]) for f in [ak.min, ak.max] ]
    mask = (data[restricted_eta_field]>eta_min)
    mask = mask & (data[restricted_eta_field]<eta_max)
    return replace_ak_fields(data, restricted_fields, mask, keep_masked_as_nans=keep_masked_as_nans)

