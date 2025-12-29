# SLiM-CUDA

**SLiM-CUDA** is a GPU-accelerated backend for large-scale hologram generation and wavefront synthesis, designed for high-performance spatial light modulator (SLM) workflows.

This PyPI distribution provides a **public, compatibility-first build** intended for correctness, reproducibility, and integration. Optimized GPU-specific kernels are available separately for collaborators.

---

## Features

- CUDA-accelerated weighted Gerchberg–Saxton (WGS)–style solvers
- Designed for large multi-focus hologram synthesis
- CuPy-based runtime integration
- Drop-in upgrade path for optimized kernels (no API changes)

---

## Installation

```bash
pip install slimcuda
```

This installs:
- PTX kernels compiled for broad GPU compatibility
- Corresponding CUDA source files for transparency and inspection
- Python-side orchestration and utilities

## Kernel Architecture & Performance Model
### Public PyPI build (default)

The PyPI wheel ships with:
- slimcuda_og.ptx 
- Corresponding CUDA source (.cu, .cuh) files

This build prioritizes:
- Broad GPU compatibility
- Reproducibility
- Ease of installation

**⚠️ Performance note**

The PTX kernels are not **performance-optimized** for modern GPUs. They exist to ensure correctness and portability.

### Optimized builds (collaborators)

Highly optimized, GPU-specific kernels are distributed as **fatbin / cubin** binaries and are **not included** in the public wheel.

If an optimized kernel is present locally, SLiM-CUDA will automatically detect and load it.

Benefits:
- Substantially higher throughput
- Reduced launch overhead
- Architecture-specific tuning

If you are a collaborator or have a supported GPU and need optimized kernels, please contact the author.

## Runtime Banner

When running with the public PTX kernels, SLiM-CUDA displays a short informational banner indicating that an optimized build exists.

This is **informational only** and can be disabled:
```bash
# Linux / macOS
export SLIMCUDA_BANNER=0

# Windows (PowerShell)
setx SLIMCUDA_BANNER 0
```

or programmatically via the loader API.

## GPU Compatibility

- Public PTX kernels: should run on most CUDA-capable GPUs
- Optimized kernels: GPU- and build-specific

If you have an optimized kernel but encounter issues on your GPU, please contact the author for a tailored build.

## License

- **Python code**: MIT License
- **Public CUDA source (PTX / .cu)**: MIT License
- **Optimized CUDA binaries**: distributed separately under collaborator-specific terms

## Citation

If you use **SLiM-CUDA** in academic work, please cite the following:

### Primary citation (recommended)
SLiM-CUDA was originally developed to support the methodology described in:

> **Z. Qu et al.**,
> *Deep-learning-aided multi-focal hologram generation*, 
> **Optics & Laser Technology**, 2025.
> DOI: 10.1016/j.optlastec.2024.112056

```bibtex
@article{jwangSlimCuda,
  title   = {Deep-learning-aided multi-focal hologram generation},
  author  = {Qu, Z. and others},
  journal = {Optics & Laser Technology},
  year    = {2025},
  doi     = {10.1016/j.optlastec.2024.112056}
}
```

If your work builds upon or uses the algorithms and concepts enabled by SLiM-CUDA,  
**please cite this publication**.

### Software citation
If you prefer to cite the software directly (e.g. for tooling or infrastructure use), you may cite:

> SLiM-CUDA: GPU-accelerated hologram generation backend.  
> https://pypi.org/project/slimcuda/

A formal software citation entry (BibTeX) will be provided in a future release.


## Disclaimer

This software is intended for research and advanced technical use.

API stability is maintained, but internal kernel implementations may evolve.