import os
import glob
import re
import uproot
import awkward as ak
import json
from ..bookkeeping.keys import all_gep_keys
from ..utils.logger import log_message

class ParquetUtils:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def get_groups_to_read(self, n_events):
        groups = self.split_groups(n_events)
        return groups[0]

    def split_groups(self, n_events_per_group):
        md = ak.metadata_from_parquet(self.folder_path)
        col_counts = md['col_counts']
        groups = []
        group_counter = 0
        while True:
            accum = 0
            row_groups = []
            for i, n in enumerate(col_counts):
                row_groups.append(group_counter)
                group_counter += 1
                accum += n
                if accum >= n_events_per_group:
                    break
            groups.append(row_groups)
            if i == len(col_counts) - 1:
                break
            col_counts = col_counts[i+1:]

        return groups 


class Sample:
    MU_TO_RUN = {
        0: "_r16128",
        140: "_r16129",
        200: "_r16130",
    }

    def __init__(self, folder):
        self.ds_folder = folder

    def get_expected_parquet_folder_path(self):
        base_name = os.path.basename(self.ds_folder)
        expected_parquet_path = os.path.join(self.ds_folder, "..", "parquet", base_name)
        expected_parquet_path = os.path.abspath(expected_parquet_path)
        return expected_parquet_path

    def has_parquet(self, validate_option=None, n_events=10):
        """
        Check that the sample has a corresponding parquet folder with parquet files.
        Validate that the parquet files correspond to the root files with the given validate_option.
        Some validations (e.g. 3), take a very long time but are very thorough.

        validate_option = None: check that parquet folder exists with any files
        validate_option = 0: Check that parquet file names match with the root files
        validate_option = 1: 0 check + the number of entries in each file pair is the same and the names of the branches
        validate_option = 2: 1 check + load the first pair of files and check the first n_events events that the contents are the same (recommended)
        validate_option = 3: 1 check + load every file and check that the first n_events events have the same content (takes very long)
        validate_option = 4: Good in case parquet files do not correspond one-to-one to the root files. Will compare :
           - total number of events
           - content of n_events from first root file with first n_events from parquet file
           - content of n_events from last root file with last n_events from parquet file
        """
        expected_parquet_path = self.get_expected_parquet_folder_path()

        if not os.path.isdir(expected_parquet_path):
            return False

        # --- List .root and .parquet files ---
        root_files = sorted(f for f in os.listdir(self.ds_folder) if f.endswith(".root"))
        parquet_files = sorted(f for f in os.listdir(expected_parquet_path) if f.endswith(".parquet"))

        if validate_option is None and len(parquet_files) > 0:
            return True

        if validate_option == 4:
            row_groups = ParquetUtils(expected_parquet_path).split_groups(n_events)
            rg_start = row_groups[0]
            rg_end = row_groups[-1]

            # Compare first n_events
            root_path = os.path.join(self.ds_folder, root_files[0])
            parquet_path = os.path.join(expected_parquet_path, parquet_files[0])
            array_root = uproot.concatenate(f"{root_path}:ntuple", entry_stop=n_events)
            array_parquet = ak.from_parquet(parquet_path, row_groups=rg_start)[:n_events]
            if not ak.almost_equal(array_root, array_parquet):
                log_message("WARNING",
                            f"Parquet folder found for {self.ds_folder} but the first {n_events} in the first file ({root_path}) differ between root and parquet."\
                            "Strongly recommended to regenerate parquet folder")
                return False

            # Compare last n_events
            root_path = root_files[-1]
            parquet_path = parquet_files[-1]
            array_root = uproot.concatenate(f"{root_path}:ntuple", entry_stop=n_events)
            array_parquet = ak.from_parquet(parquet_path, row_groups=rg_start)[-n_events:]
            if not ak.almost_equal(array_root, array_parquet):
                log_message("WARNING",
                            f"Parquet folder found for {self.ds_folder} but the last {n_events} in the last file ({root_path}) differ between root and parquet."\
                            "Strongly recommended to regenerate parquet folder")
                return False

        # --- Quick check: same number and matching base names ---
        if len(root_files) != len(parquet_files):
            log_message("WARNING",
                        f"Parquet folder found for {self.ds_folder} but the number of files in parquet and root folders is different. "\
                        "Strongly recommended to regenerate parquet folder")
            return False

        root_bases = [os.path.splitext(f)[0] for f in root_files]
        parquet_bases = [os.path.splitext(f)[0] for f in parquet_files]

        if set(root_bases) != set(parquet_bases):
            log_message("WARNING",
                        f"Parquet folder found for {self.ds_folder} but the file names in parquet and root folders don't correspond. "\
                        "Strongly recommended to regenerate parquet folder")
            return False

        if (validate_option == 0):
            return True
        # --- Deep check: same number of entries per file ---
        for base in root_bases:
            root_path = os.path.join(self.ds_folder, f"{base}.root")
            parquet_path = os.path.join(expected_parquet_path, f"{base}.parquet")
#
#            # count entries in ROOT
            with uproot.open(root_path) as f:
                root_entries = f["ntuple"].num_entries
                root_fields = f["ntuple"].keys()

            # count entries in Parquet
            md = ak.metadata_from_parquet(parquet_path)
            parquet_entries = md['num_rows']
            parquet_fields = md['form'].columns()

            if root_entries != parquet_entries:
                log_message("WARNING",
                            f"Parquet folder found for {self.ds_folder} but the number of entries for file {base} "\
                            "differ between root and corresponding parquet. Strongly recommended to regenerate parquet folder")
                return False

            if set(root_fields) != set(parquet_fields):
                log_message("WARNING",
                            f"Parquet folder found for {self.ds_folder} but the tree names differ for file {base}."\
                            "Strongly recommended to regenerate parquet folder")
                return False

            if (validate_option == 3):
                array_root= uproot.concatenate(f"{root_path}:ntuple", entry_stop=n_events)
                array_parquet = ak.from_parquet(parquet_path, row_groups=[0])[:n_events]
                if not ak.almost_equal(array_root, array_parquet):
                    log_message("WARNING",
                                f"Parquet folder found for {self.ds_folder} but the contents for file {base} differ between root and parquet."\
                                "Strongly recommended to regenerate parquet folder")
                    return False

        if (validate_option == 2):
            base = root_bases[0]
            root_path = os.path.join(self.ds_folder, f"{base}.root")
            parquet_path = os.path.join(expected_parquet_path, f"{base}.parquet")
            array_root= uproot.concatenate(f"{root_path}:ntuple", entry_stop=n_events)
            array_parquet = ak.from_parquet(parquet_path, row_groups=[0])[:n_events]
            if not ak.almost_equal(array_root, array_parquet):
                log_message("WARNING",
                            f"Parquet folder found for {self.ds_folder} but the contents for file {base} differ between root and parquet."\
                            "Strongly recommended to regenerate parquet folder")
                return False

        return True

    @classmethod
    def from_ds_name(cls, path: str, sample: str, mu: int, sample_mapping_path: str):
        mapping = json.load(open(sample_mapping_path, "r"))

        if mu not in cls.MU_TO_RUN:
            raise ValueError(f"Unsupported mu={mu}. Only {list(cls.MU_TO_RUN.keys())} are supported.")

        sample_to_search = f"{sample}-{mu}"

        # Validate sample exists in mapping
        if sample_to_search not in mapping:
            raise ValueError(f"Sample '{sample}' not found in mapping.")

        dataset_pattern = '.'.join(mapping[sample_to_search].split('.')[1:]).replace('recon.AOD.', '')
        
        run_tag = cls.MU_TO_RUN[mu]

        # Search for folders containing dataset_pattern and the correct run_tag
        candidates = [
            os.path.join(path, d)
            for d in os.listdir(path)
            if os.path.isdir(os.path.join(path, d)) and dataset_pattern in d and run_tag in d
        ]

        if not candidates:
            raise FileNotFoundError(f"No dataset folder found in {path} for sample {sample} (mu={mu}).")
        if len(candidates) > 1:
            raise RuntimeError(f"Multiple dataset folders found: {candidates}")

        dataset_folder = candidates[0]

        return Sample(dataset_folder)

    @staticmethod
    def parse_mapping(filename):
        """
        Use this to parse the mapping within run_grid.sh of the GEPOutputReader project
        """
        mapping = {}
        with open(filename) as f:
            for line in f:
                match = re.match(r'\s*\["([^"]+)"\]\s*=\s*"([^"]+)"', line)
                if match:
                    key, value = match.groups()
                    mapping[key] = value
        return mapping

class DataLoader:
    def __init__(self, sample):
        self.sample = sample

    def parquet_split_groups(self, n_events_per_group):
        return ParquetUtils(self.sample.get_expected_parquet_folder_path()).split_groups(n_events_per_group)

    def parquet_get_groups_to_read(self, n_events):
        return ParquetUtils(self.sample.get_expected_parquet_folder_path()).get_groups_to_read(n_events)

    def load_parquet(self, parquet_dir_path, n_events=5000, parquet_row_groups=None):
        if parquet_row_groups is None:
            row_groups_to_read = ParquetUtils(parquet_dir_path).get_groups_to_read(n_events)
        else:
            row_groups_to_read = parquet_row_groups
        md = ak.metadata_from_parquet(parquet_dir_path)
        if md['num_row_groups'] == 1:
            row_groups_to_read = None
            # TODO known issue in awkward: when running inside container, metadata file contains the original path (/eos/...) but the files are mounted
            #  in a different path. awkward compares those internally and throws an exception when reading with an explicitly provided row_groups
            # Temp solution is to use single parquet files
            log_message("INFO", f"Found Parquet files, loading {parquet_dir_path}")
        else:
            log_message("INFO", f"Found Parquet files, loading {n_events} events (row groups {row_groups_to_read} from {parquet_dir_path}")
        array = ak.from_parquet(parquet_dir_path, row_groups=row_groups_to_read, columns=all_gep_keys())
        return array

    def load(self, n_events=5000, parquet_row_groups=None):
        if self.sample.has_parquet(validate_option=0): #TODO set to None
            array = self.load_parquet(self.sample.get_expected_parquet_folder_path(), n_events, parquet_row_groups)
        else:
            glob = os.path.join(self.sample.ds_folder, "*.root:ntuple")
            log_message("INFO", f"Loading {glob}")
            array = uproot.concatenate(glob, entry_stop=n_events, filter_name=all_gep_keys())

        return array
