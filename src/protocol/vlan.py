from dataclasses import dataclass
from typing import List, Optional

from docker.models.containers import Container


@dataclass
class VLANConfig:
    vlan_id: int
    name: str
    ip_network: str
    tagged_ports: List[str]
    untagged_ports: Optional[List[str]] = None


class VLANManager:
    def __init__(self, container: Container):
        self.container = container

    def create_vlan(self, config: VLANConfig) -> bool:
        """Create a VLAN interface on the container."""
        try:
            # Create VLAN interface
            self.container.exec_run(
                f"ip link add link eth0 name eth0.{config.vlan_id} type vlan id {config.vlan_id}"
            )

            # Set IP address for VLAN interface
            self.container.exec_run(
                f"ip addr add {config.ip_network} dev eth0.{config.vlan_id}"
            )

            # Bring up the VLAN interface
            self.container.exec_run(f"ip link set eth0.{config.vlan_id} up")

            return True
        except Exception as e:
            print(f"Error creating VLAN: {e}")
            return False

    def delete_vlan(self, vlan_id: int) -> bool:
        """Delete a VLAN interface from the container."""
        try:
            self.container.exec_run(f"ip link delete eth0.{vlan_id}")
            return True
        except Exception as e:
            print(f"Error deleting VLAN: {e}")
            return False

    def get_vlan_info(self, vlan_id: int) -> dict:
        """Get information about a specific VLAN."""
        try:
            result = self.container.exec_run(f"ip -d link show eth0.{vlan_id}")
            return {
                "vlan_id": vlan_id,
                "status": result.exit_code == 0,
                "details": result.output.decode(),
            }
        except Exception as e:
            return {"error": str(e)}

    def verify_vlan_connectivity(self, target_ip: str, vlan_id: int) -> bool:
        """Verify connectivity within a VLAN."""
        try:
            result = self.container.exec_run(f"ping -I eth0.{vlan_id} -c 3 {target_ip}")
            return result.exit_code == 0
        except Exception as e:
            print(f"Error verifying VLAN connectivity: {e}")
            return False
