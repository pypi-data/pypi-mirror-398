"""
Multi-solver comparison module for phytrace.

[For v0.2] Allows running the same simulation with multiple solvers
and comparing results to help choose the best solver for a given problem.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

# Import OdeResult with fallback
try:
    from scipy.integrate import OdeResult
except ImportError:
    from scipy.integrate._ivp.ivp import OdeResult

from .core import trace_run
from .types import TraceResult, ParamsDict


def compare_solvers(
    simulate: Callable,
    params: ParamsDict,
    t_span: tuple[float, float],
    y0: np.ndarray,
    solvers: List[str] = ['RK45', 'DOP853', 'Radau', 'BDF'],
    tolerance: float = 1e-6,
    evidence_dir: Optional[str] = None,
    **solver_kwargs
) -> Dict[str, Any]:
    """Run the same simulation with multiple solvers and compare results.
    
    Args:
        simulate: ODE right-hand side function
        params: Simulation parameters
        t_span: Time span
        y0: Initial state
        solvers: List of solver methods to try
        tolerance: Tolerance for comparison
        evidence_dir: Optional directory for evidence packs
        **solver_kwargs: Additional solver arguments
    
    Returns:
        Dictionary with comparison results including:
        - results: Dict mapping solver name to TraceResult
        - comparison: Comparison statistics
        - recommendation: Recommended solver for this problem type
    
    Example:
        >>> comparison = compare_solvers(
        ...     simulate=my_system,
        ...     params={'k': 1.0},
        ...     t_span=(0, 10),
        ...     y0=[1.0, 0.0],
        ...     solvers=['RK45', 'DOP853', 'BDF']
        ... )
    """
    results: Dict[str, TraceResult] = {}
    
    # Run each solver
    for solver in solvers:
        solver_evidence_dir = None
        if evidence_dir:
            solver_evidence_dir = f"{evidence_dir}/solver_{solver}"
        
        try:
            result = trace_run(
                simulate=simulate,
                params=params,
                t_span=t_span,
                y0=y0,
                method=solver,
                evidence_dir=solver_evidence_dir,
                **solver_kwargs
            )
            results[solver] = result
        except Exception as e:
            # Solver failed - log but continue
            print(f"Warning: Solver {solver} failed: {e}")
    
    # Compare results
    comparison = _compare_solver_results(results, tolerance)
    
    # Generate recommendation
    recommendation = _recommend_solver(results, comparison)
    
    return {
        'results': results,
        'comparison': comparison,
        'recommendation': recommendation
    }


def _compare_solver_results(
    results: Dict[str, TraceResult],
    tolerance: float
) -> Dict[str, Any]:
    """Compare results from multiple solvers."""
    if len(results) < 2:
        return {}
    
    # Use first solver as reference
    ref_solver = list(results.keys())[0]
    ref_result = results[ref_solver]
    
    comparisons = {}
    
    for solver, result in results.items():
        if solver == ref_solver:
            continue
        
        # Interpolate to common time points
        from scipy.interpolate import interp1d
        
        t_ref = ref_result.t
        t_curr = result.t
        t_common = np.linspace(
            max(t_ref[0], t_curr[0]),
            min(t_ref[-1], t_curr[-1]),
            1000
        )
        
        # Compare trajectories
        if len(ref_result.y.shape) == 1:
            y_ref = interp1d(t_ref, ref_result.y)(t_common)
            y_curr = interp1d(t_curr, result.y)(t_common)
        else:
            y_ref = np.array([interp1d(t_ref, ref_result.y[i, :])(t_common) 
                             for i in range(ref_result.y.shape[0])])
            y_curr = np.array([interp1d(t_curr, result.y[i, :])(t_common) 
                              for i in range(result.y.shape[0])])
        
        diff = np.abs(y_ref - y_curr)
        max_diff = np.max(diff)
        rms_diff = np.sqrt(np.mean(diff**2))
        
        comparisons[solver] = {
            'max_diff': float(max_diff),
            'rms_diff': float(rms_diff),
            'nfev': result.nfev,
            'success': result.success,
            'time_ratio': result.nfev / ref_result.nfev if ref_result.nfev > 0 else 1.0
        }
    
    return {
        'reference': ref_solver,
        'comparisons': comparisons
    }


def _recommend_solver(
    results: Dict[str, TraceResult],
    comparison: Dict[str, Any]
) -> Dict[str, Any]:
    """Recommend best solver based on results."""
    if not results:
        return {'solver': None, 'reason': 'No successful results'}
    
    # Find fastest solver
    fastest = min(results.items(), key=lambda x: x[1].nfev)
    
    # Find most accurate (if comparison available)
    if comparison and 'comparisons' in comparison:
        most_accurate = min(
            comparison['comparisons'].items(),
            key=lambda x: x[1]['rms_diff']
        )
        recommended = most_accurate[0]
        reason = f"Lowest RMS error: {most_accurate[1]['rms_diff']:.2e}"
    else:
        recommended = fastest[0]
        reason = f"Fastest: {fastest[1].nfev} function evaluations"
    
    return {
        'solver': recommended,
        'reason': reason,
        'fastest': fastest[0],
        'all_results': {s: {'nfev': r.nfev, 'success': r.success} 
                       for s, r in results.items()}
    }

