import os
import pytest
from torchruntime.device_db import GPU
from torchruntime.configuration import _configure_internal as configure
from torchruntime.consts import AMD, NVIDIA


def create_gpu_info(vendor, device_id, device_name, is_discrete):
    if vendor == AMD:
        return GPU(AMD, "Advanced Micro Devices, Inc. [AMD/ATI]", device_id, device_name, is_discrete)
    return GPU(NVIDIA, "NVIDIA Corporation", device_id, device_name, is_discrete)


@pytest.fixture(autouse=True)
def clean_env():
    # Remove relevant environment variables before each test
    env_vars = [
        "HSA_OVERRIDE_GFX_VERSION",
        "HIP_VISIBLE_DEVICES",
        "ROC_ENABLE_PRE_VEGA",
        "HSA_ENABLE_SDMA",
        "PYTORCH_ENABLE_MPS_FALLBACK",
    ]

    # Store original values
    original_values = {}
    for var in env_vars:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values and remove any new ones
    for var in env_vars:
        if var in os.environ and var not in original_values:
            del os.environ[var]
        elif var in original_values:
            os.environ[var] = original_values[var]


def test_rocm_navi_4_settings():
    gpus = [create_gpu_info(AMD, "123", "Navi 44 XTX", True)]
    configure(gpus, "nightly/rocm6.4")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "12.0.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ
    assert "PYTORCH_ENABLE_MPS_FALLBACK" not in os.environ


def test_rocm_navi_3_settings():
    gpus = [create_gpu_info(AMD, "123", "Navi 31 XTX", True)]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "11.0.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ
    assert "PYTORCH_ENABLE_MPS_FALLBACK" not in os.environ


def test_rocm_navi_2_settings():
    gpus = [create_gpu_info(AMD, "123", "Navi 21 XTX", True)]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "10.3.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ


def test_rocm_navi_1_settings():
    gpus = [create_gpu_info(AMD, "123", "Navi 14", True)]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "10.3.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ


def test_rocm_vega_2_settings():
    gpus = [create_gpu_info(AMD, "123", "Vega 20 Radeon VII", True)]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "9.0.6"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ


def test_rocm_vega_1_settings():
    gpus = [create_gpu_info(AMD, "123", "Vega 10", True)]
    configure(gpus, "rocm5.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "9.0.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ


def test_rocm_ellesmere_settings():
    gpus = [create_gpu_info(AMD, "123", "Ellesmere RX 580", True)]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "8.0.3"
    assert os.environ.get("ROC_ENABLE_PRE_VEGA") == "1"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0"


def test_rocm_unknown_gpu_settings():
    gpus = [create_gpu_info(AMD, "123", "Unknown GPU", True)]
    configure(gpus, "rocm6.2")

    assert "ROC_ENABLE_PRE_VEGA" not in os.environ
    assert "HIP_VISIBLE_DEVICES" not in os.environ
    assert "HSA_OVERRIDE_GFX_VERSION" not in os.environ


def test_rocm_multiple_gpus_same_model():
    gpus = [create_gpu_info(AMD, "123", "Navi 31 XTX", True), create_gpu_info(AMD, "124", "Navi 31 XT", True)]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "11.0.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0,1"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ


def print_gpu_wasted_warning():
    print(
        "Fixme: This is not ideal, because we're disabling a perfectly-usable GPU. Need a way to specify which GPU to use (in separate processes), instead of trying to run both in the same python process"
    )


def test_rocm_multiple_gpus_navi3_navi2__newer_gpu_first():
    gpus = [
        create_gpu_info(AMD, "73f0", "Navi 33 [Radeon RX 7600M XT]", True),
        create_gpu_info(AMD, "73bf", "Navi 21 [Radeon RX 6800/6800 XT / 6900 XT]", True),
    ]
    configure(gpus, "rocm6.2")

    # Should use Navi 3 settings since at least one GPU is Navi 3
    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "11.0.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ

    print_gpu_wasted_warning()


def test_rocm_multiple_gpus_navi2_navi3__newer_gpu_second():
    gpus = [
        create_gpu_info(AMD, "73bf", "Navi 21 [Radeon RX 6800/6800 XT / 6900 XT]", True),
        create_gpu_info(AMD, "73f0", "Navi 33 [Radeon RX 7600M XT]", True),
    ]
    configure(gpus, "rocm6.2")

    # Should use Navi 3 settings since at least one GPU is Navi 3
    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "11.0.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "1"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ

    print_gpu_wasted_warning()


def test_rocm_multiple_gpus_vega2_navi2():
    gpus = [
        create_gpu_info(AMD, "66af", "Vega 20 [Radeon VII]", True),
        create_gpu_info(AMD, "73bf", "Navi 21 [Radeon RX 6800/6800 XT / 6900 XT]", True),
    ]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "10.3.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "1"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ

    print_gpu_wasted_warning()


def test_rocm_multiple_gpus_navi2_vega1():
    gpus = [
        create_gpu_info(AMD, "73bf", "Navi 21 [Radeon RX 6800/6800 XT / 6900 XT]", True),
        create_gpu_info(AMD, "6867", "Vega 10 XL [Radeon Pro Vega 56]", True),
    ]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "10.3.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ

    print_gpu_wasted_warning()


def test_rocm_multiple_gpus_navi3_ellesmere():
    gpus = [
        create_gpu_info(AMD, "73f0", "Navi 33 [Radeon RX 7600M XT]", True),
        create_gpu_info(AMD, "67df", "Ellesmere [Radeon RX 470/480/570/570X/580/580X/590]", True),
    ]
    configure(gpus, "rocm6.2")  # need to figure this out

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "11.0.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "0"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ

    print_gpu_wasted_warning()


@pytest.mark.parametrize(
    "device_id,device_name,hsa_version,roc_enable_pre_vega",
    [
        ("15dd", "Raven Ridge", "9.1.0", None),
        ("164c", "Lucienne", "9.0.12", None),
        ("164d", "Rembrandt", "10.3.5", None),
        ("15c8", "Phoenix2", "11.0.3", None),
        ("1586", "Strix Halo", "11.5.1", None),
    ],
)
def test_rocm_integrated_amd_gpu_variants(device_id, device_name, hsa_version, roc_enable_pre_vega):
    gpus = [create_gpu_info(AMD, device_id, device_name, False)]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == hsa_version
    if roc_enable_pre_vega:
        assert os.environ.get("ROC_ENABLE_PRE_VEGA") == roc_enable_pre_vega
    else:
        assert "ROC_ENABLE_PRE_VEGA" not in os.environ
    assert "HIP_VISIBLE_DEVICES" not in os.environ


def test_rocm_integrated_and_discrete_amd_gpus_multiple():
    gpus = [
        create_gpu_info(AMD, "15d8", "Picasso", False),
        create_gpu_info(AMD, "73bf", "Navi 21 [Radeon RX 6800/6800 XT / 6900 XT]", True),
    ]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "10.3.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "1"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ


def test_rocm_integrated_older_and_discrete_newer():
    gpus = [
        create_gpu_info(AMD, "9874", "Wani", False),
        create_gpu_info(AMD, "73bf", "Navi 21 [Radeon RX 6800/6800 XT / 6900 XT]", True),
    ]
    configure(gpus, "rocm6.2")

    assert os.environ.get("HSA_OVERRIDE_GFX_VERSION") == "10.3.0"
    assert os.environ.get("HIP_VISIBLE_DEVICES") == "1"
    assert "ROC_ENABLE_PRE_VEGA" not in os.environ


def test_rocm_empty_gpu_list():
    gpus = []
    configure(gpus, "rocm6.2")

    assert "ROC_ENABLE_PRE_VEGA" not in os.environ
    assert "HIP_VISIBLE_DEVICES" not in os.environ
    assert "HSA_OVERRIDE_GFX_VERSION" not in os.environ


def test_mac_settings(monkeypatch):
    monkeypatch.setattr("torchruntime.configuration.os_name", "Darwin")

    gpus = []
    configure(gpus, "cpu")

    assert os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") == "1"


def test_cuda_nvidia_settings_16xx():
    gpus = [create_gpu_info(NVIDIA, "2182", "TU116 [GeForce GTX 1660 Ti]", True)]
    configure(gpus, "cu124")


def test_cuda_nvidia_t600_and_later_settings():
    gpus = [create_gpu_info(NVIDIA, "1fb6", "TU117GLM [T600 Laptop GPU]", True)]
    configure(gpus, "cu124")


def test_cuda_nvidia_tesla_k40m_settings():
    gpus = [create_gpu_info(NVIDIA, "1023", "GK110BGL [Tesla K40m]", True)]
    configure(gpus, "cu124")


def test_cuda_nvidia_non_full_precision_gpu_settings():
    gpus = [create_gpu_info(NVIDIA, "2504", "GA106 [GeForce RTX 3060 Lite Hash Rate]", True)]
    configure(gpus, "cu124")
