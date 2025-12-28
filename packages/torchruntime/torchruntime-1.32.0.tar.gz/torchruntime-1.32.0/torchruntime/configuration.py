import os

from .consts import AMD
from .device_db import get_gpus
from .gpu_db import get_amd_gfx_info
from .platform_detection import get_torch_platform, os_name


def configure():
    gpu_infos = get_gpus()
    torch_platform = get_torch_platform(gpu_infos)

    _configure_internal(gpu_infos, torch_platform)


def _configure_internal(gpu_infos, torch_platform):
    if "rocm" in torch_platform:
        check_rocm_permissions()
        set_rocm_env_vars(gpu_infos, torch_platform)
    elif os_name == "Darwin":
        set_mac_env_vars(gpu_infos, torch_platform)


def check_rocm_permissions():
    if not os.access("/dev/kfd", os.W_OK):
        print(
            """#########################################################################
            #                    No write access to /dev/kfd !                      #
            #########################################################################

            Without this, the ROCm driver will probably not be able to initialize the GPU and torch will use the CPU for rendering.

            Follow the instructions on this site to configure access to /dev/kfd:
            https://github.com/easydiffusion/easydiffusion/wiki/AMD-on-Linux#access-permissions"""
        )


def set_rocm_env_vars(gpu_infos, torch_platform):
    if not gpu_infos:
        return

    discrete_devices, integrated_devices = [], []
    for device in gpu_infos:
        if device.is_discrete:
            discrete_devices.append(device)
        else:
            integrated_devices.append(device)

    if discrete_devices:
        return _set_rocm_vars_for_discrete(discrete_devices, all_gpu_info=gpu_infos)

    return _set_rocm_vars_for_integrated(integrated_devices)


def _set_rocm_vars_for_discrete(gpu_infos, all_gpu_info):
    device_names = [gpu.device_name for gpu in gpu_infos]
    env = {}

    # interesting reading:
    # gfx config from: https://web.archive.org/web/20241228163540/https://llvm.org/docs/AMDGPUUsage.html#processors
    # more info: https://web.archive.org/web/20241209013717/https://discuss.linuxcontainers.org/t/rocm-and-pytorch-on-amd-apu-or-gpu-ai/19743
    # this thread is great for understanding the status of torch support for RDNA 1 (i.e. 5000 series): https://github.com/ROCm/ROCm/issues/2527
    # past settings from: https://github.com/easydiffusion/easydiffusion/blob/20d77a85a1ed766ece0cc4b6a55dca003bce262c/scripts/check_modules.py#L405-L420

    # Determine GPU generations present
    has_navi4 = any("Navi 4" in device_name for device_name in device_names)  # RX 9000 series
    has_navi3 = any("Navi 3" in device_name for device_name in device_names)  # RX 7000 series
    has_navi2 = any("Navi 2" in device_name for device_name in device_names)  # RX 6000 series
    has_navi1 = any("Navi 1" in device_name for device_name in device_names)  # RX 5000 series
    has_vega2 = any("Vega 2" in device_name for device_name in device_names)  # Radeon VII etc
    has_vega1 = any("Vega 1" in device_name for device_name in device_names)  # Radeon RX Vega 56 etc
    has_ellesmere = any("Ellesmere" in device_name for device_name in device_names)  # RX 570/580/Polaris etc

    # Select GPU generation settings based on priority
    if has_navi4:
        env["HSA_OVERRIDE_GFX_VERSION"] = "12.0.0"
        # Find the index of the first Navi 4 GPU
        env["HIP_VISIBLE_DEVICES"] = _visible_device_ids(all_gpu_info, "Navi 4")
    elif has_navi3:
        env["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
        # Find the index of the first Navi 3 GPU
        env["HIP_VISIBLE_DEVICES"] = _visible_device_ids(all_gpu_info, "Navi 3")
    elif has_navi2:
        env["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"
        # Find the index of the first Navi 2 GPU
        env["HIP_VISIBLE_DEVICES"] = _visible_device_ids(all_gpu_info, "Navi 2")
    elif has_navi1:
        env["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"
        # env["HSA_ENABLE_SDMA"] = "0"  # uncomment this if facing errors like in https://github.com/ROCm/ROCm/issues/2616
        env["HIP_VISIBLE_DEVICES"] = _visible_device_ids(all_gpu_info, "Navi 1")
    elif has_vega2:
        env["HSA_OVERRIDE_GFX_VERSION"] = "9.0.6"
        env["HIP_VISIBLE_DEVICES"] = _visible_device_ids(all_gpu_info, "Vega 2")
    elif has_vega1:
        # # https://discord.com/channels/1014774730907209781/1329021732794667068/1329261488300363776
        env["HSA_OVERRIDE_GFX_VERSION"] = "9.0.0"
        env["HIP_VISIBLE_DEVICES"] = _visible_device_ids(all_gpu_info, "Vega 1")
    elif has_ellesmere:
        env["HSA_OVERRIDE_GFX_VERSION"] = "8.0.3"  # https://github.com/ROCm/ROCm/issues/1659
        env["ROC_ENABLE_PRE_VEGA"] = "1"
        env["HIP_VISIBLE_DEVICES"] = _visible_device_ids(all_gpu_info, "Ellesmere")
    else:
        env["ROC_ENABLE_PRE_VEGA"] = "1"
        print(f"[WARNING] Unrecognized AMD graphics card: {device_names}")
        return

    _set_env_vars(env)


def _set_rocm_vars_for_integrated(gpu_infos):
    gpu = gpu_infos[0]
    env = {}

    family_name, gfx_id, hsa_version = get_amd_gfx_info(gpu.device_id)
    env["HSA_OVERRIDE_GFX_VERSION"] = hsa_version

    if gfx_id.startswith("gfx8"):
        env["ROC_ENABLE_PRE_VEGA"] = "1"

    _set_env_vars(env)


def set_mac_env_vars(gpu_infos, torch_platform):
    _set_env_vars({"PYTORCH_ENABLE_MPS_FALLBACK": "1"})


def _visible_device_ids(gpu_infos, family_name):
    ids = [str(i) for i, gpu in enumerate(gpu_infos) if family_name in gpu.device_name]
    return ",".join(ids)


def _set_env_vars(env):
    for k, v in env.items():
        print(f"[INFO] Setting env variable {k}={v}")
        os.environ[k] = v
