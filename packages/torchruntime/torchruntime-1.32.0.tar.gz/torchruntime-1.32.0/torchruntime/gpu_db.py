"""
GPU identification database module.

This module consolidates GPU identification patterns for NVIDIA, AMD, and Intel GPUs.
It provides regex patterns for identifying GPU generations, architecture codes, and metadata
like shader models (for NVIDIA) and gfx numbers (for AMD).
"""

import re
from .consts import NVIDIA, AMD, INTEL


# =============================================================================
# NVIDIA GPU Identification
# =============================================================================

# NVIDIA Architecture patterns based on GPU codes
# References: https://www.techpowerup.com/gpu-specs/
# Architecture -> Shader Model (Compute Capability)
KEPLER_DEVICES = re.compile(r"\b(gk\d+\w*)\b", re.IGNORECASE)  # sm3.7
MAXWELL_DEVICES = re.compile(r"\b(gm\d+\w*)\b", re.IGNORECASE)  # sm5
PASCAL_DEVICES = re.compile(r"\b(gp\d+\w*)\b", re.IGNORECASE)  # sm6
VOLTA_DEVICES = re.compile(r"\b(gv\d+\w*)\b", re.IGNORECASE)  # sm7
TURING_DEVICES = re.compile(r"\b(tu\d+\w*)\b", re.IGNORECASE)  # sm7.5
AMPERE_DEVICES = re.compile(r"\b(ga\d+\w*)\b", re.IGNORECASE)  # sm8.6
HOPPER_DEVICES = re.compile(r"\b(gh\d+\w*)\b", re.IGNORECASE)  # sm9.0 (Grace Hopper)
ADA_LOVELACE_DEVICES = re.compile(r"\b(ad\d+\w*)\b", re.IGNORECASE)  # sm8.9
BLACKWELL_DEVICES = re.compile(r"\b(?:gb\d+\w*|5060|5070|5080|5090)\b", re.IGNORECASE)  # sm10, sm12

# Map architecture patterns to compute capability versions
NVIDIA_ARCH_MAP = {
    BLACKWELL_DEVICES: 12.0,
    ADA_LOVELACE_DEVICES: 8.9,
    HOPPER_DEVICES: 9.0,
    AMPERE_DEVICES: 8.6,
    TURING_DEVICES: 7.5,
    VOLTA_DEVICES: 7.0,
    PASCAL_DEVICES: 6.0,
    MAXWELL_DEVICES: 5.0,
    KEPLER_DEVICES: 3.7,
}


def get_nvidia_arch(device_names):
    """
    Determine NVIDIA GPU architecture version (compute capability) from device names.

    Args:
        device_names (iterable of str): GPU device names to analyze

    Returns:
        float: Compute capability version (e.g., 8.9 for Ada Lovelace), or 0 if unknown
    """
    for arch_regex, arch_version in NVIDIA_ARCH_MAP.items():
        if any(arch_regex.search(device_name) for device_name in device_names):
            return arch_version
    return 0


# =============================================================================
# AMD GPU Identification
# =============================================================================

# AMD Integrated GPU mapping: PCI Device ID -> (Name, GFX Target, HSA Version)
AMD_INTEGRATED_GPUS = {
    # RDNA 1 (gfx10)
    "1636": ("Renoir", "gfx90c", "9.0.12"),
    "164c": ("Lucienne", "gfx90c", "9.0.12"),
    "1638": ("Cezanne", "gfx90c", "9.0.12"),
    "15e7": ("Barcelo", "gfx90c", "9.0.12"),
    "163f": ("VanGogh", "gfx1033", "10.3.3"),
    "164d": ("Rembrandt", "gfx1035", "10.3.5"),
    "1681": ("Rembrandt", "gfx1035", "10.3.5"),
    "164e": ("Raphael", "gfx1036", "10.3.6"),
    "1506": ("Mendocino", "gfx1037", "10.3.7"),
    "13c0": ("Granite Ridge", "gfx1030", "10.3.0"),
    # RDNA 2/3 (gfx11)
    "164f": ("Phoenix", "gfx1103", "11.0.1"),
    "15bf": ("Phoenix1", "gfx1103", "11.0.3"),
    "15c8": ("Phoenix2", "gfx1103", "11.0.3"),
    "1900": ("Phoenix3", "gfx1103", "11.0.4"),
    "1901": ("Phoenix4", "gfx1103", "11.0.4"),
    "150e": ("Strix", "gfx1150", "11.5.0"),
    "1586": ("Strix Halo", "gfx1151", "11.5.1"),
    "1114": ("Krackan", "gfx1151", "11.5.1"),
    # Older architectures
    "15dd": ("Raven Ridge", "gfx902", "9.1.0"),
    "15d8": ("Picasso", "gfx903", "9.1.0"),
}


def get_amd_gfx_info(device_id):
    """
    Get AMD GPU GFX information from device ID.

    Args:
        device_id (str): PCI device ID (hex string)

    Returns:
        tuple: (device_name, gfx_target, hsa_version) or ("", "", "") if not found
    """
    return AMD_INTEGRATED_GPUS.get(device_id, ("", "", ""))


# =============================================================================
# GPU Device Type Identification
# =============================================================================

# Build NVIDIA discrete pattern from architecture patterns (Kepler and newer only)
# This covers GPUs from 2012 onwards with compute capability 3.7+
_NVIDIA_ARCH_PATTERNS = r"|".join(pattern.pattern.strip(r"\b()").strip(r"(?:)") for pattern in NVIDIA_ARCH_MAP.keys())
NVIDIA_DISCRETE_PATTERN = re.compile(
    rf"\b(?:{_NVIDIA_ARCH_PATTERNS})\b",
    re.IGNORECASE,
)

# AMD discrete pattern - matches product line names
AMD_DISCRETE_PATTERN = re.compile(
    r"\b(?:radeon|instinct|fire|rage|polaris|aldebaran|navi)\b",
    re.IGNORECASE,
)

GPU_DEVICES = {
    AMD: {
        "discrete": AMD_DISCRETE_PATTERN,
        "integrated": AMD_INTEGRATED_GPUS,
        "exclude": re.compile(r"\b(?:audio|bridge|arden|oberon|stoney|wani|usb|switch)\b", re.IGNORECASE),
    },
    INTEL: {
        "discrete": re.compile(r"\b(?:arc)\b", re.IGNORECASE),
        "integrated": re.compile(r"\b(?:iris|hd graphics|uhd graphics)\b", re.IGNORECASE),
        "exclude": re.compile(r"\b(?:audio|bridge)\b", re.IGNORECASE),
    },
    NVIDIA: {
        "discrete": NVIDIA_DISCRETE_PATTERN,
        "exclude": re.compile(
            r"\b(?:audio|switch|pci|memory|smbus|ide|co-processor|bridge|usb|sata|controller)\b",
            re.IGNORECASE,
        ),
    },
}


def is_gpu_vendor(vendor_id):
    """
    Check if a vendor ID corresponds to a known GPU vendor.

    Args:
        vendor_id (str): PCI vendor ID

    Returns:
        bool: True if vendor is AMD, Intel, or NVIDIA
    """
    return vendor_id in GPU_DEVICES


def get_gpu_type(vendor_id, device_id, device_name):
    """
    Determine GPU type (discrete, integrated, or none) for a given device.

    Args:
        vendor_id (str): PCI Vendor ID
        device_id (str): PCI Device ID
        device_name (str): PCI Device Name

    Returns:
        str: "DISCRETE", "INTEGRATED", or "NONE"
    """

    def matches(pattern):
        if isinstance(pattern, re.Pattern):
            return pattern.search(device_name)
        if isinstance(pattern, dict):
            return device_id in pattern
        return False

    vendor_devices = GPU_DEVICES.get(vendor_id)
    if not vendor_devices:
        return "NONE"

    discrete_devices = vendor_devices.get("discrete")
    integrated_devices = vendor_devices.get("integrated")
    exclude_devices = vendor_devices.get("exclude")

    # Check exclusions first
    if matches(exclude_devices):
        return "NONE"

    # Check integrated before discrete to avoid misclassification
    # (e.g., "Radeon" in integrated APU names)
    if matches(integrated_devices):
        return "INTEGRATED"

    if matches(discrete_devices):
        return "DISCRETE"

    return "NONE"
