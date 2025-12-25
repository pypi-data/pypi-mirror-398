"""
Invariant checking system for runtime verification of simulation constraints.

This module provides tools for checking physical and mathematical invariants
during simulation execution, such as energy conservation, bounds checking,
and monotonicity.
"""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from .types import InvariantCheck, InvariantFunc, ParamsDict, StateVector


class InvariantChecker:
    """Manages and executes invariant checks during simulation.
    
    Tracks multiple invariants and their violation history, providing
    statistics and summaries of check results.
    
    Example:
        >>> checker = InvariantChecker([
        ...     InvariantCheck("energy", check_energy, "critical"),
        ...     InvariantCheck("bounds", check_bounds, "warning")
        ... ])
        >>> violations = checker.check(0.0, [1.0, 0.0], {'k': 1.0})
        >>> summary = checker.get_summary()
    """
    
    def __init__(self, invariants: List[InvariantCheck]):
        """Initialize the invariant checker.
        
        Args:
            invariants: List of InvariantCheck objects to monitor
        """
        self.invariants = invariants
        self._previous_state: Optional[StateVector] = None
        self._previous_time: Optional[float] = None
    
    def check(self, t: float, y: StateVector, params: ParamsDict) -> List[str]:
        """Check all invariants at the current simulation state.
        
        Args:
            t: Current time
            y: Current state vector
            params: Simulation parameters
        
        Returns:
            List of names of invariants that were violated
        """
        violations: List[str] = []
        y_array = np.asarray(y)
        
        for inv in self.invariants:
            inv.total_checks += 1
            
            try:
                # Prepare kwargs for invariant function
                kwargs: Dict[str, Any] = {}
                if self._previous_state is not None:
                    kwargs['previous_state'] = self._previous_state
                if self._previous_time is not None:
                    kwargs['previous_time'] = self._previous_time
                
                # Call invariant function
                result = inv.func(t, y_array, params, **kwargs)
                
                if not result:
                    inv.violations += 1
                    violations.append(inv.name)
            except Exception as e:
                # If invariant check raises exception, treat as violation
                inv.violations += 1
                violations.append(inv.name)
                # Could log the exception here
        
        # Update previous state for next check
        self._previous_state = y_array.copy()
        self._previous_time = t
        
        return violations
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all invariants.
        
        Returns:
            Dictionary with summary information including:
            - total_checks: Total number of checks performed
            - total_violations: Total number of violations
            - invariants: Per-invariant statistics
        """
        summary: Dict[str, Any] = {
            'total_checks': sum(inv.total_checks for inv in self.invariants),
            'total_violations': sum(inv.violations for inv in self.invariants),
            'invariants': []
        }
        
        for inv in self.invariants:
            summary['invariants'].append({
                'name': inv.name,
                'severity': inv.severity,
                'checks': inv.total_checks,
                'violations': inv.violations,
                'violation_rate': (
                    inv.violations / inv.total_checks 
                    if inv.total_checks > 0 else 0.0
                )
            })
        
        return summary
    
    def reset(self):
        """Reset all check counters and previous state."""
        for inv in self.invariants:
            inv.total_checks = 0
            inv.violations = 0
        self._previous_state = None
        self._previous_time = None


def create_invariant(name: str, severity: str = 'warning'):
    """Decorator to create an InvariantCheck from a function.
    
    Args:
        name: Name of the invariant
        severity: Severity level ('warning', 'error', 'critical')
    
    Returns:
        Decorator function that converts a function to an InvariantCheck
    
    Example:
        >>> @create_invariant(name="energy_conserved", severity="critical")
        ... def check_energy(t, y, params):
        ...     energy = compute_energy(y, params)
        ...     return energy < params['E_max']
        >>> 
        >>> # check_energy is now an InvariantCheck object
        >>> # Use in trace_run:
        >>> result = trace_run(..., invariants=[check_energy])
    """
    def decorator(func: InvariantFunc) -> InvariantCheck:
        """Convert function to InvariantCheck."""
        # Wrap the function to preserve it
        wrapped_func = func
        return InvariantCheck(
            name=name,
            func=wrapped_func,
            severity=severity
        )
    return decorator


# Built-in invariant factories

def bounded(min_val: float, max_val: float, 
            indices: Optional[List[int]] = None) -> InvariantCheck:
    """Create an invariant that checks state values are within bounds.
    
    Args:
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        indices: Optional list of state indices to check. If None, checks all.
    
    Returns:
        InvariantCheck object
    
    Example:
        >>> # Check all states are between -10 and 10
        >>> bound_check = bounded(-10.0, 10.0)
        >>> 
        >>> # Check only first two states
        >>> bound_check = bounded(0.0, 1.0, indices=[0, 1])
    """
    def check_func(t: float, y: StateVector, params: ParamsDict, **kwargs) -> bool:
        y_array = np.asarray(y)
        if indices is not None:
            values = y_array[indices]
        else:
            values = y_array.flatten()
        return np.all((values >= min_val) & (values <= max_val))
    
    return InvariantCheck(
        name=f"bounded_{min_val}_{max_val}",
        func=check_func,
        severity='error'
    )


def monotonic(increasing: bool = True, index: int = 0) -> InvariantCheck:
    """Create an invariant that checks a state variable is monotonic.
    
    Args:
        increasing: If True, check for monotonic increase; if False, decrease
        index: Index of state variable to check
    
    Returns:
        InvariantCheck object
    
    Example:
        >>> # Check first state variable is monotonically increasing
        >>> mono_check = monotonic(increasing=True, index=0)
    """
    def check_func(t: float, y: StateVector, params: ParamsDict, **kwargs) -> bool:
        y_array = np.asarray(y)
        current_val = y_array[index]
        
        previous_state = kwargs.get('previous_state')
        if previous_state is None:
            return True  # First check, no previous value
        
        previous_val = previous_state[index]
        
        if increasing:
            return current_val >= previous_val
        else:
            return current_val <= previous_val
    
    direction = "increasing" if increasing else "decreasing"
    return InvariantCheck(
        name=f"monotonic_{direction}_index_{index}",
        func=check_func,
        severity='warning'
    )


def finite() -> InvariantCheck:
    """Create an invariant that checks all state values are finite (no NaN or inf).
    
    Returns:
        InvariantCheck object
    
    Example:
        >>> # Check no NaN or inf values
        >>> finite_check = finite()
    """
    def check_func(t: float, y: StateVector, params: ParamsDict, **kwargs) -> bool:
        y_array = np.asarray(y)
        return np.all(np.isfinite(y_array))
    
    return InvariantCheck(
        name="finite",
        func=check_func,
        severity='critical'
    )

