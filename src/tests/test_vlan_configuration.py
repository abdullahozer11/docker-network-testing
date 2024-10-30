from typing import Dict

import docker
import pytest

from src.core.test_base import NetworkTestBase
from src.protocol.vlan import VLANConfig, VLANManager


class TestVLANConfiguration:
    @pytest.fixture(scope="class")
    def network_test(self):
        return NetworkTestBase()

    @pytest.fixture(scope="class")
    def docker_client(self):
        return docker.from_env()

    @pytest.fixture(scope="class")
    def vlan_configs(self) -> Dict[str, VLANConfig]:
        return {
            "vlan10": VLANConfig(
                vlan_id=10,
                name="management",
                ip_network="192.168.10.0/24",
                tagged_ports=["eth0"],
            ),
            "vlan20": VLANConfig(
                vlan_id=20,
                name="data",
                ip_network="192.168.20.0/24",
                tagged_ports=["eth0"],
            ),
        }

    @pytest.fixture(scope="function")
    def setup_vlans(self, docker_client, vlan_configs):
        """Setup VLANs on test containers."""
        containers = {
            "node1": docker_client.containers.get("network-test-framework-node1-1"),
            "node2": docker_client.containers.get("network-test-framework-node2-1"),
        }

        vlan_managers = {}
        for node_name, container in containers.items():
            manager = VLANManager(container)
            vlan_managers[node_name] = manager

            # Setup VLANs on each node
            for vlan_config in vlan_configs.values():
                manager.create_vlan(vlan_config)

        yield vlan_managers

        # Cleanup
        for manager in vlan_managers.values():
            for vlan_config in vlan_configs.values():
                manager.delete_vlan(vlan_config.vlan_id)

    def test_vlan_creation_and_connectivity(
        self, network_test, setup_vlans, vlan_configs
    ):
        """Test VLAN creation and inter-VLAN connectivity."""

        def run_vlan_test():
            vlan_managers = setup_vlans

            # Test VLAN 10 connectivity
            assert vlan_managers["node1"].verify_vlan_connectivity(
                "192.168.10.2", vlan_configs["vlan10"].vlan_id
            ), "VLAN 10 connectivity failed"

            # Test VLAN 20 connectivity
            assert vlan_managers["node1"].verify_vlan_connectivity(
                "192.168.20.2", vlan_configs["vlan20"].vlan_id
            ), "VLAN 20 connectivity failed"

            # Verify VLAN isolation
            vlan10_info = vlan_managers["node1"].get_vlan_info(10)
            vlan20_info = vlan_managers["node1"].get_vlan_info(20)

            assert vlan10_info["status"], "VLAN 10 not properly configured"
            assert vlan20_info["status"], "VLAN 20 not properly configured"

        network_test.run_test("test_vlan_configuration", run_vlan_test)

    def test_vlan_isolation(self, network_test, setup_vlans):
        """Test that traffic is properly isolated between VLANs."""

        def run_isolation_test():
            vlan_managers = setup_vlans

            # Try to ping VLAN 20 IP from VLAN 10 interface
            cross_vlan_ping = vlan_managers["node1"].verify_vlan_connectivity(
                "192.168.20.2", 10
            )

            assert not cross_vlan_ping, "VLAN isolation breach detected"

        network_test.run_test("test_vlan_isolation", run_isolation_test)
