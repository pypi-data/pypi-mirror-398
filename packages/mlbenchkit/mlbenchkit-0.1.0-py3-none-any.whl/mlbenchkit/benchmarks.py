import time


def _sync_device(device: str):
    if device == "cuda":
        import torch
        torch.cuda.synchronize()
    elif device == "mps":
        import torch
        torch.empty(1, device="mps").cpu()


def torch_matmul_bench(N=2048, dtype="float32", device="cpu", warmup=20, iters=50):
    # Lazy import
    import torch

    dtype_map = {
        "float32": torch.float32,
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
    }
    tdtype = dtype_map.get(dtype, torch.float32)

    a = torch.randn((N, N), device=device, dtype=tdtype)
    b = torch.randn((N, N), device=device, dtype=tdtype)

    # warmup
    for _ in range(warmup):
        _ = a @ b
    _sync_device(device)

    t0 = time.perf_counter()
    for _ in range(iters):
        _ = a @ b
    _sync_device(device)
    t1 = time.perf_counter()

    avg_ms = (t1 - t0) * 1000 / iters

    flops = 2 * (N ** 3)
    t_sec = (t1 - t0) / iters
    tflops = (flops / t_sec) / 1e12

    out = {"name": "torch_matmul", "device": device, "N": N, "dtype": dtype, "avg_ms": avg_ms, "tflops": tflops}

    if device == "cuda":
        idx = torch.cuda.current_device()
        out["vram_allocated_gb"] = round(torch.cuda.memory_allocated(idx) / (1024 ** 3), 4)
        out["vram_reserved_gb"] = round(torch.cuda.memory_reserved(idx) / (1024 ** 3), 4)
        out["vram_max_allocated_gb"] = round(torch.cuda.max_memory_allocated(idx) / (1024 ** 3), 4)
        out["vram_max_reserved_gb"] = round(torch.cuda.max_memory_reserved(idx) / (1024 ** 3), 4)

    return out


def sklearn_rf_train_bench(n_samples=5000, n_features=50, n_estimators=200, random_state=0):
    # Optional dependency
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier

    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=min(10, n_features),
        n_redundant=0,
        random_state=random_state,
    )
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,  # use all cores
    )

    t0 = time.perf_counter()
    model.fit(X, y)
    t1 = time.perf_counter()

    return {
        "name": "sklearn_rf_train",
        "n_samples": n_samples,
        "n_features": n_features,
        "n_estimators": n_estimators,
        "seconds": (t1 - t0),
    }
