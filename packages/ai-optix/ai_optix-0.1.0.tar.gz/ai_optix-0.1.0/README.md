# AI Optix

**Intelligent profiling and optimization engine for AI workloads.**

AI Optix is a research-grade infrastructure tool designed to bridge the gap between high-level Python AI frameworks and low-level hardware performance. It prioritizes **correctness**, **reproducibility**, and **transparency** over "black box" auto-tuning.

---

## 🚀 Key Features

- **Hybrid Architecture**: Python orchestration with Rust system agents and C++ high-performance math kernels.
- **Hardware-Aware Benchmarking**: Automatic detection of CPU/GPU/Accelerator capabilities (via MEBS).
- **Correctness First**: Rigorous validation of optimization results against PyTorch/NumPy baselines.
- **System-Wide Profiling**: Correlates model metrics with OS-level counters (context switches, cache misses).
- **Safe Fallbacks**: Guaranteed execution on CPU if specialized hardware is unavailable.

## 🏗 Architecture Overview

| Component | Language | Responsibility |
|-----------|----------|----------------|
| **Core API** | Python | User interface, experiment orchestration, visualization. |
| **System Agent** | Rust | Safe threading, OS metric collection, background daemons. |
| **Kernels** | C++ | SIMD-optimized math operations, hardware-specific acceleration. |
| **Device Abstraction** | C | Low-level hardware query interface. |

## 💻 Supported Platforms

- **Linux** (Primary, extensive support)
- **macOS** (Apple Silicon support via MPS)
- **Windows** (Experimental via WSL2)

## 📚 Documentation

- [**Architecture Overview**](ARCHITECTURE.md): High-level system design.
- [**CPU Execution**](CPU_EXECUTION.md): Deep dive into memory & threading.
- [**GPU Comparison**](GPU_COMPARISON.md): When to use ai_optix vs. PyTorch for GPU.
- [**Performance Notes**](PERFORMANCE_NOTES.md): Bottlenecks and optimization guide.

## ⚡ Quick Start

### Installation (Pip)

We provide an automated setup script that handles:
- Python 3.11 Virtual Environment creation
- CPU vs CUDA Runtime detection
- PyTorch version selection

```bash
# Clone the repository
git clone https://github.com/ai-foundation-software/ai-optix.git
cd ai-optix

# Run the setup script
./scripts/setup.sh

# Activate the environment
source .venv/bin/activate
```

### Running a Benchmark

```bash
# Run the Reference MatMul Benchmark
python -m ai_optix.benchmarks.mebs.matmul_benchmark
```

### Python API Example

```python
from ai_optix.benchmarks.mebs import BenchmarkRunner, BenchmarkConfig
import torch

def my_model_op():
    # Your model code here
    pass

config = BenchmarkConfig(name="MyModel", warmup_iters=10, measure_iters=50)
runner = BenchmarkRunner(config)
runner.run(my_model_op)
```

## 🛡 Safety Philosophy

AI Optix adheres to strict principles:
1. **Never optimize without measuring.**
2. **Never sacrifice precision for speed** (unless explicitly requested via quantization levels).
3. **Always report the baseline.**

## 🗺 Roadmap

- [x] Initial Hybrid Architecture (Python/Rust/C++)
- [x] Model Efficiency Benchmark Suite (MEBS)
- [ ] Automated Kernel Tuning
- [ ] Distributed Training Profiling
- [ ] Web-based Visualization Dashboard

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code style and development workflow.

## 📄 License

This project is licensed under the Apache-2.0 License - see the [LICENSE](LICENSE) file for details.
