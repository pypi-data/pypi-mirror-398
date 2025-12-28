"""
Multi-device VPCS command execution tool using telnetlib3 with threading.
Supports concurrent execution of multiple command groups across multiple VPCS devices.
"""

import json
import os
import threading
from time import sleep
from typing import Any

from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from telnetlib3 import Telnet

from gns3_copilot.log_config import setup_tool_logger
from gns3_copilot.public_model import get_device_ports_from_topology

logger = setup_tool_logger("vpcs_multi_commands")


class VPCSMultiCommands(BaseTool):
    """
    A tool to execute multiple command groups across multiple VPCS devices concurrently.
    Supports parallel execution with threading for improved performance.

    Input should be a JSON array containing command group objects.
    Example input:
        [
            {
                "device_name": "PC1",
                "commands": ["ip 10.10.0.12/24 10.10.0.254", "ping 10.10.0.254"]
            },
            {
                "device_name": "PC2",
                "commands": ["ip 10.10.0.13/24 10.10.0.254"]
            }
        ]

    Returns a list of results, one for each command group.
    """

    name: str = "execute_vpcs_multi_commands"
    description: str = """
    Executes multiple command groups across multiple VPCS devices concurrently using telnetlib3.
    Supports parallel execution with threading for improved performance.

    Input should be a JSON array containing command group objects with device_name and commands.
    Example input:
        [
            {
                "device_name": "PC1",
                "commands": ["ip 10.10.0.12/24 10.10.0.254", "ping 10.10.0.254"]
            },
            {
                "device_name": "PC2",
                "commands": ["ip 10.10.0.13/24 10.10.0.254"]
            }
        ]

    Returns a list of results, each containing device_name, status, output, and commands.
    """

    def _connect_and_execute_commands(
        self,
        device_name: str,
        commands: list[str],
        results_list: list[Any],
        index: int,
        device_ports: dict[str, Any],
        gns3_host: str,
    ) -> None:
        """Internal method to connect to device and execute multiple commands"""

        # Check if device has port information
        if device_name not in device_ports:
            results_list[index] = {
                "device_name": device_name,
                "status": "error",
                "output": f"Device '{device_name}' not found in topology or missing console port",
                "commands": commands,
            }
            return

        port = device_ports[device_name]["port"]
        host = gns3_host

        tn = Telnet()
        try:
            tn.open(host=host, port=port, timeout=30)

            # Initialize connection
            tn.write(b"\n")
            sleep(0.5)
            tn.write(b"\n")
            sleep(0.5)
            tn.write(b"\n")
            sleep(0.5)
            tn.write(b"\n")
            sleep(0.5)
            tn.expect([rb"PC\d+>"])

            # Execute all commands and merge output
            combined_output = ""
            for command in commands:
                tn.write(command.encode(encoding="ascii") + b"\n")
                sleep(5)
                tn.expect([rb"PC\d+>"])
                output = tn.read_very_eager().decode("utf-8")
                combined_output += output

            # Add result to list
            results_list[index] = {
                "device_name": device_name,
                "status": "success",
                "output": combined_output,
                "commands": commands,
            }

        except Exception as e:
            results_list[index] = {
                "device_name": device_name,
                "status": "error",
                "output": str(e),
                "commands": commands,
            }
        finally:
            tn.close()

    def _run(
        self, tool_input: str, run_manager: CallbackManagerForToolRun | None = None
    ) -> list[dict[str, Any]]:
        """Main method to execute multi-device multi-commands"""

        try:
            cmd_groups = json.loads(tool_input)
            if not isinstance(cmd_groups, list):
                return [
                    {"error": "Input must be a JSON array of command group objects"}
                ]
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON input: %s", e)
            return [{"error": f"Invalid JSON input: {e}"}]

        # Extract all device names from input using set comprehension
        device_names = {cmd_group["device_name"] for cmd_group in cmd_groups}

        # Get device port mapping
        device_ports = get_device_ports_from_topology(list(device_names))

        # Get host IP from environment variable
        gns3_host = os.getenv("GNS3_SERVER_HOST", "127.0.0.1")

        # Initialize results list (pre-allocate space for concurrent writes)
        results: list[dict[str, Any]] = [{} for _ in range(len(cmd_groups))]
        threads = []

        # Create thread for each command group
        for i, cmd_group in enumerate(cmd_groups):
            thread = threading.Thread(
                target=self._connect_and_execute_commands,
                args=(
                    cmd_group["device_name"],
                    cmd_group["commands"],
                    results,
                    i,
                    device_ports,
                    gns3_host,
                ),
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        logger.info(
            "Multi-device command execution completed. Results: %s",
            json.dumps(results, indent=2, ensure_ascii=False),
        )

        return results


if __name__ == "__main__":
    # Example usage
    command_groups = [
        {
            "device_name": "PC1",
            "commands": ["ip 10.10.0.12/24 10.10.0.254", "ping 10.10.0.254"],
        },
        {"device_name": "PC2", "commands": ["ip 10.10.0.13/24 10.10.0.254"]},
        {
            "device_name": "PC3",
            "commands": ["ip 10.20.0.22/24 10.20.0.254", "ping 10.20.0.254"],
        },
        {"device_name": "PC4", "commands": ["ip 10.20.0.23/24 10.20.0.254"]},
    ]

    exe_cmd = VPCSMultiCommands()
    result = exe_cmd._run(tool_input=json.dumps(command_groups))
    print("Execution results:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
