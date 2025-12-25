import yaml

from wp21_train.savers.adapter import adapter
from wp21_train.utils.logger   import log_message

class yml_adapter(adapter):
    def __init__(self, file_name, dump_data = {}, dump_meta = {}):
        self._file         = file_name + '.yml'
        self._data         = {"data": dump_data or {}}
        self._meta         = {"meta": dump_meta or {}}

    def write_data(self):
        payload = [self._data, self._meta]
        with open(self._file, 'w') as yml_file:
            yaml.safe_dump(payload, yml_file, sort_keys=False)
        log_message('info',f'Successful write to {self._file}')

    def read_data(self):

        with open(self._file, 'r') as yml_file:
            payload = yaml.safe_load(yml_file)

        if isinstance(payload, (list, tuple)):
            data_part = payload[0] if len(payload) > 0 else {}
            meta_part = payload[1] if len(payload) > 1 else {}
        elif isinstance(payload, dict):
            data_part = payload.get('data', payload if 'meta' not in payload else {})
            meta_part = payload.get('meta', {})
        else:
            data_part, meta_part = payload, {}
            
        self._data = self._wrap_section(data_part, 'data')
        self._meta = self._wrap_section(meta_part, 'meta')
            
        log_message('info',f'Successful read from {self._file}')
        return [self._data, self._meta]
