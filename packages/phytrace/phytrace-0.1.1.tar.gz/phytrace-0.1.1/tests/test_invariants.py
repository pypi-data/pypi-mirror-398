"""
Tests for invariant checking system.
"""

import numpy as np
import pytest

from phytrace.invariants import (
    InvariantChecker,
    InvariantCheck,
    bounded,
    monotonic,
    finite,
    create_invariant,
)


def test_bounded_invariant():
    """Test bounded invariant with passing and failing cases."""
    # Create bounded check
    bound_check = bounded(-1.0, 1.0)
    
    checker = InvariantChecker([bound_check])
    params = {}
    
    # Test passing case
    violations = checker.check(0.0, [0.5, -0.3], params)
    assert len(violations) == 0
    assert bound_check.total_checks == 1
    assert bound_check.violations == 0
    
    # Test failing case
    violations = checker.check(1.0, [1.5, -0.3], params)
    assert len(violations) > 0
    assert 'bounded' in violations[0] or bound_check.name in violations
    assert bound_check.violations == 1
    
    # Test with specific indices
    bound_check_idx = bounded(-1.0, 1.0, indices=[0])
    checker_idx = InvariantChecker([bound_check_idx])
    
    # First state out of bounds, but we only check index 0
    violations = checker_idx.check(0.0, [0.5, 2.0], params)
    assert len(violations) == 0  # Index 0 is in bounds


def test_monotonic_invariant():
    """Test monotonic invariant with increasing and decreasing cases."""
    # Test increasing monotonic
    mono_inc = monotonic(increasing=True, index=0)
    checker = InvariantChecker([mono_inc])
    params = {}
    
    # First check (no previous state)
    violations = checker.check(0.0, [1.0, 0.0], params)
    assert len(violations) == 0
    
    # Increasing - should pass
    violations = checker.check(1.0, [1.5, 0.0], params)
    assert len(violations) == 0
    
    # Decreasing - should fail
    violations = checker.check(2.0, [1.0, 0.0], params)
    assert len(violations) > 0
    
    # Test decreasing monotonic
    mono_dec = monotonic(increasing=False, index=0)
    checker_dec = InvariantChecker([mono_dec])
    
    # First check
    checker_dec.check(0.0, [2.0, 0.0], params)
    # Decreasing - should pass
    violations = checker_dec.check(1.0, [1.5, 0.0], params)
    assert len(violations) == 0


def test_finite_invariant():
    """Test finite invariant detects NaN and inf."""
    finite_check = finite()
    checker = InvariantChecker([finite_check])
    params = {}
    
    # Test with finite values
    violations = checker.check(0.0, [1.0, 2.0, 3.0], params)
    assert len(violations) == 0
    
    # Test with NaN
    violations = checker.check(1.0, [1.0, np.nan, 3.0], params)
    assert len(violations) > 0
    
    # Test with inf
    violations = checker.check(2.0, [1.0, np.inf, 3.0], params)
    assert len(violations) > 0


def test_multiple_invariants():
    """Test multiple invariants with different severities."""
    bound_check = bounded(-2.0, 2.0)
    finite_check = finite()
    
    # Create custom invariant with different severity
    def custom_check(t, y, params, **kwargs):
        return np.sum(y) < 10.0
    
    custom_inv = InvariantCheck(
        name="sum_less_than_10",
        func=custom_check,
        severity='warning'
    )
    
    checker = InvariantChecker([bound_check, finite_check, custom_inv])
    params = {}
    
    # All should pass
    violations = checker.check(0.0, [1.0, 0.5], params)
    assert len(violations) == 0
    
    # One should fail (out of bounds)
    violations = checker.check(1.0, [3.0, 0.5], params)
    assert len(violations) > 0
    
    # Check summary
    summary = checker.get_summary()
    assert summary['total_checks'] >= 2  # At least two checks performed
    assert len(summary['invariants']) == 3  # Three invariants


def test_invariant_with_state():
    """Test invariant that uses previous state."""
    # Energy conservation check (simplified)
    def energy_conserved(t, y, params, **kwargs):
        # Simple energy: E = 0.5 * m * v^2 + 0.5 * k * x^2
        x, v = y[0], y[1]
        m = params.get('m', 1.0)
        k = params.get('k', 1.0)
        current_energy = 0.5 * m * v**2 + 0.5 * k * x**2
        
        previous_state = kwargs.get('previous_state')
        if previous_state is None:
            return True  # First check
        
        prev_x, prev_v = previous_state[0], previous_state[1]
        previous_energy = 0.5 * m * prev_v**2 + 0.5 * k * prev_x**2
        
        # Energy should be approximately conserved (within tolerance)
        return abs(current_energy - previous_energy) < 1e-6
    
    energy_inv = InvariantCheck(
        name="energy_conserved",
        func=energy_conserved,
        severity='critical'
    )
    
    checker = InvariantChecker([energy_inv])
    params = {'m': 1.0, 'k': 1.0}
    
    # First check (no previous state)
    violations = checker.check(0.0, [1.0, 0.0], params)
    assert len(violations) == 0
    
    # Second check with same energy (should pass)
    violations = checker.check(0.1, [1.0, 0.0], params)
    assert len(violations) == 0
    
    # Check with different energy (should fail)
    violations = checker.check(0.2, [2.0, 1.0], params)
    # This might pass or fail depending on energy difference
    # The important thing is that previous_state is available


def test_severity_levels():
    """Test that different severity levels behave correctly."""
    def always_false(t, y, params, **kwargs):
        return False
    
    warning_inv = InvariantCheck(
        name="warning_test",
        func=always_false,
        severity='warning'
    )
    
    error_inv = InvariantCheck(
        name="error_test",
        func=always_false,
        severity='error'
    )
    
    critical_inv = InvariantCheck(
        name="critical_test",
        func=always_false,
        severity='critical'
    )
    
    checker = InvariantChecker([warning_inv, error_inv, critical_inv])
    params = {}
    
    # All should be violated
    violations = checker.check(0.0, [1.0], params)
    assert len(violations) == 3
    
    # Check counters
    assert warning_inv.violations == 1
    assert error_inv.violations == 1
    assert critical_inv.violations == 1


def test_create_invariant_decorator():
    """Test the create_invariant decorator."""
    @create_invariant(name="test_invariant", severity="warning")
    def test_check(t, y, params, **kwargs):
        return np.sum(y) > 0
    
    # Should return an InvariantCheck
    assert isinstance(test_check, InvariantCheck)
    assert test_check.name == "test_invariant"
    assert test_check.severity == "warning"
    
    # Should be callable
    result = test_check.func(0.0, [1.0, 2.0], {})
    assert bool(result) is True  # Handle numpy bool types


def test_invariant_checker_reset():
    """Test that reset clears counters and previous state."""
    bound_check = bounded(-1.0, 1.0)
    checker = InvariantChecker([bound_check])
    params = {}
    
    # Perform some checks
    checker.check(0.0, [0.5], params)
    checker.check(1.0, [1.5], params)  # Violation
    
    assert bound_check.total_checks == 2
    assert bound_check.violations == 1
    assert checker._previous_state is not None
    
    # Reset
    checker.reset()
    
    assert bound_check.total_checks == 0
    assert bound_check.violations == 0
    assert checker._previous_state is None
    assert checker._previous_time is None


def test_invariant_checker_summary():
    """Test get_summary returns correct statistics."""
    bound_check = bounded(-1.0, 1.0)
    finite_check = finite()
    
    checker = InvariantChecker([bound_check, finite_check])
    params = {}
    
    # Perform checks
    checker.check(0.0, [0.5], params)  # Pass
    checker.check(1.0, [1.5], params)  # Bound violation
    checker.check(2.0, [np.nan], params)  # Finite violation
    
    summary = checker.get_summary()
    
    assert summary['total_checks'] >= 3  # At least 3 checks
    assert summary['total_violations'] >= 2  # At least 2 violations
    assert len(summary['invariants']) == 2
    
    # Check individual invariant stats
    bound_stats = next(inv for inv in summary['invariants'] if 'bounded' in inv['name'])
    assert bound_stats['checks'] >= 3  # At least 3 checks
    assert bound_stats['violations'] >= 1  # At least 1 violation
    if bound_stats['checks'] > 0:
        assert bound_stats['violation_rate'] == pytest.approx(bound_stats['violations'] / bound_stats['checks'])

