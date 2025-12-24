import argparse
import json
import os
from datetime import datetime

from .specs import system_specs, torch_accelerator_details
from .benchmarks import torch_matmul_bench, sklearn_rf_train_bench


def _pick_torch_device(acc):
    d = acc.get("device", "none")
    if d in ("cuda", "mps"):
        return d
    return "cpu"


def cmd_specs(args):
    out = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "specs": system_specs(),
        "accelerator": torch_accelerator_details(),
    }
    print(json.dumps(out, indent=2))


def cmd_run(args):
    specs = system_specs()
    acc = torch_accelerator_details()
    device = _pick_torch_device(acc)

    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "specs": specs,
        "accelerator": acc,
        "benchmarks": [],
    }

    # Torch benchmarks (if torch installed)
    if acc.get("device") != "none":
        # CPU matmul
        results["benchmarks"].append(
            torch_matmul_bench(N=args.cpu_N, dtype="float32", device="cpu", warmup=args.warmup, iters=args.iters)
        )

        # Accelerator matmul (CUDA/MPS)
        if device in ("cuda", "mps"):
            results["benchmarks"].append(
                torch_matmul_bench(N=args.gpu_N, dtype=args.gpu_dtype, device=device, warmup=args.warmup, iters=args.iters)
            )

    # sklearn benchmark (if installed)
    if args.with_sklearn:
        try:
            results["benchmarks"].append(
                sklearn_rf_train_bench(
                    n_samples=args.rf_samples,
                    n_features=args.rf_features,
                    n_estimators=args.rf_estimators,
                    random_state=0,
                )
            )
        except Exception as e:
            results["benchmarks"].append({"name": "sklearn_rf_train", "error": str(e)})

    # Save JSON
    os.makedirs(args.out_dir, exist_ok=True)
    fname = args.out_file
    if not fname:
        host = specs.get("hostname", "machine")
        fname = f"mlbench_{host}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
    path = os.path.join(args.out_dir, fname)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved: {path}")
    print(json.dumps(results["benchmarks"], indent=2))


def main():
    p = argparse.ArgumentParser(prog="mlbench", description="Cross-platform ML benchmarking toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_specs = sub.add_parser("specs", help="Print machine specs + accelerator info")
    p_specs.set_defaults(func=cmd_specs)

    p_run = sub.add_parser("run", help="Run benchmark suite and save JSON")
    p_run.add_argument("--out-dir", default="bench_outputs", help="Output directory for JSON results")
    p_run.add_argument("--out-file", default=None, help="Optional output filename (default auto)")
    p_run.add_argument("--warmup", type=int, default=20, help="Warmup iterations for torch benchmarks")
    p_run.add_argument("--iters", type=int, default=50, help="Measured iterations for torch benchmarks")
    p_run.add_argument("--cpu-N", dest="cpu_N", type=int, default=2048, help="CPU matmul matrix size")
    p_run.add_argument("--gpu-N", dest="gpu_N", type=int, default=4096, help="GPU matmul matrix size")
    p_run.add_argument("--gpu-dtype", default="float16", choices=["float16", "float32", "bfloat16"], help="GPU dtype")

    p_run.add_argument("--with-sklearn", action="store_true", help="Also run sklearn RandomForest training benchmark")
    p_run.add_argument("--rf-samples", type=int, default=5000)
    p_run.add_argument("--rf-features", type=int, default=50)
    p_run.add_argument("--rf-estimators", type=int, default=200)

    p_run.set_defaults(func=cmd_run)

    args = p.parse_args()
    args.func(args)
