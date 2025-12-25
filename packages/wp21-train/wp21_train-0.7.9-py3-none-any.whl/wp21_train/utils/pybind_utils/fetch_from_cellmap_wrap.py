import awkward as ak
import os
from . import make
from ...bookkeeping.keys import GEPDataKeys

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

@make(
    this_folder=THIS_FOLDER,
    module_name="fetch_from_cellmap_impl",
    package="wp21_train.utils.pybind_utils"
)
def fetch_from_cellmap_wrap(fetch_from_cellmap_impl, *args, **kwargs):
    return fetch_from_cellmap_impl.fetch(*args, **kwargs)


def fetch_from_cellmap(data, cell_map, field_to_fetch):
    gepcells_id_shape = ak.num(data[GEPDataKeys.cell_key_map()["id"]])
    gepcells_id_flat  = ak.to_numpy(ak.flatten(data[GEPDataKeys.cell_key_map()["id"]]))
    cell_id_flat = ak.to_numpy(ak.flatten(cell_map[GEPDataKeys.cellmap_key_map()["id"]]))
    branch_flat = ak.to_numpy(ak.flatten(cell_map[field_to_fetch]))
    
    res = fetch_from_cellmap_wrap(gepcells_id_flat, cell_id_flat, branch_flat)
    return ak.with_field(data, ak.unflatten(res, gepcells_id_shape), field_to_fetch)
 
 

