# EZGA — Evolutionary Structure Exploration Framework

## Overview

EZGA is a modular, scalable, and chemically aware evolutionary framework for exploring and optimizing atomistic structures. It follows the **GitLab Enterprise Documentation Style**, emphasizing clarity, task‑orientation, operational guidance, and maintainability. This page serves as the primary landing document for new users and contributors.

EZGA enables configuration‑first evolutionary searches across molecular, cluster, crystalline, and surface systems. The engine integrates interchangeable components—initialization, features, objectives, selection, variation, convergence, and simulation—built around reproducible workflows and deterministic archival.

---

## Key capabilities

* **Configuration‑driven GA engine** for molecules and periodic crystals.
* **Composable modules**: initialization, constraints, features, objectives, selection, variation, simulator, convergence.
* **Robust execution**: deterministic seeds, deduplication, integrity checks, scalable parallelism.
* **Physical‑model integration** with ASE/MACE or any Python‑callable evaluator.
* **Hierarchical Supercell Escalation (HiSE)** for periodic systems.
* **Task‑oriented workflows**: copy → modify → run.

---

## Why use EZGA

* Explore large compositional/structural spaces efficiently.
* Apply human‑readable constraints (e.g., `greater_than("Cu", 1)`).
* Start with datasets or DoE space‑filling seeds; escalate to larger supercells.
* Increase robustness using integrity checks that avoid unphysical trial structures.
* Scale seamlessly from a laptop to multi‑GPU clusters.

---

## Get started fast

### 1. Install (Python ≥ 3.10)

```bash
pip install ezga_lib
```

Optional GPU/ML potential dependencies (MACE/ASE, CUDA/ROCm) depend on your environment.
See **Simulator** in the Wiki.

### 2. Smoke test

```python
import ezga
print(getattr(ezga, "__version__", "unknown"))
```

### 3. Run your first job

Follow the minimal runnable script in **Quickstart**.

**Tip:** In GitLab Wiki, section anchors work like: `./Constraints#greater-than`.

---

## Documentation

Full documentation is available in the project's **GitLab Wiki**:

* **[Home](./-/wikis/home)**
* **[Installation](./-/wikis/Installation)**
* **[Quickstart](./-/wikis/Quickstart)**
* **[Recipes](./-/wikis/Recipes)**
* **[Configuration (GAConfig)](./-/wikis/Configuration)**

---

## Repository structure

```
src/ezga/
    core/                   # GA engine
    selection/              # Parent selectors
    variation/              # Mutation & crossover operators
    hise/                   # Supercell escalation
    thermostat/             # Exploration–exploitation control
    DoE/                    # Design-of-Experiments initializer
    bayesian_optimization/  # Surrogate-driven generative module
    convergence/            # Termination logic
    simulator/              # MD, relaxations, MLIPs
    evaluator/              # Feature & objective metrics
    visualization/
    sync/                   # Island-model mailbox
    io/                     # SQL–HDF5 state storage
    cli/                    # Command-line interface
    utils/

docs/                       # Sphinx documentation
tests/                      # Regression tests
dist/                       # Build artifacts
examples/                   # Example workflows
```

---

## Usage

### YAML workflow

```bash
ezga run config.yaml
```

### Python API

```python
from ezga import Agent, load_config
config = load_config("config.yaml")
agent = Agent(config)
agent.run()
```

---

## Benchmarks

EZGA is validated on:

* Molecular conformational exploration (alanine dipeptide).
* Lennard–Jones cluster global search.
* Binary‑oxide convex‑hull reconstruction.
* Autonomous CuO/Cu₂O grand‑canonical phase diagram.

---

## Issues & Support

Use the GitLab **Issues** board to report problems, request enhancements, or ask questions:

* **[Report a bug](./-/issues/new?issue_type=bug)**
* **[Request a feature](./-/issues/new?issue_type=feature)**
* **[Ask for clarification](./-/issues)**
* **[Suggest documentation improvements](./-/issues)**

Issue templates (if configured) are available here:
**[Issue templates](./-/issues/templates)**

---

## Authors

* Juan Manuel Lombardi
* Felix Riccius
* Charles W. P. Paré
* Karsten Reuter
* Christoph Scheurer

