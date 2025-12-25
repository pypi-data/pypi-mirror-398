import xml.etree.ElementTree as ET
from wp21_train.utils.version import __version__

class aie_parser:

    def __init__(self, report_name):
        self._rpt_name  = report_name
        self._data      = {}
        self._meta_data = {}
        self._parse()

    def __time_parse(self, data, value, extra = ''):
        data[extra+'total_cycles'] = int(value.findtext('total_cycle_count')  )
        data[extra+'min_cycles']   = int(value.findtext('minimum_cycle_count'))
        data[extra+'max_cycles']   = int(value.findtext('maximum_cycle_count'))
        data[extra+'avg_cycles']   = int(value.findtext('average_cycle_count'))
        return data

    def __instr_parse(self, data, value, extra = ''):
        data[extra+'total'] = int(value.findtext('instruction_count')        )
        data[extra+'min']   = int(value.findtext('minimum_instruction_count'))
        data[extra+'max']   = int(value.findtext('maximum_instruction_count'))
        data[extra+'avg']   = int(value.findtext('average_instruction_count'))

    def __callee_parse(self, data, values, extra = ''):
        cnt         = 0
        for i_entry in values:
            data[f'{extra}_callee_{cnt}_name'] = i_entry.findtext('function_name')
            cnt += 1
        return data
        
    def _parse(self, _criterion = 'function2'):
        tree = ET.parse(self._rpt_name)
        root = tree.getroot()

        functions = root.findall('.//function')

        cnt  = 0
        for i_elem in functions:
            temp                  = {}
            temp_meta             = {}
            #Data
            temp['name']          = i_elem.findtext('function_name')
            temp['calls']         = int(i_elem.findtext('calls'))
            func_time             = i_elem.find('function_time')
            func_dep_time         = i_elem.find('function_and_descendants_time')
            instr_cnt             = i_elem.find('function_instruction_count')
            instr_dep_cnt         = i_elem.find('function_and_descendants_instruction_count')
            self.__time_parse(temp, func_time    , 'time_'         )
            self.__time_parse(temp, func_dep_time, 'time_and_desc_')
            self.__instr_parse(temp, instr_cnt    , 'instr_'         )
            self.__instr_parse(temp, instr_dep_cnt, 'instr_and_desc_')
            #temp['Title']         = 'data'
            self._data[f'function_{cnt}'] = temp
            #Meta-Data
            temp_meta['low_pc']       = int(i_elem.findtext('low_pc'))
            temp_meta['high_pc']      = int(i_elem.findtext('high_pc'))
            temp_meta['mangled_name'] = i_elem.findtext('mangled_function_name')
            callee_data               = i_elem.findall('callee')
            self.__callee_parse(temp_meta, callee_data, 'tree')
            #temp_meta['Title']        = 'meta-data'            
            self._meta_data[f'function_{cnt}_meta'] = temp_meta
            cnt += 1            
            
    def get_version(self):
        return f"aie_parser version: {__version__}"

            
