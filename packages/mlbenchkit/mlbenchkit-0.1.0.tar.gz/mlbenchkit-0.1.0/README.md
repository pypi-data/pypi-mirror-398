# MachineLearningBenchMarkingToolkit

Cross-platform machine-learning benchmarking toolkit to compare **Windows** PCs and **MacBook (Pro/Air)** machines.
It reports **system specs** (CPU cores/frequency, RAM) and runs **lightweight ML-style benchmarks** on:

- **CPU** (always)
- **NVIDIA CUDA GPU** (Windows/Linux, if available)
- **Apple Silicon GPU via MPS** (macOS, if available)

Outputs are saved as JSON files so you can easily compare multiple machines.

## Features

- ✅ Machine specs: hostname, OS, CPU model, cores, CPU freq, RAM totals/available
- ✅ Accelerator info:
  - CUDA: GPU name, total VRAM, compute capability
  - MPS: Apple Silicon (unified memory note)
- ✅ Benchmarks:
  - PyTorch matmul on CPU
  - PyTorch matmul on CUDA/MPS (if available)
  - Optional: scikit-learn RandomForest training benchmark

## Installation

### Minimal
```bash
pip install mlbenchkit
```

### With PyTorch benchmarks
```bash
# With PyTorch benchmarks
pip install "mlbenchkit[torch]"
```

## With scikit-learn benchmark
pip install "mlbenchkit[sklearn]"

## Everything
pip install "mlbenchkit[torch,sklearn]"

```

## How to use it?

```bash
mlbench specs
```

### Run benchmark suite (saves a JSON file):

```bash
mlbench run
# Run with sklearn benchmark:
mlbench run --with-sklearn
## Customize workload:
mlbench run --cpu-N 2048 --gpu-N 4096 --iters 50 --warmup 20 --gpu-dtype float16

```


