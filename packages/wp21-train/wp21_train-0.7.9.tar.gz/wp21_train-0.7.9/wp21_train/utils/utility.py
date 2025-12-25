from typing import Iterable
from itertools import product

def get_short_type(value):
    type_map = {
        int  : 'd',
        float: 'f',
        str  : 's',
        bool : 'b',
        list : 'l',
        dict : 'm',
        tuple: 't',
        set  : 'set'}

    return type_map.get(type(value), 'u')

def _as_list(v):
    if isinstance(v, str) or not isinstance(v, Iterable) or isinstance(v, dict):
        return [v]

    return list(v)

def _iter_param_grid(space):

    keys = list(space.keys())
    value_lists = [_as_list(space[k]) for k in keys]

    for combo in product(*value_lists):
        yield dict(zip(keys, combo))

def _grid_size(space):
    n = 1
    for v in space.values():
        n *= max(1, len(_as_list(v)))
    return n

def _params_at(space, index: int):
    keys = list(space.keys())
    value_lists = [_as_list((space[k])) for k in keys]
    bases = [len(vs) for vs in value_lists]
    total = _grid_size(space)
    if index < 0 or index >= total:
        raise IndexError(f"index {index} out of range 0..{total-1}")
    digits = []
    for base in reversed(bases):
        digits.append(index % base)
        index //= base
    digits.reverse()
    return {k: value_lists[i][digits[i]] for i, k in enumerate(keys)}
          
def _merge_missing(dst, src):
    for k, v in src.items():
        if k not in dst:
            dst[k] = v
    return dst
        
def _wrap_section(section, topkey):
    if section is None:
        return {topkey: {}}
    if isinstance(section, dict):
        if topkey in section and isinstance(section[topkey], dict):
            return {topkey: section[topkey]}
        
        return {topkey: section}
    
    return {topkey: section}
    
    
