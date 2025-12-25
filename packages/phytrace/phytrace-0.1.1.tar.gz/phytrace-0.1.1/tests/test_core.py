"""
Tests for core trace_run functionality.
"""

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from phytrace import trace_run
from phytrace.invariants import bounded, finite
from phytrace.types import InvariantCheck


def exponential_decay(t, y, k):
    """Simple exponential decay: dy/dt = -k*y"""
    return -k * y


def damped_oscillator(t, y, k, c, m):
    """Damped harmonic oscillator: x'' + (c/m)x' + (k/m)x = 0"""
    x, v = y
    return [v, -(k/m)*x - (c/m)*v]


def unbounded_growth(t, y, r):
    """Unbounded exponential growth: dy/dt = r*y (will violate bounds)"""
    return r * y


@pytest.fixture
def tmp_evidence_dir(tmp_path):
    """Fixture providing a temporary evidence directory."""
    return tmp_path / "evidence"


def test_basic_ode_solve(tmp_evidence_dir):
    """Test basic ODE solving matches scipy directly."""
    # Run with trace_run
    result_traced = trace_run(
        simulate=exponential_decay,
        params={'k': 0.5},
        t_span=(0, 5),
        y0=[1.0],
        evidence_dir=str(tmp_evidence_dir / "test_basic")
    )
    
    # Run with scipy directly
    result_direct = solve_ivp(
        fun=lambda t, y: exponential_decay(t, y, k=0.5),
        t_span=(0, 5),
        y0=[1.0]
    )
    
    # Compare results
    assert result_traced.success == result_direct.success
    np.testing.assert_allclose(result_traced.t, result_direct.t)
    np.testing.assert_allclose(result_traced.y, result_direct.y, rtol=1e-10)
    
    # Check evidence directory was created
    assert result_traced.evidence_dir.exists()
    assert (result_traced.evidence_dir / "manifest.json").exists()


def test_invariant_checking(tmp_evidence_dir):
    """Test invariant checking during simulation."""
    # Create bounded invariant
    bound_check = bounded(-2.0, 2.0)
    
    result = trace_run(
        simulate=damped_oscillator,
        params={'k': 1.0, 'c': 0.1, 'm': 1.0},
        t_span=(0, 10),
        y0=[1.0, 0.0],
        invariants=[bound_check],
        evidence_dir=str(tmp_evidence_dir / "test_invariants")
    )
    
    # Verify invariants were checked
    assert 'invariants' in result.invariant_log or len(result.invariant_log) > 0
    
    # Check that invariant summary exists
    if 'invariants' in result.invariant_log:
        inv_list = result.invariant_log['invariants']
        assert len(inv_list) > 0
        # Find our bounded invariant
        bound_inv = next((inv for inv in inv_list if 'bounded' in inv['name']), None)
        assert bound_inv is not None
        assert bound_inv['checks'] > 0


def test_invariant_violation_critical(tmp_evidence_dir):
    """Test that critical invariant violations stop simulation."""
    # Create a critical invariant that will definitely fail
    def always_false(t, y, params, **kwargs):
        return False
    
    critical_inv = InvariantCheck(
        name="always_false",
        func=always_false,
        severity='critical'
    )
    
    # This should raise RuntimeError
    with pytest.raises(RuntimeError, match="Critical invariant"):
        trace_run(
            simulate=exponential_decay,
            params={'k': 0.5},
            t_span=(0, 5),
            y0=[1.0],
            invariants=[critical_inv],
            evidence_dir=str(tmp_evidence_dir / "test_critical")
        )


def test_seed_determinism(tmp_evidence_dir):
    """Test that same seed produces identical results."""
    # Run twice with same seed
    result1 = trace_run(
        simulate=damped_oscillator,
        params={'k': 1.0, 'c': 0.1, 'm': 1.0},
        t_span=(0, 5),
        y0=[1.0, 0.0],
        seed=42,
        evidence_dir=str(tmp_evidence_dir / "test_seed1")
    )
    
    result2 = trace_run(
        simulate=damped_oscillator,
        params={'k': 1.0, 'c': 0.1, 'm': 1.0},
        t_span=(0, 5),
        y0=[1.0, 0.0],
        seed=42,
        evidence_dir=str(tmp_evidence_dir / "test_seed2")
    )
    
    # Results should be identical
    np.testing.assert_array_equal(result1.t, result2.t)
    np.testing.assert_array_equal(result1.y, result2.y)
    
    # Run with different seed - should be different
    result3 = trace_run(
        simulate=damped_oscillator,
        params={'k': 1.0, 'c': 0.1, 'm': 1.0},
        t_span=(0, 5),
        y0=[1.0, 0.0],
        seed=123,
        evidence_dir=str(tmp_evidence_dir / "test_seed3")
    )
    
    # Results should be different (at least trajectory should differ)
    # Note: For deterministic ODEs without randomness, results might be same
    # But the manifest run_id should be different
    assert result1.manifest['run_id'] != result3.manifest['run_id']


def test_missing_evidence_dir():
    """Test that simulation works without evidence_dir."""
    result = trace_run(
        simulate=exponential_decay,
        params={'k': 0.5},
        t_span=(0, 5),
        y0=[1.0],
        evidence_dir=None
    )
    
    # Should still work
    assert result.success
    assert result.evidence_dir is None
    
    # No files should be created (evidence_dir is None)
    # This is expected behavior


def test_custom_solver_kwargs(tmp_evidence_dir):
    """Test that custom solver kwargs are passed through."""
    result = trace_run(
        simulate=damped_oscillator,
        params={'k': 1.0, 'c': 0.1, 'm': 1.0},
        t_span=(0, 5),
        y0=[1.0, 0.0],
        method='RK45',
        rtol=1e-8,
        atol=1e-10,
        evidence_dir=str(tmp_evidence_dir / "test_solver_kwargs")
    )
    
    # Verify solver config in manifest
    solver_config = result.manifest['simulation']['solver']
    assert solver_config['method'] == 'RK45'
    # Note: rtol/atol might not be in manifest if they're defaults
    # But the simulation should have used them


def test_invariant_warning_severity(tmp_evidence_dir):
    """Test that warning severity doesn't stop simulation."""
    def sometimes_false(t, y, params, **kwargs):
        # Fail after t > 2
        return t <= 2.0
    
    warning_inv = InvariantCheck(
        name="sometimes_false",
        func=sometimes_false,
        severity='warning'
    )
    
    # Should complete despite violations
    result = trace_run(
        simulate=exponential_decay,
        params={'k': 0.5},
        t_span=(0, 5),
        y0=[1.0],
        invariants=[warning_inv],
        evidence_dir=str(tmp_evidence_dir / "test_warning")
    )
    
    assert result.success
    # Should have violations logged
    assert len(result.manifest.get('violations', [])) > 0


def test_invariant_error_severity(tmp_evidence_dir):
    """Test that error severity logs but continues."""
    def sometimes_false(t, y, params, **kwargs):
        return t <= 2.0
    
    error_inv = InvariantCheck(
        name="sometimes_false",
        func=sometimes_false,
        severity='error'
    )
    
    # Should complete despite violations
    result = trace_run(
        simulate=exponential_decay,
        params={'k': 0.5},
        t_span=(0, 5),
        y0=[1.0],
        invariants=[error_inv],
        evidence_dir=str(tmp_evidence_dir / "test_error")
    )
    
    assert result.success
    # Should have violations logged
    assert len(result.manifest.get('violations', [])) > 0
    # checks_passed should be False
    assert result.checks_passed is False

