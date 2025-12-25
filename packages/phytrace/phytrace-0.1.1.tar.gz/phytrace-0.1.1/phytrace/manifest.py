"""
Manifest generation module for phytrace.

Generates structured manifest.json files containing all metadata needed to
reproduce and understand simulation runs.
"""

import inspect
import uuid
from typing import Any, Callable, Dict, List

import numpy as np

# Import OdeResult with fallback
try:
    from scipy.integrate import OdeResult
except ImportError:
    from scipy.integrate._ivp.ivp import OdeResult

from .types import InvariantCheck, TraceResult


def create_manifest(
    result: TraceResult,
    params: Dict[str, Any],
    simulate_func: Callable,
    solver_config: Dict[str, Any],
    environment: Dict[str, Any],
    seeds: Dict[str, Any],
    invariants: List[InvariantCheck]
) -> Dict[str, Any]:
    """Create manifest dictionary with complete run metadata.
    
    Generates a comprehensive manifest containing:
    - Run identification (run_id, timestamp)
    - Environment information (Python, platform, packages, git)
    - Seed information
    - Simulation configuration (function, parameters, initial state, solver)
    - Invariant definitions and results
    - Solver statistics
    
    Args:
        result: TraceResult from the simulation
        params: Simulation parameters dictionary
        simulate_func: The simulation function that was called
        solver_config: Solver configuration (method, rtol, atol, etc.)
        environment: Environment information from capture_environment()
        seeds: Seed information from set_global_seeds()
        invariants: List of InvariantCheck objects used
    
    Returns:
        Dictionary containing all manifest information
    
    Example:
        >>> manifest = create_manifest(
        ...     result=result,
        ...     params={'k': 1.0, 'c': 0.1},
        ...     simulate_func=damped_oscillator,
        ...     solver_config={'method': 'RK45', 'rtol': 1e-6},
        ...     environment=env,
        ...     seeds=seeds,
        ...     invariants=[finite(), bounded(-10, 10)]
        ... )
    """
    # Get function information
    func_name = simulate_func.__name__
    func_module = getattr(simulate_func, '__module__', 'unknown')
    try:
        func_file = inspect.getfile(simulate_func)
    except (TypeError, OSError):
        func_file = 'unknown'
    
    # Convert params to serializable format
    serializable_params = _make_serializable(params)
    
    # Get initial state
    if hasattr(result, 'y') and result.y is not None:
        if len(result.y.shape) > 1:
            initial_state = result.y[:, 0].tolist()
        else:
            initial_state = [float(result.y[0])] if len(result.y) > 0 else []
    else:
        initial_state = []
    
    # Get time span
    if hasattr(result, 't') and result.t is not None and len(result.t) > 0:
        t_span = [float(result.t[0]), float(result.t[-1])]
    else:
        t_span = [0.0, 0.0]
    
    # Build manifest
    manifest: Dict[str, Any] = {
        'run_id': str(uuid.uuid4()),
        'timestamp': environment.get('timestamp', ''),
        'environment': environment,
        'seeds': seeds,
        'simulation': {
            'function': f'{func_module}.{func_name}',
            'source_file': func_file,
            'params': serializable_params,
            'initial_state': initial_state,
            't_span': t_span,
            'solver': {
                'method': solver_config.get('method', 'unknown'),
                **{k: v for k, v in solver_config.items() 
                   if isinstance(v, (int, float, str, bool)) and k != 'method'}
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
            'nfev': int(result.nfev),
            'njev': int(result.njev) if result.njev else 0,
            'nlu': int(result.nlu) if result.nlu else 0,
            'success': bool(result.success),
            'message': str(result.message),
            'status': int(result.status)
        }
    }
    
    # Add violation log if available
    if hasattr(result, 'manifest') and isinstance(result.manifest, dict):
        violations = result.manifest.get('violations', [])
        if violations:
            manifest['violations'] = violations
    
    return manifest


def _make_serializable(obj: Any) -> Any:
    """Convert object to JSON-serializable format.
    
    Handles numpy arrays, complex types, and other non-serializable objects
    by converting them to lists or strings.
    
    Args:
        obj: Object to make serializable
    
    Returns:
        Serializable version of the object
    """
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    else:
        # Fallback: convert to string
        return str(obj)

