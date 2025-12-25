import uproot
import json
import numpy   as np
import awkward as ak

from collections.abc import Mapping, Sequence

from wp21_train.savers.adapter import *
from wp21_train.utils.logger   import log_message


class root_adapter(adapter):

    def __init__(self, file_name, dump_data = {}, dump_meta = {}):
        self._file         = file_name + ".root"
        self._data         = {'data':dump_data or {}}
        self._meta         = {'meta':dump_meta or {}}

    def _flatten(self, mapping, parent_key="", sep="__"):
        out = {}
        for k, v in (mapping or {}).items():
            key = f"{parent_key}{sep}{k}" if parent_key else str(k)
            if isinstance(v, Mapping):
                out.update(self._flatten(v, key, sep=sep))
            else:
                out[key] = v
        return out
        
    def _infer_branch_type(self, key, value):
        if isinstance(value, Mapping):
            return "string"

        if isinstance(value, bool):
            return "int8"
        if isinstance(value, int) and not isinstance(value, bool):
            return "int64"
        if isinstance(value, float):
            return "float64"
        if isinstance(value, str):
            return "string"

        if isinstance(value, (list, tuple, np.ndarray, ak.Array)):
            try:
                seq0 = value[0] if len(value) > 0 else None
                if isinstance(seq0, str):
                    return "string"
            except Exception:
                pass

            first = None
            if isinstance(value, ak.Array):
                if len(value) > 0:
                    first = ak.to_list(value)[0]
            elif isinstance(value, np.ndarray):
                if value.size > 0:
                    first = value.flat[0]
            else:
                if len(value) > 0:
                    first = value[0]

            if isinstance(first, int):
                return "var * int64"
            if isinstance(first, float):
                return "var * float64"

            return "string"

        return "string"
    
    
    def _to_branch_array(self, value, branch_type):
    
        if branch_type == "string":
            if value is None:
                s = None
            elif isinstance(value, (list, tuple, np.ndarray, ak.Array)):
                try:
                    if len(value) == 0:
                        s = ""
                    else:
                        v0 = value[0]
                        if isinstance(v0, str):
                            s = ",".join(map(str, value))
                        elif isinstance(v0, (int, float, bool)):
                            s = ",".join(map(str, value))
                        else:
                            s = json.dumps(list(value), ensure_ascii=False)
                except Exception:
                    s = str(value)
            elif isinstance(value, Mapping):
                s = json.dumps(value, ensure_ascii=False)
            else:
                s = str(value)
            return np.array([s], dtype=object)

        if branch_type in ("int64", "int32", "int16"):
            return np.array([0 if value is None else int(value)], dtype=np.int64)
        if branch_type in ("float64", "float32"):
            return np.array([0.0 if value is None else float(value)], dtype=np.float64)

        if branch_type.startswith("var * "):
            base = branch_type.split("var * ", 1)[1]
            if isinstance(value, ak.Array):
                arr = value
                if ak.num(arr, axis=0) != 1:
                    arr = ak.Array([ak.to_list(arr)])
                return arr

            if value is None:
                seq = []
            elif isinstance(value, np.ndarray):
                seq = value.tolist()
            elif isinstance(value, (list, tuple)):
                seq = list(value)
            else:
                seq = [value]

            flat = []
            for x in seq:
                if isinstance(x, (list, tuple, np.ndarray)):
                    flat.extend(list(x))
                else:
                    flat.append(x)

            if "int" in base:
                flat = [int(xx) for xx in flat if xx is not None]
            else:
                flat = [float(xx) for xx in flat if xx is not None]

            return ak.Array([flat])

        return np.array([None], dtype=object)
        
    def _prepare_tree(self, mapping):
        
        flat               = self._flatten(mapping or {})
        branch_types, data = {}, {}
        
        for k, v in flat.items():

            if isinstance(v, (list, tuple)) and len(v) == 0:
                continue
            btype = self._infer_branch_type(k, v)
            arr   = self._to_branch_array(v, btype)

            if isinstance(arr, ak.Array):
                if ak.num(arr, axis=0) != 1:
                    arr = ak.Array([ak.to_list(arr)])
            else:
                if arr.shape[0] != 1:
                    arr = arr.reshape(1, *arr.shape)

            branch_types[k] = btype
            data[k]         = arr
        return branch_types, data
    
    def write_data(self):
        data_map = self._data.get('data', {}) or {}
        meta_map = self._meta.get('meta', {}) or {}

        data_schema, data_payload = self._prepare_tree(data_map)
        meta_schema, meta_payload = self._prepare_tree(meta_map)

        with uproot.recreate(self._file) as root_file:
            if data_schema:
                t_data = root_file.mktree('data', data_schema)
                t_data.extend(data_payload)
            if meta_schema:
                t_meta = root_file.mktree('meta', meta_schema)
                t_meta.extend(meta_payload)

        log_message('info', f'Successful write to {self._file}')

    def read_data(self):
        data_out, meta_out = {}, {}

        with uproot.open(self._file) as root_file:
            if 'data' in root_file:
                t = root_file['data']
                for br in t.keys():
                    arr          = t[br].array(library='ak')
                    data_out[br] = ak.to_list(arr[0])
            if 'meta' in root_file:
                t = root_file['meta']
                for br in t.keys():
                    arr          = t[br].array(library='ak')
                    meta_out[br] = ak.to_list(arr[0])

        self._data = {'data': data_out}
        self._meta = {'meta': meta_out}
        log_message('info',f'Successful read from {self._file}')
        return [self._data, self._meta]
