import os
import re
import json
import sqlite3
import platform
import subprocess
from dataclasses import dataclass

from .consts import NVIDIA, AMD, INTEL
from .gpu_db import is_gpu_vendor, get_gpu_type

DEVICE_DB_FILE = "gpu_pci_ids.db"  # this file will only include AMD, NVIDIA and Discrete Intel GPUs


@dataclass
class GPU:
    vendor_id: str
    vendor_name: str
    device_id: str
    device_name: str
    is_discrete: bool


os_name = platform.system()


def get_windows_output():
    try:
        command = [
            "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            "-Command",
            "Get-WmiObject Win32_VideoController | ForEach-Object { $_.PNPDeviceID }",
        ]
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return ""


def get_linux_output():
    try:
        return subprocess.check_output(["lspci", "-nn"], text=True)
    except FileNotFoundError:
        return ""


def get_macos_output():
    try:
        return subprocess.check_output(["system_profiler", "-json", "SPDisplaysDataType"], text=True)
    except subprocess.CalledProcessError:
        return ""


def parse_windows_output(output):
    pci_ids = []
    for line in output.splitlines():
        match = re.search(r"VEN_(\w+)&DEV_(\w+)", line, re.IGNORECASE)
        if match:
            vendor_id = match.group(1).lower()
            device_id = match.group(2).lower()
            pci_ids.append((vendor_id, device_id))
    return list(pci_ids)


def parse_linux_output(output):
    pci_ids = []
    for line in output.splitlines():
        match = re.search(r"\[(\w+):(\w+)\]", line)
        if match:
            vendor_id = match.group(1).lower()
            device_id = match.group(2).lower()
            pci_ids.append((vendor_id, device_id))
    return list(pci_ids)


def parse_macos_output(output):
    pci_ids = []
    try:
        data = json.loads(output)
        displays = data.get("SPDisplaysDataType", [])
        for display in displays:
            vendor_raw = display.get("spdisplays_vendor", "")
            device_id_raw = display.get("spdisplays_device-id", "")
            if device_id_raw and vendor_raw:
                device_id = device_id_raw.replace("0x", "").lower()
                if "Intel" in vendor_raw:
                    vendor_id = "8086"
                else:
                    match = re.search(r"\((0x\w+)\)", vendor_raw)
                    if match:
                        vendor_id = match.group(1).replace("0x", "").lower()
                    else:
                        continue
                pci_ids.append((vendor_id, device_id))
    except json.JSONDecodeError:
        pass
    return list(pci_ids)


def get_pci_ids():
    if os_name == "Windows":
        output = get_windows_output()
        return parse_windows_output(output)
    elif os_name == "Linux":
        output = get_linux_output()
        return parse_linux_output(output)
    elif os_name == "Darwin":  # macOS
        output = get_macos_output()
        return parse_macos_output(output)
    else:
        return []


def get_device_infos(pci_ids):
    """
    Reads the given SQLite database file and queries the `pci_ids` table
    for matching vendor_id and device_id.

    Args:
        db_file_name (str): Path to the SQLite database file.
        pci_ids (list of tuples): List of (vendor_id, device_id) pairs to match.

    Returns:
        list of `torchruntime.device_db.GPU` objects
    """
    result = []

    # Establish connection to the database
    db_path = os.path.join(os.path.dirname(__file__), DEVICE_DB_FILE)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create a query to retrieve matching rows
        query = """
        SELECT vendor_id, vendor_name, device_id, device_name, is_discrete
        FROM pci_ids
        WHERE vendor_id = ? AND device_id = ?
        """

        # Execute query for each (vendor_id, device_id) in pci_ids
        for vendor_id, device_id in pci_ids:
            cursor.execute(query, (vendor_id, device_id))
            rows = cursor.fetchall()
            for row in rows:
                gpu = GPU(*row)
                gpu.is_discrete = bool(gpu.is_discrete)
                result.append(gpu)

    finally:
        # Close the database connection
        conn.close()

    return result


def get_gpus():
    pci_ids = get_pci_ids()
    return get_device_infos(pci_ids)
