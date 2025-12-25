import xml.etree.ElementTree as ET
from wp21_train.utils.version import __version__
from wp21_train.utils.logger  import log_message

class hls_parser:

    def __init__(self, report_name, block_name = 'top'):        
        self._rpt_name  = report_name
        self._fw_block  = block_name
        self._data      = {}
        self._meta_data = {}

        self._parse('AreaEstimates'       )
        self._parse('UserAssignments'     )
        self._parse('PerformanceEstimates')

    def _parse(self, _criterion = 'AreaEstimates'):
        try:
            tree = ET.parse(self._rpt_name)
            root = tree.getroot()
        except Exception as e:
            log_message("ERROR", f"Failed to parse XML file {self._rpt_name}: {e}")
            return

        elem = root.find(_criterion)
        if elem is None:
            log_message("ERROR", f"Section {_criterion} not found in XML. Skipping.")
            return

        if _criterion == 'AreaEstimates':
            for child in elem:
                if child.tag == 'Resources':
                    for res in child:
                        try:
                            if res.text is not None:
                                self._data[res.tag] = float(res.text.strip())
                        except ValueError:
                            log_message("WARNING", f"Could not convert {res.tag} value to float. Skipping.")

                elif child.tag == 'AvailableResources':
                    for res in child:
                        try:
                            if res.text is not None:
                                self._meta_data[res.tag] = float(res.text.strip())
                        except ValueError:
                            log_message("WARNING", f"Could not convert {res.tag} meta-data value to float. Skipping.")

        elif _criterion == 'UserAssignments':
            for child in elem:
                if child.text is not None:
                    self._meta_data[child.tag] = child.text.strip()
                else:
                    log_message("WARNING", f"UserAssignment {child.tag} has no text. Skipping.")

        elif _criterion == 'PerformanceEstimates':
            for child in elem:
                tag = child.tag

                if tag == 'SummaryOfTimingAnalysis':
                    cp = child.find('EstimatedClockPeriod')
                    if cp is not None and cp.text:
                        try:
                            self._data['EstimatedClockPeriod'] = float(cp.text.strip())
                        except ValueError:
                            log_message("WARNING", f"Invalid EstimatedClockPeriod value. Skipping.")
                    else:
                        log_message("WARNING", f"Missing EstimatedClockPeriod tag.")

                elif tag == 'SummaryOfOverallLatency':
                    def safe_latency(key, xml_key):
                        val = child.find(xml_key)
                        if val is not None and val.text:
                            try:
                                self._data[key] = float(val.text.strip())
                            except ValueError:
                                log_message("WARNING", f"Invalid value for {xml_key}. Skipping.")
                        else:
                            log_message("WARNING", f"Missing {xml_key} tag")

                    safe_latency('BestCaseLatency'   , 'Best-caseLatency'   )
                    safe_latency('AverageCaseLatency', 'Average-caseLatency')
                    safe_latency('WorstCaseLatency'  , 'Worst-caseLatency'  )
                    safe_latency('PipelineDepth'     , 'PipelineDepth'      )
                            
        
    def get_version(self):
        return f"hls_parser version: {__version__}"
