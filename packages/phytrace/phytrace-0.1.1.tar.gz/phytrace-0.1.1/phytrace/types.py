"""
Core type definitions for phytrace.

This module defines the fundamental types used throughout the library
for type checking and documentation purposes.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Union
from pathlib import Path

import numpy as np

# OdeResult is returned by solve_ivp but not directly importable in some scipy versions
# We'll import it from the internal module or use a workaround
try:
    from scipy.integrate import OdeResult
except ImportError:
    from scipy.integrate._ivp.ivp import OdeResult


# Type aliases for common patterns
ParamsDict = Dict[str, Union[float, int, np.ndarray]]
"""Dictionary of simulation parameters. Values can be scalars or arrays."""

StateVector = Union[List[float], np.ndarray]
"""State vector representing the system state at a given time."""

InvariantFunc = Callable[[float, StateVector, ParamsDict, ...], bool]
"""
Function signature for invariant checks.

Args:
    t: Current time
    y: Current state vector
    params: Simulation parameters
    **kwargs: Additional context (e.g., previous state)

Returns:
    True if invariant holds, False otherwise
"""

SimulateFunc = Callable[[float, StateVector, ...], StateVector]
"""
Function signature for ODE right-hand side.

Args:
    t: Current time
    y: Current state vector
    **kwargs: Additional arguments (typically params)

Returns:
    Derivative dy/dt
"""


@dataclass
class InvariantCheck:
    """Represents a single invariant check configuration.
    
    Attributes:
        name: Human-readable name for the invariant
        func: Function that performs the check
        severity: How to handle violations ('warning', 'error', 'critical')
        total_checks: Number of times this invariant has been checked
        violations: Number of times this invariant has been violated
    """
    name: str
    func: InvariantFunc
    severity: Literal['warning', 'error', 'critical'] = 'warning'
    total_checks: int = 0
    violations: int = 0


class TraceResult(OdeResult):
    """Extended ODE result with provenance and evidence metadata.
    
    Extends scipy.integrate.OdeResult with additional fields for
    tracking simulation provenance and generating evidence packs.
    
    Attributes:
        evidence_dir: Path to the evidence pack directory (if created)
        manifest: Dictionary containing run metadata and configuration
        invariant_log: Dictionary containing invariant check results
        checks_passed: Whether all critical and error-level checks passed
    """
    
    def __init__(self, ode_result: OdeResult, 
                 evidence_dir: Path = None,
                 manifest: Dict[str, Any] = None,
                 invariant_log: Dict[str, Any] = None,
                 checks_passed: bool = True):
        """Initialize TraceResult from an OdeResult.
        
        Args:
            ode_result: The underlying OdeResult from scipy
            evidence_dir: Path to evidence pack directory
            manifest: Run metadata dictionary
            invariant_log: Invariant check results
            checks_passed: Whether all checks passed
        """
        # Copy all attributes from OdeResult
        super().__init__(
            t=ode_result.t,
            y=ode_result.y,
            sol=ode_result.sol,
            t_events=ode_result.t_events,
            y_events=ode_result.y_events,
            nfev=ode_result.nfev,
            njev=ode_result.njev,
            nlu=ode_result.nlu,
            status=ode_result.status,
            message=ode_result.message,
            success=ode_result.success
        )
        self.evidence_dir = evidence_dir
        self.manifest = manifest if manifest is not None else {}
        self.invariant_log = invariant_log if invariant_log is not None else {}
        self.checks_passed = checks_passed

