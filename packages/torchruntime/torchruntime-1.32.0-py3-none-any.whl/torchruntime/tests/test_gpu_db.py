"""
Tests for the gpu_db module to ensure GPU identification patterns work correctly.
"""

import pytest
from torchruntime.gpu_db import (
    get_nvidia_arch,
    get_amd_gfx_info,
    get_gpu_type,
    is_gpu_vendor,
    NVIDIA,
    AMD,
    INTEL,
)


class TestNvidiaArchDetection:
    """Test NVIDIA GPU architecture detection."""

    def test_kepler_detection(self):
        device_names = ["NVIDIA GeForce GK104", "GeForce GTX 780 Ti"]
        assert get_nvidia_arch(device_names) == 3.7

    def test_maxwell_detection(self):
        device_names = ["NVIDIA GeForce GM107", "GeForce GTX 950"]
        assert get_nvidia_arch(device_names) == 5.0

    def test_pascal_detection(self):
        device_names = ["NVIDIA GeForce GP104", "GeForce GTX 1080"]
        assert get_nvidia_arch(device_names) == 6.0

    def test_volta_detection(self):
        device_names = ["NVIDIA Tesla GV100"]
        assert get_nvidia_arch(device_names) == 7.0

    def test_turing_detection(self):
        device_names = ["NVIDIA GeForce TU116", "GeForce GTX 1660"]
        assert get_nvidia_arch(device_names) == 7.5

    def test_ampere_detection(self):
        device_names = ["NVIDIA GeForce GA102", "GeForce RTX 3080"]
        assert get_nvidia_arch(device_names) == 8.6

    def test_hopper_detection(self):
        device_names = ["NVIDIA GH100", "H100 PCIe", "H200 SXM 141GB"]
        assert get_nvidia_arch(device_names) == 9.0

    def test_ada_lovelace_detection(self):
        device_names = ["NVIDIA GeForce AD102", "GeForce RTX 4090"]
        assert get_nvidia_arch(device_names) == 8.9

    def test_blackwell_detection(self):
        device_names = ["NVIDIA GeForce RTX 5090"]
        assert get_nvidia_arch(device_names) == 12.0

    def test_blackwell_gb_code_detection(self):
        device_names = ["NVIDIA GB100"]
        assert get_nvidia_arch(device_names) == 12.0

    def test_unknown_architecture(self):
        device_names = ["NVIDIA GeForce Unknown"]
        assert get_nvidia_arch(device_names) == 0


class TestAMDGfxInfo:
    """Test AMD GPU GFX information retrieval."""

    def test_renoir_gfx(self):
        name, gfx, hsa = get_amd_gfx_info("1636")
        assert name == "Renoir"
        assert gfx == "gfx90c"
        assert hsa == "9.0.12"

    def test_phoenix_gfx(self):
        name, gfx, hsa = get_amd_gfx_info("164f")
        assert name == "Phoenix"
        assert gfx == "gfx1103"
        assert hsa == "11.0.1"

    def test_strix_gfx(self):
        name, gfx, hsa = get_amd_gfx_info("150e")
        assert name == "Strix"
        assert gfx == "gfx1150"
        assert hsa == "11.5.0"

    def test_unknown_device_id(self):
        name, gfx, hsa = get_amd_gfx_info("9999")
        assert name == ""
        assert gfx == ""
        assert hsa == ""


class TestGPUTypeDetection:
    """Test GPU type detection (discrete, integrated, none)."""

    def test_nvidia_discrete_by_brand(self):
        # Note: In real PCI IDs database, GPU names include architecture codes
        # Testing with realistic device names that include arch codes
        assert get_gpu_type(NVIDIA, "2704", "AD103 [GeForce RTX 4080]") == "DISCRETE"
        assert get_gpu_type(NVIDIA, "1cb1", "GP107GL [Quadro P1000]") == "DISCRETE"
        assert get_gpu_type(NVIDIA, "1db4", "GV100GL [Tesla V100]") == "DISCRETE"

    def test_nvidia_discrete_by_arch_code(self):
        assert get_gpu_type(NVIDIA, "1234", "NVIDIA GP104") == "DISCRETE"
        assert get_gpu_type(NVIDIA, "1234", "NVIDIA TU116") == "DISCRETE"
        assert get_gpu_type(NVIDIA, "1234", "NVIDIA GA102") == "DISCRETE"
        assert get_gpu_type(NVIDIA, "1234", "NVIDIA AD103") == "DISCRETE"
        assert get_gpu_type(NVIDIA, "1234", "NVIDIA GH100") == "DISCRETE"

    def test_nvidia_excluded_devices(self):
        assert get_gpu_type(NVIDIA, "1234", "NVIDIA Audio Controller") == "NONE"
        assert get_gpu_type(NVIDIA, "1234", "NVIDIA USB Controller") == "NONE"

    def test_amd_discrete_by_name(self):
        assert get_gpu_type(AMD, "1234", "AMD Radeon RX 7900 XT") == "DISCRETE"
        assert get_gpu_type(AMD, "1234", "AMD Navi 31") == "DISCRETE"
        assert get_gpu_type(AMD, "1234", "AMD Instinct MI300") == "DISCRETE"

    def test_amd_integrated_by_device_id(self):
        assert get_gpu_type(AMD, "1636", "AMD Renoir") == "INTEGRATED"
        assert get_gpu_type(AMD, "164f", "AMD Phoenix") == "INTEGRATED"
        assert get_gpu_type(AMD, "150e", "AMD Strix") == "INTEGRATED"

    def test_amd_excluded_devices(self):
        assert get_gpu_type(AMD, "1234", "AMD Audio Device") == "NONE"
        assert get_gpu_type(AMD, "1234", "AMD USB Controller") == "NONE"

    def test_intel_discrete(self):
        assert get_gpu_type(INTEL, "1234", "Intel Arc A770") == "DISCRETE"

    def test_intel_integrated(self):
        assert get_gpu_type(INTEL, "1234", "Intel Iris Xe Graphics") == "INTEGRATED"
        assert get_gpu_type(INTEL, "1234", "Intel HD Graphics 620") == "INTEGRATED"
        assert get_gpu_type(INTEL, "1234", "Intel UHD Graphics 630") == "INTEGRATED"

    def test_intel_excluded_devices(self):
        assert get_gpu_type(INTEL, "1234", "Intel Audio Device") == "NONE"


class TestGPUVendorCheck:
    """Test GPU vendor identification."""

    def test_known_vendors(self):
        assert is_gpu_vendor(NVIDIA) is True
        assert is_gpu_vendor(AMD) is True
        assert is_gpu_vendor(INTEL) is True

    def test_unknown_vendor(self):
        assert is_gpu_vendor("9999") is False


class TestPatternConstruction:
    """Test that patterns are correctly built without duplication."""

    def test_nvidia_discrete_pattern_includes_all_architectures(self):
        """Verify NVIDIA_DISCRETE_PATTERN includes all architecture codes (Kepler+)."""
        from torchruntime.gpu_db import NVIDIA_DISCRETE_PATTERN

        # Test that all architecture patterns are included (Kepler and newer)
        arch_codes = ["gk104", "gm107", "gp104", "gv100", "tu116", "ga102", "gh100", "ad102", "gb100"]
        for code in arch_codes:
            assert NVIDIA_DISCRETE_PATTERN.search(code), f"Pattern should match {code}"

        # Test Blackwell model numbers
        models = ["5060", "5070", "5080", "5090"]
        for model in models:
            assert NVIDIA_DISCRETE_PATTERN.search(model), f"Pattern should match {model}"

        # Brand names alone (without arch codes) are NOT supported for Kepler+ only detection
        # Pre-Kepler GPUs like "GeForce 8800 GTX" (G80) should NOT match
        assert not NVIDIA_DISCRETE_PATTERN.search("GeForce 8800 GTX")
        assert not NVIDIA_DISCRETE_PATTERN.search("GeForce GTX 580")  # GF110, pre-Kepler

    def test_amd_discrete_pattern_separate(self):
        """Verify AMD has a separate discrete pattern."""
        from torchruntime.gpu_db import AMD_DISCRETE_PATTERN

        # Should match AMD product lines
        assert AMD_DISCRETE_PATTERN.search("Radeon RX 7900")
        assert AMD_DISCRETE_PATTERN.search("Instinct MI300")
        assert AMD_DISCRETE_PATTERN.search("Navi 31")

        # Should not match integrated codenames
        assert not AMD_DISCRETE_PATTERN.search("Phoenix")
        assert not AMD_DISCRETE_PATTERN.search("Renoir")
