import json
from pathlib import Path
from typing import Any, Dict

from loguru import logger


class SettingsLoader:
    def __init__(self, config_dir: Path = None):
        if config_dir is None:
            config_dir = Path(__file__).parent / "defaults"
        self.config_dir = config_dir

    def load(self, network: str, config_name: str = "structural_pattern_settings") -> Dict[str, Any]:
        network_file = self.config_dir / f"{network}_{config_name}.json"
        if network_file.exists():
            logger.info(f"Loading network-specific config from {network_file}")
            return self._load_json(network_file)

        base_file = self.config_dir / f"{config_name}.json"
        if base_file.exists():
            logger.info(f"Loading base config from {base_file} with network overrides for {network}")
            base_config = self._load_json(base_file)
            return self._apply_network_overrides(base_config, network)

        raise RuntimeError(f"No configuration found for {config_name} in {self.config_dir}")

    def _load_json(self, path: Path) -> Dict[str, Any]:
        with open(path, "r") as f:
            config = json.load(f)
        self._validate_config(config)
        return config

    def _apply_network_overrides(self, config: Dict[str, Any], network: str) -> Dict[str, Any]:
        resolved = {}
        for section_name, section_config in config.items():
            if not isinstance(section_config, dict):
                resolved[section_name] = section_config
                continue

            section_resolved = {}
            network_overrides = section_config.get("network_overrides", {})
            network_specific = network_overrides.get(network, {})

            for key, value in section_config.items():
                if key == "network_overrides":
                    continue
                if key in network_specific:
                    section_resolved[key] = network_specific[key]
                else:
                    section_resolved[key] = value

            resolved[section_name] = section_resolved

        return resolved

    def _validate_config(self, config: Dict[str, Any]) -> None:
        required_keys = [
            "cycle_detection",
            "path_analysis",
            "proximity_analysis",
            "network_analysis",
            "motif_detection",
        ]

        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")

        cycle_config = config["cycle_detection"]
        for key in ["max_cycle_length", "max_cycles_per_scc"]:
            if key not in cycle_config:
                raise ValueError(f"Missing required cycle detection parameter: {key}")

        path_config = config["path_analysis"]
        for key in ["min_path_length", "max_path_length", "max_paths_to_check"]:
            if key not in path_config:
                raise ValueError(f"Missing required path analysis parameter: {key}")

        proximity_config = config["proximity_analysis"]
        if "max_distance" not in proximity_config:
            raise ValueError("Missing required proximity analysis parameter: max_distance")
