# src/core/config.py
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml


@dataclass
class NetworkConfig:
    ip_address: str
    subnet_mask: str
    gateway: Optional[str] = None


@dataclass
class TestConfig:
    name: str
    description: str
    nodes: Dict[str, NetworkConfig]
    timeout: int = 30


class ConfigManager:
    def __init__(self, config_path: str = "config/test_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, TestConfig]:
        if not self.config_path.exists():
            return self._create_default_config()

        with open(self.config_path, "r") as f:
            raw_config = yaml.safe_load(f)
            return self._parse_config(raw_config)

    @staticmethod
    def _parse_config(raw_config: dict) -> Dict[str, TestConfig]:
        configs = {}
        for name, cfg in raw_config.items():
            nodes = {
                node_name: NetworkConfig(
                    ip_address=node_cfg["ip_address"],
                    subnet_mask=node_cfg["subnet_mask"],
                    gateway=node_cfg.get("gateway"),
                )
                for node_name, node_cfg in cfg["nodes"].items()
            }

            configs[name] = TestConfig(
                name=name,
                description=cfg.get("description", ""),
                nodes=nodes,
                timeout=cfg.get("timeout", 30),
            )
        return configs

    def _create_default_config(self) -> Dict[str, TestConfig]:
        default_config = {
            "basic_connectivity": TestConfig(
                name="basic_connectivity",
                description="Basic connectivity test between nodes",
                nodes={
                    "node1": NetworkConfig(
                        ip_address="172.20.0.2", subnet_mask="255.255.0.0"
                    ),
                    "node2": NetworkConfig(
                        ip_address="172.20.0.3", subnet_mask="255.255.0.0"
                    ),
                },
            )
        }

        self.config_path.parent.mkdir(exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(
                {
                    name: {
                        "description": cfg.description,
                        "nodes": {
                            nname: {
                                "ip_address": node.ip_address,
                                "subnet_mask": node.subnet_mask,
                            }
                            for nname, node in cfg.nodes.items()
                        },
                    }
                    for name, cfg in default_config.items()
                },
                f,
                default_flow_style=False,
            )

        return default_config
