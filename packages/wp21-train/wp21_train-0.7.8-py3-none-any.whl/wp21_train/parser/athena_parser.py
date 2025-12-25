import sys
import yaml

# should I rename it to log?
from wp21_train.utils.logger  import log_message
from wp21_train.utils.version import __version__


class athena_parser:

    def __init__(self, data: dict, metadata: dict):
        self.config = data['data']
        self.environment = metadata['meta']

        # inputs to the parser should be dictionaries
        # produced by an adapter
        if not isinstance(self.config, dict):
            log_message("error", "Configuration data is not a dictionary.")
            sys.exit(1)
        if not isinstance(self.environment, dict):
            log_message("error", "Environment metadata is not a dictionary.")
            sys.exit(1)

        self._config_arguments = {
            "clusterAlgs":  "commma separated list of stategies for GepClusterAlg: [WFS,Calo420,Calo422,TopoTower]",
            "jetAlgs":      "commma separated list of stategies for GepJetAlg:[Cone,ModAntikT,AntiKt4,AntiKt4Truth,AntiKt4EMPFlow,L1_jFexSRJetRoI]",
            "inputFiles":   "list of files to run over",
            "fexs":         "fexs to enable",
            "ems":          "EM algos",
            "taus":         "Tau algos",
            "outputFile":   "Name of output file"
        }

        self._environment_arguments = {
            "WP21_VERSION": "WP21 version to use",
            "ENV_ATHENA":   "ATHENA version",
            "ENV_GEP_HASH": "GEP output reader git commit hash",
        }

        self._parse()

    def _check_version(self):
        if 'WP21_VERSION' not in self.environment:
            log_message("warning", "WP21_VERSION is not set in the info YML file.")
            self.environment['WP21_VERSION'] = __version__
            log_message("info", f"Setting WP21_VERSION to {__version__}.")
        elif self.environment['WP21_VERSION'] != __version__:
            log_message("error", f"WP21_VERSION provided in data ({self.environment['WP21_VERSION']}) does not match the current version ({__version__}).")
            sys.exit(1)

    def _find_unexpected_args(self, args, allowed_args):
        unexpected_args = [
            arg for arg in args
            if arg not in allowed_args
        ]
        if unexpected_args:
            log_message("error", f"Unexpected configuration arguments found: {unexpected_args}. \nThe allowed arguments are: {list(allowed_args)}.")
            sys.exit(1)

    def _check_config(self):
        """Checking config is tolerant to missing arguments. It just check if names are correct."""
        self._find_unexpected_args(args=self.config.keys(), allowed_args=self._config_arguments)

    def _check_environment(self):
        """Checking environment is not tolerant to missing arguments. It checks if all required environment variables are set."""
        self._find_unexpected_args(args=self.environment.keys(), allowed_args=self._environment_arguments)

        missing_env = [
            arg for arg in self._environment_arguments
            if arg not in self.environment or self.environment[arg] is None
        ]

        n_missing_env = len(missing_env)
        n_env = len(self._environment_arguments)

        if n_missing_env == 0:
            log_message("info", "All required environment variables are set.")
            return []
        
        log_message("warning", f"{n_missing_env} of {n_env} environment variables are missing.\n The following variables are missing: {missing_env}\n")

        return missing_env

    def _provide_mandatory_input(self, var_name: str, var_desc: str, config_or_env: str, missing_or_incorrect: str = "missing"):
        while True:
            if missing_or_incorrect == "missing":
                value = input(f"Missing {config_or_env} argument {var_name} - ({var_desc}): ")
            elif missing_or_incorrect == "incorrect":
                value = input(f"Incorrect {config_or_env} argument for {var_name} - ({var_desc}): ")
            if value:
                return value
            log_message("warning",f"A value for {var_name} is mandatory to be provided")

    def _update_missing_info(self, missing_env: list):
        if missing_env:
            log_message("warning", "Let's setup the missing environment info:")

        for var, desc in self._environment_arguments.items():
            if var not in self.environment:
                missing_var = self._provide_mandatory_input(
                    var_name=var, 
                    var_desc=desc, 
                    config_or_env="environment", 
                    missing_or_incorrect="missing",) 
                   
                self.environment[var] = missing_var

    def _check_env_hash(self):
        # at this point the hash needs to have been provided
        hash_val = self.environment.get("ENV_GEP_HASH")
        try:
            int(hash_val, 16)
            return True
        except ValueError:
            log_message("error", f"Provided ENV_GEP_HASH '{hash_val}' is not a valid hexadecimal string.")
            sys.exit(1)

    def _save_config(self):
        with open("config.yml", "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)
        log_message("info", "Configuration saved to config.yml")

    
    def _save_environment(self):
        with open("environment.yml", "w") as f:
            yaml.dump(self.environment, f, default_flow_style=False)
        log_message("info", "Environment metadata saved to environment.yml")

    def _parse(self):
        self._check_version()
        self._check_config()
        missing_env = self._check_environment()

        self._update_missing_info(missing_env)
        self._check_env_hash()
        
        self._save_config()
        self._save_environment()

        log_message("info", "Configuration and environment metadata parsed successfully.")
