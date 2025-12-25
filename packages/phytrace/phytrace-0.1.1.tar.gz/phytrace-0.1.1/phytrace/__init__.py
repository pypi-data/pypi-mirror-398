"""
phytrace: Provenance tracking, invariant checking, and evidence generation
for scientific simulations.

A minimal wrapper around scipy.integrate.solve_ivp that adds:
- Automatic environment capture
- Runtime invariant checking
- Structured evidence packs for reproducibility
- Deterministic execution by default
"""

__version__ = "0.1.1"

# Core functionality
from .core import trace_run
from .invariants import (
    InvariantCheck,
    InvariantChecker,
    create_invariant,
    bounded,
    monotonic,
    finite,
)
from .types import TraceResult, ParamsDict, StateVector

# Golden test framework (v0.1.0 - basic functionality)
from .golden import GoldenTest, golden_test, store_golden, compare_results

__all__ = [
    "trace_run",
    "InvariantCheck",
    "InvariantChecker",
    "create_invariant",
    "bounded",
    "monotonic",
    "finite",
    "TraceResult",
    "ParamsDict",
    "StateVector",
    "GoldenTest",
    "golden_test",
    "store_golden",
    "compare_results",
]

# Note: Advanced features (comparison, assumptions) are implemented but
# not included in v0.1.0 exports. They will be available in v0.2.0.

