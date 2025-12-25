"""
Golden test framework for regression testing of simulations.

Golden tests store reference results and compare new runs against them,
detecting when changes in code, dependencies, or environment cause
unexpected differences in simulation results.
"""

import json
import pickle
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np

try:
    import h5py
    H5PY_AVAILABLE = True
except ImportError:
    H5PY_AVAILABLE = False

from .core import trace_run
from .types import TraceResult


GOLDEN_DIR = Path(".golden")
GOLDEN_VERSION = "1.0"  # Version of golden test format


def store_golden(result: TraceResult, name: str, golden_dir: Optional[Path] = None) -> Path:
    """Store a TraceResult as a golden reference.
    
    Saves the trajectory data and metadata to be used as a reference
    for future regression tests.
    
    Args:
        result: TraceResult to store as reference
        name: Name identifier for this golden test
        golden_dir: Directory to store golden data (default: .golden/)
    
    Returns:
        Path to the stored golden reference
    
    Example:
        >>> result = trace_run(...)
        >>> golden_path = store_golden(result, "damped_oscillator_v1")
    """
    if golden_dir is None:
        golden_dir = GOLDEN_DIR
    
    golden_dir = Path(golden_dir)
    golden_dir.mkdir(parents=True, exist_ok=True)
    
    test_dir = golden_dir / name
    test_dir.mkdir(exist_ok=True)
    
    # Store trajectory data
    if H5PY_AVAILABLE:
        # Use HDF5 for efficient storage
        h5_path = test_dir / "trajectory.h5"
        with h5py.File(h5_path, 'w') as f:
            f.create_dataset('time', data=result.t, compression='gzip')
            f.create_dataset('state', data=result.y, compression='gzip')
            f.attrs['n_states'] = result.y.shape[0] if len(result.y.shape) > 1 else 1
            f.attrs['n_points'] = len(result.t)
    else:
        # Fallback to numpy compressed format
        npz_path = test_dir / "trajectory.npz"
        np.savez_compressed(npz_path, time=result.t, state=result.y)
    
    # Store metadata
    metadata = {
        'version': GOLDEN_VERSION,
        'run_id': result.manifest.get('run_id', 'unknown'),
        'timestamp': result.manifest.get('timestamp', ''),
        'simulation': result.manifest.get('simulation', {}),
        'solver_stats': result.manifest.get('solver_stats', {}),
        'environment': result.manifest.get('environment', {}),
        'n_states': result.y.shape[0] if len(result.y.shape) > 1 else 1,
        'n_points': len(result.t)
    }
    
    metadata_path = test_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    return test_dir


def load_golden(name: str, golden_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load a golden reference.
    
    Args:
        name: Name identifier for the golden test
        golden_dir: Directory containing golden data (default: .golden/)
    
    Returns:
        Dictionary with 'time', 'state', and 'metadata' keys
    
    Raises:
        FileNotFoundError: If golden reference doesn't exist
    """
    if golden_dir is None:
        golden_dir = GOLDEN_DIR
    
    test_dir = Path(golden_dir) / name
    
    if not test_dir.exists():
        raise FileNotFoundError(f"Golden reference '{name}' not found in {golden_dir}")
    
    # Load trajectory
    if H5PY_AVAILABLE:
        h5_path = test_dir / "trajectory.h5"
        if h5_path.exists():
            with h5py.File(h5_path, 'r') as f:
                time = f['time'][:]
                state = f['state'][:]
        else:
            # Fallback to npz
            npz_path = test_dir / "trajectory.npz"
            data = np.load(npz_path)
            time = data['time']
            state = data['state']
    else:
        npz_path = test_dir / "trajectory.npz"
        data = np.load(npz_path)
        time = data['time']
        state = data['state']
    
    # Load metadata
    metadata_path = test_dir / "metadata.json"
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    return {
        'time': time,
        'state': state,
        'metadata': metadata
    }


def compare_results(
    result1: TraceResult,
    result2: TraceResult,
    tolerance: float = 1e-8
) -> Dict[str, Any]:
    """Compare two TraceResults and return detailed statistics.
    
    Args:
        result1: First result (typically golden reference)
        result2: Second result (typically new run)
        tolerance: Maximum allowed difference
    
    Returns:
        Dictionary with comparison statistics including:
        - max_diff: Maximum absolute difference
        - max_rel_diff: Maximum relative difference
        - rms_diff: RMS difference
        - divergence_points: Indices where difference exceeds tolerance
        - match: Whether results match within tolerance
    """
    # Interpolate to common time points
    from scipy.interpolate import interp1d
    
    t1, y1 = result1.t, result1.y
    t2, y2 = result2.t, result2.y
    
    # Use union of time points
    t_common = np.unique(np.concatenate([t1, t2]))
    t_common = t_common[(t_common >= max(t1[0], t2[0])) & (t_common <= min(t1[-1], t2[-1]))]
    
    # Interpolate both to common times
    if len(y1.shape) == 1:
        y1_interp = interp1d(t1, y1)(t_common)
        y2_interp = interp1d(t2, y2)(t_common)
    else:
        y1_interp = np.array([interp1d(t1, y1[i, :])(t_common) for i in range(y1.shape[0])])
        y2_interp = np.array([interp1d(t2, y2[i, :])(t_common) for i in range(y2.shape[0])])
    
    # Calculate differences
    diff = np.abs(y1_interp - y2_interp)
    max_diff = np.max(diff)
    
    # Relative difference (avoid division by zero)
    with np.errstate(divide='ignore', invalid='ignore'):
        rel_diff = np.abs((y1_interp - y2_interp) / (np.abs(y1_interp) + 1e-15))
    max_rel_diff = np.max(rel_diff)
    
    # RMS difference
    rms_diff = np.sqrt(np.mean(diff**2))
    
    # Find divergence points
    divergence_mask = diff > tolerance
    divergence_points = np.where(divergence_mask)[0] if len(diff.shape) == 1 else np.where(np.any(divergence_mask, axis=0))[0]
    
    match = max_diff <= tolerance
    
    return {
        'match': match,
        'max_diff': float(max_diff),
        'max_rel_diff': float(max_rel_diff),
        'rms_diff': float(rms_diff),
        'tolerance': tolerance,
        'divergence_points': divergence_points.tolist() if len(divergence_points) > 0 else [],
        'n_divergence_points': len(divergence_points),
        'n_common_points': len(t_common)
    }


def golden_test(name: str, tolerance: float = 1e-8, golden_dir: Optional[Path] = None):
    """Decorator for golden test regression testing.
    
    Usage:
        @golden_test(name="my_test", tolerance=1e-6)
        def test_my_simulation():
            result = trace_run(...)
            return result
    
    The decorator will:
    1. Run the function to get a TraceResult
    2. Compare against stored golden reference
    3. Fail if divergence exceeds tolerance
    4. Store result as new golden if reference doesn't exist
    
    Args:
        name: Name identifier for the golden test
        tolerance: Maximum allowed difference
        golden_dir: Directory for golden data (default: .golden/)
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable[[], TraceResult]) -> Callable[[], TraceResult]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> TraceResult:
            result = func(*args, **kwargs)
            
            if golden_dir is None:
                gdir = GOLDEN_DIR
            else:
                gdir = Path(golden_dir)
            
            # Try to load golden reference
            try:
                golden_data = load_golden(name, gdir)
                
                # Create a TraceResult from golden data for comparison
                try:
                    from scipy.integrate import OdeResult
                except ImportError:
                    from scipy.integrate._ivp.ivp import OdeResult
                golden_ode_result = OdeResult(
                    t=golden_data['time'],
                    y=golden_data['state'],
                    sol=None,
                    t_events=None,
                    y_events=None,
                    nfev=0,
                    njev=0,
                    nlu=0,
                    status=0,
                    message="Golden reference",
                    success=True
                )
                
                golden_result = TraceResult(
                    ode_result=golden_ode_result,
                    evidence_dir=None,
                    manifest=golden_data['metadata'],
                    invariant_log={},
                    checks_passed=True
                )
                
                # Compare
                comparison = compare_results(golden_result, result, tolerance)
                
                if not comparison['match']:
                    raise AssertionError(
                        f"Golden test '{name}' failed:\n"
                        f"  Max difference: {comparison['max_diff']:.2e} (tolerance: {tolerance:.2e})\n"
                        f"  Max relative difference: {comparison['max_rel_diff']:.2e}\n"
                        f"  RMS difference: {comparison['rms_diff']:.2e}\n"
                        f"  Divergence points: {comparison['n_divergence_points']}/{comparison['n_common_points']}\n"
                        f"  To update golden: store_golden(result, '{name}')"
                    )
                
            except FileNotFoundError:
                # No golden reference exists, store this as new reference
                store_golden(result, name, gdir)
                print(f"Warning: No golden reference for '{name}'. Stored current result as new reference.")
            
            return result
        return wrapper
    return decorator


class GoldenTest:
    """Class-based interface for golden tests."""
    
    def __init__(self, name: str, tolerance: float = 1e-8, golden_dir: Optional[Path] = None):
        """Initialize golden test.
        
        Args:
            name: Test name identifier
            tolerance: Maximum allowed difference
            golden_dir: Directory for golden data
        """
        self.name = name
        self.tolerance = tolerance
        self.golden_dir = Path(golden_dir) if golden_dir else GOLDEN_DIR
    
    def store(self, result: TraceResult) -> Path:
        """Store result as golden reference."""
        return store_golden(result, self.name, self.golden_dir)
    
    def load(self) -> Dict[str, Any]:
        """Load golden reference."""
        return load_golden(self.name, self.golden_dir)
    
    def compare(self, result: TraceResult) -> Dict[str, Any]:
        """Compare result against golden reference."""
        golden_data = self.load()
        
        try:
            from scipy.integrate import OdeResult
        except ImportError:
            from scipy.integrate._ivp.ivp import OdeResult
        golden_ode_result = OdeResult(
            t=golden_data['time'],
            y=golden_data['state'],
            sol=None,
            t_events=None,
            y_events=None,
            nfev=0,
            njev=0,
            nlu=0,
            status=0,
            message="Golden reference",
            success=True
        )
        
        golden_result = TraceResult(
            ode_result=golden_ode_result,
            evidence_dir=None,
            manifest=golden_data['metadata'],
            invariant_log={},
            checks_passed=True
        )
        
        return compare_results(golden_result, result, self.tolerance)

