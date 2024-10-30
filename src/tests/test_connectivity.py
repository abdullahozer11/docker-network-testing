import pytest

from src.core.test_base import NetworkTestBase


class TestBasicConnectivity:
    @pytest.fixture(scope="class")
    def network_test(self):
        return NetworkTestBase()

    def test_ping_between_nodes(self, network_test):
        """Test if node1 can ping node2."""

        def run_ping():
            # Direct node names are used instead of NetworkNode objects
            container = network_test.docker_client.containers.get(
                "network-test-framework-node1-1"
            )
            exit_code, _ = network_test._execute_command(
                container, "ping -c 3 172.20.0.3", "node1"
            )
            assert exit_code == 0, "Node1 cannot ping Node2"

            # Test reverse connectivity
            container = network_test.docker_client.containers.get(
                "network-test-framework-node2-1"
            )
            exit_code, _ = network_test._execute_command(
                container, "ping -c 3 172.20.0.2", "node2"
            )
            assert exit_code == 0, "Node2 cannot ping Node1"

        network_test.run_test("test_ping_between_nodes", run_ping)

    def test_interface_configuration(self, network_test):
        """Test interface configuration on both nodes."""

        def run_interface_test():
            # Verify interface configuration on both nodes
            node1_interface = network_test.verify_interface("node1", "eth0")
            assert node1_interface["status"] == "UP", "Node1 interface is down"

            node2_interface = network_test.verify_interface("node2", "eth0")
            assert node2_interface["status"] == "UP", "Node2 interface is down"

        network_test.run_test("test_interface_configuration", run_interface_test)

    def test_routing_configuration(self, network_test):
        """Test routing table configuration on both nodes."""

        def run_routing_test():
            # Check routing tables on both nodes
            node1_routes = network_test.check_routing_table("node1")
            assert (
                "172.20.0.0/16" in node1_routes["routes"]
            ), "Missing expected route on node1"

            node2_routes = network_test.check_routing_table("node2")
            assert (
                "172.20.0.0/16" in node2_routes["routes"]
            ), "Missing expected route on node2"

        network_test.run_test("test_routing_configuration", run_routing_test)
