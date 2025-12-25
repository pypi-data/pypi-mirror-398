"""
Core tracing functionality for phytrace.

This module provides the main trace_run function that wraps scipy.integrate.solve_ivp
with provenance tracking, invariant checking, and evidence generation.
"""

import inspect
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp

from .environment import capture_environment
from .invariants import InvariantChecker, InvariantCheck
from .seeds import set_global_seeds
from .types import ParamsDict, StateVector, TraceResult


def trace_run(
    simulate: Callable,
    params: Dict[str, Any],
    t_span: Tuple[float, float],
    y0: np.ndarray,
    invariants: Optional[List[InvariantCheck]] = None,
    method: str = 'RK45',
    evidence_dir: Optional[str] = None,
    seed: int = 42,
    dense_output: bool = False,
    events: Optional[Callable] = None,
    progress_callback: Optional[Callable[[float, StateVector], None]] = None,
    **solver_kwargs
) -> TraceResult:
    """Run a traced simulation with provenance tracking and invariant checking.
    
    This is the main entry point for phytrace. It wraps scipy.integrate.solve_ivp
    with additional functionality:
    - Automatic seed management for reproducibility
    - Environment capture (Python version, packages, git state)
    - Runtime invariant checking
    - Evidence pack generation
    
    Args:
        simulate: ODE right-hand side function: f(t, y, **params) -> dy/dt
        params: Dictionary of simulation parameters
        t_span: Time span (t0, tf) for integration
        y0: Initial state vector
        invariants: Optional list of InvariantCheck objects to verify
        method: ODE solver method (default: 'RK45')
        evidence_dir: Optional directory path for evidence pack
        seed: Random seed for reproducibility (default: 42)
        dense_output: Whether to compute dense output solution
        events: Optional event function for solve_ivp
        progress_callback: Optional callback(t, y) called during integration
        **solver_kwargs: Additional arguments passed to solve_ivp
    
    Returns:
        TraceResult object extending OdeResult with provenance metadata
    
    Raises:
        RuntimeError: If critical invariant violation occurs
    
    Example:
        >>> def damped_oscillator(t, y, k, c, m):
        ...     x, v = y
        ...     return [v, -(k/m)*x - (c/m)*v]
        >>> 
        >>> from phytrace.invariants import finite, bounded
        >>> 
        >>> result = trace_run(
        ...     simulate=damped_oscillator,
        ...     params={'k': 1.0, 'c': 0.1, 'm': 1.0},
        ...     t_span=(0, 10),
        ...     y0=[1.0, 0.0],
        ...     invariants=[finite(), bounded(-10, 10)],
        ...     evidence_dir='./evidence/run_001'
        ... )
    """
    # Step 1: Set seeds for reproducibility
    seeds_set = set_global_seeds(seed)
    
    # Step 2: Capture environment
    environment = capture_environment()
    
    # Step 3: Create evidence directory if requested
    evidence_path = None
    if evidence_dir:
        evidence_path = Path(evidence_dir)
        evidence_path.mkdir(parents=True, exist_ok=True)
    
    # Step 4: Set up invariant checker
    invariant_checker = None
    if invariants:
        invariant_checker = InvariantChecker(invariants)
    
    # Step 5: Wrap simulate function to check invariants
    violation_log: List[Dict[str, Any]] = []
    invariants_list = invariants or []  # Store for use in closure
    
    def wrapped_simulate(t: float, y: StateVector) -> StateVector:
        """Wrapper that checks invariants before calling simulate."""
        # Check invariants
        if invariant_checker:
            violations = invariant_checker.check(t, y, params)
            
            for inv_name in violations:
                # Find the invariant to get its severity
                inv = next((inv for inv in invariants_list if inv.name == inv_name), None)
                if inv:
                    violation_info = {
                        'time': t,
                        'state': np.asarray(y).tolist(),
                        'invariant': inv_name,
                        'severity': inv.severity
                    }
                    violation_log.append(violation_info)
                    
                    # Handle based on severity
                    if inv.severity == 'critical':
                        raise RuntimeError(
                            f"Critical invariant '{inv_name}' violated at t={t:.6f}. "
                            f"State: {y}. Simulation stopped."
                        )
                    elif inv.severity == 'error':
                        # Log but continue
                        pass
                    # 'warning' severity just logs
        
        # Call progress callback if provided
        if progress_callback:
            try:
                progress_callback(t, y)
            except Exception:
                pass  # Don't let callback errors stop simulation
        
        # Call original simulate function
        # Handle different function signatures
        sig = inspect.signature(simulate)
        if 'params' in sig.parameters or len(sig.parameters) > 2:
            # Function expects params as separate arguments
            return simulate(t, y, **params)
        else:
            # Function might expect params differently
            return simulate(t, y)
    
    # Step 6: Call scipy.integrate.solve_ivp
    try:
        ode_result = solve_ivp(
            fun=wrapped_simulate,
            t_span=t_span,
            y0=y0,
            method=method,
            dense_output=dense_output,
            events=events,
            **solver_kwargs
        )
    except RuntimeError as e:
        # Re-raise critical invariant violations
        if "Critical invariant" in str(e):
            raise
        # Otherwise, let it propagate
        raise
    
    # Step 7: Collect invariant summary
    invariant_summary = {}
    checks_passed = True
    if invariant_checker:
        invariant_summary = invariant_checker.get_summary()
        # Check if any critical or error invariants failed
        for inv in invariants_list:
            if inv.severity in ('critical', 'error') and inv.violations > 0:
                checks_passed = False
    
    # Step 8: Generate manifest
    manifest = _create_manifest(
        simulate=simulate,
        params=params,
        t_span=t_span,
        y0=y0,
        method=method,
        solver_kwargs=solver_kwargs,
        environment=environment,
        seeds=seeds_set,
        invariants=invariants or [],
        ode_result=ode_result,
        violation_log=violation_log
    )
    
    # Step 9: Create TraceResult
    trace_result = TraceResult(
        ode_result=ode_result,
        evidence_dir=evidence_path,
        manifest=manifest,
        invariant_log=invariant_summary,
        checks_passed=checks_passed
    )
    
    # Step 10: Generate evidence pack if directory was provided
    if evidence_path:
        try:
            from .evidence import create_evidence_pack
            create_evidence_pack(
                result=trace_result,
                evidence_dir=evidence_path,
                include_plots=True,
                include_data=True
            )
        except Exception as e:
            # Log error but don't fail the simulation
            print(f"Warning: Could not create evidence pack: {e}")
    
    return trace_result


def _create_manifest(
    simulate: Callable,
    params: Dict[str, Any],
    t_span: Tuple[float, float],
    y0: np.ndarray,
    method: str,
    solver_kwargs: Dict[str, Any],
    environment: Dict[str, Any],
    seeds: Dict[str, bool],
    invariants: List[InvariantCheck],
    ode_result: Any,
    violation_log: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create manifest dictionary with run metadata.
    
    Args:
        simulate: Simulation function
        params: Simulation parameters
        t_span: Time span
        y0: Initial state
        method: Solver method
        solver_kwargs: Additional solver arguments
        environment: Environment info
        seeds: Seed information
        invariants: List of invariants
        ode_result: ODE solver result
        violation_log: Log of invariant violations
    
    Returns:
        Manifest dictionary
    """
    # Get function information
    func_name = simulate.__name__
    func_module = getattr(simulate, '__module__', 'unknown')
    try:
        func_file = inspect.getfile(simulate)
    except (TypeError, OSError):
        func_file = 'unknown'
    
    # Convert params to serializable format
    serializable_params = {}
    for key, value in params.items():
        if isinstance(value, (int, float, str, bool)):
            serializable_params[key] = value
        elif isinstance(value, np.ndarray):
            serializable_params[key] = value.tolist()
        else:
            serializable_params[key] = str(value)
    
    manifest = {
        'run_id': str(uuid.uuid4()),
        'timestamp': environment.get('timestamp', ''),
        'environment': environment,
        'seeds': seeds,
        'simulation': {
            'function': f'{func_module}.{func_name}',
            'source_file': func_file,
            'params': serializable_params,
            'initial_state': np.asarray(y0).tolist(),
            't_span': list(t_span),
            'solver': {
                'method': method,
                **{k: v for k, v in solver_kwargs.items() 
                   if isinstance(v, (int, float, str, bool))}
            }
        },
        'invariants': [
            {
                'name': inv.name,
                'severity': inv.severity,
                'checks': inv.total_checks,
                'violations': inv.violations
            }
            for inv in invariants
        ],
        'solver_stats': {
            'nfev': int(ode_result.nfev),
            'njev': int(ode_result.njev) if ode_result.njev else 0,
            'nlu': int(ode_result.nlu) if ode_result.nlu else 0,
            'success': bool(ode_result.success),
            'message': str(ode_result.message)
        },
        'violations': violation_log
    }
    
    return manifest

