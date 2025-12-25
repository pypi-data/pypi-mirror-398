"""OS-level system checks and functions for the comms system."""
from typing import Any, Optional, Union
import json
import os
import subprocess
import getpass


_SUDO_PASSWORD = None


def is_can_interface(interface: str) -> bool:
    """Check if an interface is a CAN interface."""
    return interface.startswith(("can", "vcan"))


def is_running_as_sudo() -> bool:
    """Returns True if the current process is running as sudo, False otherwise."""
    return os.geteuid() == 0


def run_checked_system_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a system command and check the result. Fails if the command returns a non-zero exit code."""
    # Get sudo password and send it into the command via stdin if needed
    stdin_input = None
    if cmd[0] == "sudo" and not is_running_as_sudo():
        global _SUDO_PASSWORD
        if _SUDO_PASSWORD is None:
            _SUDO_PASSWORD = getpass.getpass("Enter sudo password: ")
        if cmd[1] != "-S":
            cmd.insert(1, "-S")
        stdin_input = _SUDO_PASSWORD + "\n"

    result = subprocess.run(cmd, capture_output=True, text=True, input=stdin_input)
    if result.returncode != 0:
        raise ValueError(f"Command \"{' '.join(cmd)}\" failed with return code {result.returncode}. " \
                         f"\n\tstdout: {result.stdout}, \n\tstderr: {result.stderr}")
    return result


def get_can_links_json() -> list[dict[str, Any]]:
    """Return a list of JSON records for interfaces whose names start with 'can' or 'vcan'."""
    data = json.loads(run_checked_system_command(["ip", "-details", "-json", "link"]).stdout)
    return [link for link in data if is_can_interface(link.get("ifname", ""))]


def get_all_physical_can_interfaces() -> list[str]:
    """Return a list of all physical CAN interfaces."""
    return [link["ifname"] for link in get_can_links_json() if link["ifname"].startswith("can")]


def enable_can_interface(interface: Union[str, list[str]], bitrate: int = 1_000_000) -> None:
    """Enable a CAN interface or multipleinterfaces.
    
    For a "can" interface:
    - If it doesn't exist, raise an error
    - If it exists but is down, enable it
    - If it exists and is up, make sure the bitrate is correct. Raise an error if it is not.

    For a "vcan" interface:
    - If it doesn't exist, create it
    - If it exists but is down, enable it
    - Bitrate is ignored
    """
    if isinstance(interface, (list, tuple)):
        for iface in interface:
            enable_can_interface(iface, bitrate)
        return
    
    _enable_can_helper(interface, bitrate)
    if not _enable_can_helper(interface, bitrate, just_checking=True):
        raise ValueError(f"Can interface {interface} failed to enable after running commands")


def _get_can_bitrate(link: dict[str, Any]) -> int:
    """Return the bitrate of a CAN interface"""
    return link['linkinfo']['info_data']['bittiming']['bitrate']


def _enable_can_helper(
    interface: str, 
    bitrate: int,
    can_links_json: Optional[list[dict[str, Any]]] = None,
    just_checking: bool = False
) -> bool:
    """Helper function to enable a CAN interface. Returns True if the interface was already up, False otherwise."""
    can_links_json = get_can_links_json() if can_links_json is None else can_links_json
    
    for link in can_links_json:
        if link["ifname"] == interface:
            # The interface exists, check if it's up and ready. vCANs are always "UNKNOWN" state once created
            if link["operstate"] == "UP" or (interface.startswith("vcan") and link["operstate"] == "UNKNOWN"):
                if not interface.startswith("vcan") and _get_can_bitrate(link) != bitrate:
                    exp_str = f"Expected {bitrate}, got {_get_can_bitrate(link)}"
                    raise ValueError(f"Can interface {interface} is already up but has the wrong bitrate. {exp_str}")
                return True
            else:
                if just_checking:
                    return False
                _enable_can_interface(interface, bitrate)
            break
    else:
        # The interface doesn't exist. If it's a vCAN interface, create it. Otherwise, raise an error.
        if interface.startswith("vcan"):
            if just_checking:
                return False

            run_checked_system_command(["sudo", "ip", "link", "add", "dev", interface, "type", "vcan"])
            _enable_can_interface(interface, bitrate)

            return False
        
        raise ValueError(f"Can interface {interface} not found")
    
    return False


def _enable_can_interface(interface: str, bitrate: int) -> None:
    """Helper function to enable a CAN/vCAN interface. Assumes the interface exists but is not up."""
    if not interface.startswith("vcan"):
        run_checked_system_command(["sudo", "ip", "link", "set", interface, "type", "can", "bitrate", str(bitrate)])
    run_checked_system_command(["sudo", "ip", "link", "set", interface, "up"])


def is_can_enabled(interface: str, bitrate: int = 1_000_000) -> bool:
    """Returns True if a CAN interface is enabled and the bitrate is correct, False otherwise."""
    return _enable_can_helper(interface, bitrate, just_checking=True)