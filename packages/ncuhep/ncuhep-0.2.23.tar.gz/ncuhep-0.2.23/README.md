# ncuhep

A collection of high-energy and astroparticle physics utilities focused on **muography** and **dimension-aware units**. The library bundles a full muon tracking pipeline, a lightweight units system, and small helpers such as an SSH-based job scheduler for remote clusters.

## Table of contents
- [Features](#features)
- [Installation](#installation)
- [Quickstart](#quickstart)
  - [Muography pipeline](#muography-pipeline)
  - [Units and dimensional arithmetic](#units-and-dimensional-arithmetic)
  - [Lightweight SSH job scheduling](#lightweight-ssh-job-scheduling)
- [Project structure](#project-structure)
- [Development](#development)
- [License](#license)

## Features
- **Muography (`ncuhep.muography`)**
  - Parse raw DAQ `_Mu.txt` files into timestamped hits with configurable counter unwrapping and glitch suppression.
  - Identify coincident events per detector layer and reconstruct straight-line tracks with χ² scoring.
  - Generate Monte Carlo response bases and geometric factors for flux reconstruction, plus helpers for flux post-processing and visualization.
- **Units (`ncuhep.units`)**
  - SI-centric unit classes with attribute-based getters/setters (e.g., `Length`, `Time`, `Flux`, `Density`).
  - Automatic dimensional arithmetic with registry-backed derived quantities, plus helpers for custom unit definitions.
- **Job scheduling (`ncuhep.job_scheduler`)**
  - A minimal SSH-based dispatcher that probes remote CPU load and assigns jobs across hosts, with optional submission time windows.

## Installation
Requires **Python 3.11+**.

From PyPI:
```bash
pip install ncuhep
```

From source (editable):
```bash
git clone <this-repo>
cd ncuhep
pip install -e .
```

GPU acceleration for Monte Carlo rendering uses Numba/CUDA when available but is optional.

## Quickstart
### Muography pipeline
Below is a minimal sketch of how the parser → identifier → tracker pipeline fits together. Configure your detector geometry, DAQ file format, and analysis cuts before running the chain.

```python
from ncuhep.muography import parser, identifier, tracker
from ncuhep.muography.classes import PlaneDetector, MuTxtFormat, AnalysisConfig

# Load detector geometry (JSON layout exported via PlaneDetector._export())
det = PlaneDetector()
det._import("detector_config.json")

# Describe your raw _Mu.txt format
fmt = MuTxtFormat()
fmt._import("mu_txt_format.json")

# Analysis cuts (time clustering, hit thresholds, etc.)
cfg = AnalysisConfig()
cfg._import("analysis_config.json")

# Parse one run, then build events and tracks
hits, live_time = parser("/data/runs", "run001_Mu.txt", fmt, det, cfg, return_hits=True)
events = identifier(hits, det)
tracks = tracker(events, det)

print(f"Reconstructed {len(tracks)} tracks with {live_time/3600:.2f} hours of live time")
```

### Units and dimensional arithmetic
The units module exposes base quantities (length, time, counts, angle, etc.) and common derived types. Values are stored internally in SI and converted via attribute access.

```python
from ncuhep.units import Length, Time, Flux

L = Length()
L.cm = 50   # store as 0.50 m internally

T = Time()
T.s = 120

Φ = Flux()
Φ.counts_m2_s_sr = 200

area = L * L          # -> Area
live_time = T.h       # numeric hours view
fluence = Φ * T       # dimensional arithmetic preserved
print(area.unit)      # "m^2"
```

Custom units can be registered at runtime using `make_custom_unit` or `make_custom_unit_from_signature` for niche dimensions.

### Lightweight SSH job scheduling
`ncuhep.job_scheduler.smart_scheduler.SSHJobScheduler` provides a small “poor man’s Slurm” for dispatching many similar jobs across SSH-accessible hosts.

```python
from ncuhep.job_scheduler.smart_scheduler import SSHJobScheduler
import numpy as np

scheduler = SSHJobScheduler(
    hosts=["chip03", "chip04"],
    remote_workdir="/data/workdir",
    executable="/path/to/python",      # or a compiled binary
    script_path="/data/workdir/run.py", # used when executable is Python
    cpu_threshold=50.0,
    max_jobs_per_host=2,
)

# Dispatch a grid of arguments; each column is one positional argument
results = scheduler.dispatch_many_from_columns(
    np.arange(0, 5),   # arg0
    np.linspace(0, 1, 5),  # arg1
)
print(results)
```

## Project structure
- `ncuhep/muography/` – core muography pipeline, Monte Carlo rendering, scatter modeling, profiling tools, and utilities (tracking, coordinates, flux processing).
- `ncuhep/units/` – unit definitions and dimensional arithmetic helpers.
- `ncuhep/job_scheduler/` – SSH job dispatcher with CPU probing and submission time windows.

## Development
- Install dependencies with `pip install -e .` in a Python 3.11+ environment.
- Formatting and linting are not enforced by tooling in-repo; please keep style consistent with existing NumPy/scipy-oriented code.
- Tests are not bundled; exercising the parser/identifier/tracker pipeline on a small `_Mu.txt` sample is recommended before larger runs.

## License
This project is distributed under the **NCUHEP Research Read-Only License**. You may download, run, and study the code for personal, educational, or academic research purposes, but redistribution and commercial use are prohibited. Citation is required for published work based on this software. See [`LICENSE`](./LICENSE) for full terms.