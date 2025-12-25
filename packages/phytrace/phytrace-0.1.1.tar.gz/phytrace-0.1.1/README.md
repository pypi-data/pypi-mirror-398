# phytrace

[![Tests](https://img.shields.io/badge/tests-pending-yellow)](https://github.com/mdcanocreates/phytrace)
[![Coverage](https://img.shields.io/badge/coverage-pending-yellow)](https://codecov.io/gh/mdcanocreates/phytrace)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://pypi.org/project/phytrace/)
[![Python](https://img.shields.io/badge/python-3.9+-blue)](https://www.python.org/downloads/)

A Python library that adds provenance tracking, invariant checking, and evidence generation to scientific simulations. `phytrace` is a minimal wrapper around `scipy.integrate.solve_ivp` that makes your simulations audit-ready and reproducible by default, without requiring any refactoring of existing code.

## Overview

`phytrace` solves the reproducibility crisis in scientific computing by automatically capturing everything needed to reproduce and audit simulation results. It wraps your existing ODE solvers with zero refactoring required, adding automatic environment capture, runtime invariant checking, and structured evidence packs that make your simulations publication-ready.

## Why phytrace?

### The Reproducibility Crisis

Scientific computing faces a reproducibility crisis. Results that worked "yesterday" fail today. Code that ran on your machine fails on a colleague's. Six months later, you can't remember which parameters you used. `phytrace` solves these problems by automatically documenting every aspect of your simulation.

### "Works on My Machine" Problem

Different Python versions, package versions, or system configurations can lead to different results. `phytrace` captures all of this automatically:
- Python version and implementation
- Installed package versions
- System information (OS, architecture)
- Git commit hash (if in a repository)

### Audit Requirements

Many fields require detailed documentation of simulations:
- **Research publications**: Need to prove results are reproducible
- **Regulatory submissions**: Must document all simulation parameters
- **Quality assurance**: Need evidence that simulations were run correctly
- **Collaboration**: Teams need to understand exactly what was run

`phytrace` generates evidence packs that satisfy these requirements automatically.

## Quick Start

Here's a complete example using a damped harmonic oscillator:

```python
from phytrace import trace_run
from phytrace.invariants import bounded, finite
import numpy as np

def damped_oscillator(t, y, k, c, m):
    x, v = y
    return [v, -(k/m)*x - (c/m)*v]

# Run traced simulation
result = trace_run(
    simulate=damped_oscillator,
    params={'k': 1.0, 'c': 0.1, 'm': 1.0},
    t_span=(0, 10),
    y0=[1.0, 0.0],
    invariants=[finite(), bounded(-10, 10)],
    evidence_dir='./evidence/run_001'
)

print(f"Success: {result.success}")
print(f"Function evaluations: {result.nfev}")
```

That's it! The evidence pack is automatically generated in `./evidence/run_001/` with:
- Complete environment and parameter documentation
- Invariant check results
- Trajectory data
- Publication-ready plots
- Human-readable report

See `examples/damped_oscillator.py` for a complete working example.

## Features

### Environment Capture

Automatically captures everything needed to reproduce your simulation:
- Python version and implementation
- Installed package versions (numpy, scipy, etc.)
- System information (OS, architecture, hostname)
- Git repository state (commit, branch, dirty flag)
- Timestamp of execution

All stored in `manifest.json` for easy inspection.

### Invariant Checking

Verify physical and mathematical constraints during simulation:

```python
from phytrace.invariants import bounded, monotonic, finite, create_invariant

# Built-in invariants
invariants = [
    finite(),                    # No NaN or inf
    bounded(-10, 10),           # Values stay in range
    monotonic(increasing=True, index=0)  # First state is increasing
]

# Custom invariant
@create_invariant(name="energy_conserved", severity="critical")
def check_energy(t, y, params, **kwargs):
    energy = compute_energy(y, params)
    return energy < params['E_max']

result = trace_run(..., invariants=invariants)
```

Severity levels:
- **warning**: Logs violations but continues
- **error**: Logs violations, sets `checks_passed=False`, but continues
- **critical**: Stops simulation immediately with RuntimeError

### Evidence Packs

Structured evidence packs contain everything needed to audit and reproduce:

```
evidence/run_001/
├── manifest.json          # Complete metadata
├── run_log.txt           # Execution log
├── invariants.json       # Check results
├── data/
│   ├── trajectory.csv    # Full state history
│   └── trajectory.h5     # HDF5 format (if available)
├── plots/
│   ├── time_series.png   # State evolution
│   ├── phase_space.png   # Phase portrait
│   └── solver_stats.png  # Solver diagnostics
├── checks/
│   └── solver_stats.json # Detailed statistics
└── report.md             # Human-readable summary
```

### Deterministic Execution

Automatic seed management ensures reproducibility:

```python
# Same seed = identical results
result1 = trace_run(..., seed=42)
result2 = trace_run(..., seed=42)
# result1.y == result2.y (identical)
```

Seeds are set for:
- numpy.random
- Python's random module
- PyTorch (if available)
- JAX (if available)

## Installation

```bash
pip install phytrace
```

For optional dependencies (pandas, h5py, gitpython):

```bash
pip install phytrace[full]
```

### Requirements

- Python 3.9+
- numpy >= 1.24
- scipy >= 1.11
- matplotlib >= 3.7

Optional:
- pandas (for CSV export)
- h5py (for HDF5 export)
- gitpython (for git repository tracking)

## API Reference

### Main Function

#### `trace_run(simulate, params, t_span, y0, ...)`

Main function for running traced simulations.

**Parameters:**
- `simulate` (Callable): ODE right-hand side function `f(t, y, **params) -> dy/dt`
- `params` (dict): Simulation parameters
- `t_span` (tuple): Time span `(t0, tf)`
- `y0` (array): Initial state vector
- `invariants` (list, optional): List of `InvariantCheck` objects
- `method` (str, default='RK45'): ODE solver method
- `evidence_dir` (str, optional): Directory for evidence pack
- `seed` (int, default=42): Random seed for reproducibility
- `dense_output` (bool, default=False): Compute dense output
- `events` (Callable, optional): Event function
- `**solver_kwargs`: Additional arguments for `solve_ivp`

**Returns:**
- `TraceResult`: Extended `OdeResult` with provenance metadata

### Invariants

#### Built-in Invariants

- `finite()`: Check for NaN or inf values
- `bounded(min_val, max_val, indices=None)`: Check values stay in range
- `monotonic(increasing=True, index=0)`: Check monotonicity

#### Custom Invariants

```python
from phytrace.invariants import create_invariant

@create_invariant(name="my_check", severity="warning")
def my_invariant(t, y, params, **kwargs):
    # kwargs may contain 'previous_state' and 'previous_time'
    return some_condition(y, params)
```

## Examples

### Basic Example: Damped Oscillator

See `examples/damped_oscillator.py` for a complete example with:
- Multiple invariants (finite, bounded, energy)
- Analytical solution comparison
- Evidence pack generation
- Detailed comments

### Advanced Example: Double Pendulum

See `examples/double_pendulum.py` for a chaotic system example:
- 4D state space
- Energy conservation tracking
- Sensitivity to initial conditions
- Comparison of nearby trajectories

Run examples:

```bash
python examples/damped_oscillator.py
python examples/double_pendulum.py
```

## FAQ

### When should I use this?

Use `phytrace` when you need:
- **Reproducible results**: Same inputs should give same outputs
- **Documentation**: Automatic capture of all simulation details
- **Audit trails**: Evidence packs for regulatory or publication requirements
- **Debugging**: Invariant violations help catch errors early
- **Collaboration**: Share complete simulation context with team

### What's the performance overhead?

Minimal. `phytrace` adds:
- **< 5% overhead** for typical simulations
- Invariant checking only at solver steps (not every function evaluation)
- Evidence generation happens after simulation completes
- Can disable evidence generation entirely by setting `evidence_dir=None`

### Does this provide certification or formal verification?

**No.** `phytrace` provides:
- ✅ Provenance tracking
- ✅ Runtime invariant checking
- ✅ Evidence generation
- ✅ Reproducibility

It does **not** provide:
- ❌ Formal verification
- ❌ Real-time guarantees
- ❌ Certification claims
- ❌ Proof of correctness

Think of it as "documentation and testing" for simulations, not "verification."

### Can I use this with my existing code?

**Yes!** That's the whole point. `trace_run` is a drop-in replacement for `scipy.integrate.solve_ivp`:

```python
# Before
result = solve_ivp(fun, t_span, y0, ...)

# After
result = trace_run(simulate=fun, params={...}, t_span=t_span, y0=y0, ...)
```

No refactoring required.

### How do I reproduce results from an evidence pack?

1. Check `manifest.json` for:
   - Python version
   - Package versions
   - Git commit (if applicable)
2. Install matching versions
3. Use the same parameters and initial state from `manifest.json`
4. Use the same seed (captured in manifest)
5. Run the simulation

The evidence pack contains everything needed.

## Roadmap (v0.2)

Planned features:
- **Golden test framework**: Regression testing for simulations
- **Multi-solver comparison**: Compare results across different solvers
- **Assumption ledger**: Track modeling assumptions
- **Jupyter integration**: Magic commands and inline visualization
- **CLI tools**: Validate and compare evidence packs
- **Performance profiling**: Detailed overhead analysis

## Contributing

Contributions are welcome! Areas where help is needed:
- Additional built-in invariants
- More plot types
- Documentation improvements
- Performance optimizations
- Test coverage

Please see the contributing guidelines (to be added).

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

If you use `phytrace` in your research, please cite:

```bibtex
@software{phytrace,
  title = {phytrace: Provenance tracking for scientific simulations},
  author = {mdcanocreates},
  version = {0.1.0},
  year = {2025},
  url = {https://github.com/mdcanocreates/phytrace}
}
```

## Scope / Non-goals

**v0.1.0 Scope:**
- Traced ODE runner wrapping `scipy.integrate.solve_ivp`
- Provenance capture (environment, parameters, git state)
- Runtime invariant checking
- Evidence pack generation with stable schema
- Examples and tests

**Not in v0.1.0:**
- CLI tools (planned for v0.2)
- Configuration system (planned for v0.2)
- Jupyter integration (planned for v0.2)
- Multi-solver comparison (planned for v0.2)
- Assumption ledger (planned for v0.2)

**Non-goals (not planned):**
- Formal verification
- Real-time guarantees
- Certification or regulatory compliance
- Proof of correctness

## Status

This project is in **early development** (v0.1.0). Core functionality is implemented and tested, but the API may evolve. Feedback and contributions welcome!

---

**Made for researchers who need to show their work.** 🔬
