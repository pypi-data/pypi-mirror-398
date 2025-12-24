import platform
import socket

import psutil
import cpuinfo

from .utils import bytes_to_gb


def cpu_details():
    ci = cpuinfo.get_cpu_info()
    freq = psutil.cpu_freq()

    return {
        "cpu_model": ci.get("brand_raw", "Unknown CPU"),
        "cpu_advertised": ci.get("hz_advertised_friendly", None) or ci.get("hz_actual_friendly", "Unknown"),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "cpu_freq_current_mhz": round(freq.current, 1) if freq else None,
        "cpu_freq_max_mhz": round(freq.max, 1) if (freq and freq.max) else None,
        "cpu_freq_min_mhz": round(freq.min, 1) if (freq and freq.min) else None,
    }


def ram_details():
    vm = psutil.virtual_memory()
    return {
        "ram_total_gb": round(bytes_to_gb(vm.total), 2),
        "ram_available_gb": round(bytes_to_gb(vm.available), 2),
        "ram_used_gb": round(bytes_to_gb(vm.used), 2),
        "ram_percent": vm.percent,
    }


def torch_accelerator_details():
    # Import torch lazily so toolkit works without torch installed
    try:
        import torch
    except Exception:
        return {"device": "none", "name": None, "note": "torch not installed"}

    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"

    acc = {
        "device": device,
        "torch_version": getattr(torch, "__version__", None),
        "cuda_version": getattr(torch.version, "cuda", None),
        "cudnn_version": torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None,
    }

    if device == "cuda":
        idx = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(idx)
        acc.update({
            "device_index": idx,
            "name": props.name,
            "compute_capability": f"{props.major}.{props.minor}",
            "vram_total_gb": round(props.total_memory / (1024 ** 3), 2),
            "multi_processor_count": getattr(props, "multi_processor_count", None),
            "warp_size": getattr(props, "warp_size", None),
        })
    elif device == "mps":
        # Apple GPU uses unified memory; dedicated VRAM not exposed in PyTorch
        acc.update({
            "name": "Apple Silicon (MPS)",
            "note": "Apple GPU uses unified memory; dedicated VRAM size is not exposed via PyTorch.",
        })
    else:
        acc.update({"name": "CPU"})

    return acc


def system_specs():
    specs = {
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "architecture": platform.machine(),
    }
    specs.update(cpu_details())
    specs.update(ram_details())
    return specs
