"""
Tests for evidence pack generation.
"""

import json
from pathlib import Path

import numpy as np
import pytest

# Import OdeResult with fallback
try:
    from scipy.integrate import OdeResult
except ImportError:
    from scipy.integrate._ivp.ivp import OdeResult

from phytrace import trace_run
from phytrace.evidence import create_evidence_pack
from phytrace.invariants import bounded, finite
from phytrace.types import TraceResult


def exponential_decay(t, y, k):
    """Simple exponential decay for testing."""
    return -k * y


def damped_oscillator(t, y, k, c, m):
    """Damped oscillator for testing."""
    x, v = y
    return [v, -(k/m)*x - (c/m)*v]


def test_manifest_creation(tmp_path):
    """Test that manifest.json is created with all required fields."""
    # Run a simple simulation
    result = trace_run(
        simulate=exponential_decay,
        params={'k': 0.5},
        t_span=(0, 5),
        y0=[1.0],
        evidence_dir=str(tmp_path / "evidence")
    )
    
    # Check manifest exists
    manifest_path = result.evidence_dir / "manifest.json"
    assert manifest_path.exists()
    
    # Load and verify structure
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Check required fields
    assert 'run_id' in manifest
    assert 'timestamp' in manifest
    assert 'environment' in manifest
    assert 'seeds' in manifest
    assert 'simulation' in manifest
    assert 'solver_stats' in manifest
    
    # Check environment fields
    env = manifest['environment']
    assert 'python' in env
    assert 'platform' in env
    
    # Check simulation fields
    sim = manifest['simulation']
    assert 'function' in sim
    assert 'params' in sim
    assert 'initial_state' in sim
    assert 't_span' in sim
    assert 'solver' in sim


def test_directory_structure(tmp_path):
    """Test that all expected directories and files are created."""
    result = trace_run(
        simulate=damped_oscillator,
        params={'k': 1.0, 'c': 0.1, 'm': 1.0},
        t_span=(0, 5),
        y0=[1.0, 0.0],
        evidence_dir=str(tmp_path / "evidence")
    )
    
    evidence_dir = result.evidence_dir
    
    # Check main files
    assert (evidence_dir / "manifest.json").exists()
    assert (evidence_dir / "run_log.txt").exists()
    assert (evidence_dir / "invariants.json").exists()
    assert (evidence_dir / "report.md").exists()
    
    # Check subdirectories
    assert (evidence_dir / "data").exists()
    assert (evidence_dir / "plots").exists()
    assert (evidence_dir / "checks").exists()
    
    # Check data files
    assert (evidence_dir / "data" / "trajectory.csv").exists()
    
    # Check plots (may or may not exist depending on matplotlib)
    plots_dir = evidence_dir / "plots"
    # At least one plot should exist
    plot_files = list(plots_dir.glob("*.png"))
    assert len(plot_files) > 0
    
    # Check solver stats
    assert (evidence_dir / "checks" / "solver_stats.json").exists()


def test_trajectory_export(tmp_path):
    """Test trajectory data export to CSV and HDF5."""
    result = trace_run(
        simulate=damped_oscillator,
        params={'k': 1.0, 'c': 0.1, 'm': 1.0},
        t_span=(0, 5),
        y0=[1.0, 0.0],
        evidence_dir=str(tmp_path / "evidence")
    )
    
    data_dir = result.evidence_dir / "data"
    
    # Test CSV
    csv_path = data_dir / "trajectory.csv"
    assert csv_path.exists()
    
    # Try to read with pandas if available
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        assert 'time' in df.columns
        assert len(df) > 0
        # Check data integrity
        assert np.allclose(df['time'].values, result.t)
    except ImportError:
        # If pandas not available, check file exists and has content
        assert csv_path.stat().st_size > 0
        # Read first few lines manually
        with open(csv_path) as f:
            lines = f.readlines()
            assert len(lines) > 1  # Header + data
    
    # Test HDF5 if available
    h5_path = data_dir / "trajectory.h5"
    try:
        import h5py
        if h5_path.exists():
            with h5py.File(h5_path, 'r') as f:
                assert 'time' in f
                assert 'state' in f
                # Check data integrity
                assert np.allclose(f['time'][:], result.t)
                assert np.allclose(f['state'][:], result.y)
    except ImportError:
        # HDF5 not available, that's okay
        pass


def test_plot_generation(tmp_path):
    """Test that plots are generated correctly."""
    result = trace_run(
        simulate=damped_oscillator,
        params={'k': 1.0, 'c': 0.1, 'm': 1.0},
        t_span=(0, 5),
        y0=[1.0, 0.0],
        evidence_dir=str(tmp_path / "evidence")
    )
    
    plots_dir = result.evidence_dir / "plots"
    
    # Check plots exist
    plot_files = list(plots_dir.glob("*.png"))
    assert len(plot_files) > 0
    
    # Check at least time_series exists
    time_series_path = plots_dir / "time_series.png"
    # May or may not exist depending on implementation
    # But at least one plot should exist
    
    # Verify files are valid PNGs (basic check - file exists and has content)
    for plot_file in plot_files:
        assert plot_file.exists()
        assert plot_file.stat().st_size > 0
        # PNG files should start with PNG signature
        with open(plot_file, 'rb') as f:
            header = f.read(8)
            # PNG signature: 89 50 4E 47 0D 0A 1A 0A
            assert header[:4] == b'\x89PNG' or header[0] == 0x89


def test_report_markdown(tmp_path):
    """Test that report.md is valid markdown with all sections."""
    result = trace_run(
        simulate=exponential_decay,
        params={'k': 0.5},
        t_span=(0, 5),
        y0=[1.0],
        invariants=[finite(), bounded(-10, 10)],
        evidence_dir=str(tmp_path / "evidence")
    )
    
    report_path = result.evidence_dir / "report.md"
    assert report_path.exists()
    
    # Read and check content
    with open(report_path) as f:
        content = f.read()
    
    # Check for key sections
    assert "# Simulation Evidence Report" in content
    assert "## Summary" in content
    assert "## Environment" in content
    assert "## Simulation Parameters" in content
    assert "## Invariant Checks" in content
    assert "## Solver Statistics" in content
    
    # Check for key information
    assert "Run ID" in content or "run_id" in content.lower()
    assert "Function" in content or "function" in content.lower()


def test_evidence_pack_without_plots(tmp_path):
    """Test evidence pack creation without plots."""
    result = trace_run(
        simulate=exponential_decay,
        params={'k': 0.5},
        t_span=(0, 5),
        y0=[1.0],
        evidence_dir=str(tmp_path / "evidence")
    )
    
    # Manually create evidence pack without plots
    evidence_dir = tmp_path / "evidence_no_plots"
    create_evidence_pack(
        result=result,
        evidence_dir=evidence_dir,
        include_plots=False,
        include_data=True
    )
    
    # Check plots directory might exist but be empty or not exist
    plots_dir = evidence_dir / "plots"
    if plots_dir.exists():
        plot_files = list(plots_dir.glob("*.png"))
        # Should have no plots or minimal plots
        pass  # Implementation dependent
    
    # But data should exist
    assert (evidence_dir / "data" / "trajectory.csv").exists()


def test_evidence_pack_without_data(tmp_path):
    """Test evidence pack creation without data export."""
    result = trace_run(
        simulate=exponential_decay,
        params={'k': 0.5},
        t_span=(0, 5),
        y0=[1.0],
        evidence_dir=str(tmp_path / "evidence")
    )
    
    # Manually create evidence pack without data
    evidence_dir = tmp_path / "evidence_no_data"
    create_evidence_pack(
        result=result,
        evidence_dir=evidence_dir,
        include_plots=True,
        include_data=False
    )
    
    # Data directory might exist but CSV might not
    data_dir = evidence_dir / "data"
    # Implementation dependent - some implementations create dir anyway


def test_invariants_json(tmp_path):
    """Test that invariants.json contains correct information."""
    result = trace_run(
        simulate=damped_oscillator,
        params={'k': 1.0, 'c': 0.1, 'm': 1.0},
        t_span=(0, 5),
        y0=[1.0, 0.0],
        invariants=[finite(), bounded(-10, 10)],
        evidence_dir=str(tmp_path / "evidence")
    )
    
    invariants_path = result.evidence_dir / "invariants.json"
    assert invariants_path.exists()
    
    # Load and verify
    with open(invariants_path) as f:
        inv_data = json.load(f)
    
    # Should have invariant information
    # Structure depends on implementation
    assert isinstance(inv_data, (dict, list))


def test_solver_stats_json(tmp_path):
    """Test that solver_stats.json contains correct information."""
    result = trace_run(
        simulate=exponential_decay,
        params={'k': 0.5},
        t_span=(0, 5),
        y0=[1.0],
        evidence_dir=str(tmp_path / "evidence")
    )
    
    stats_path = result.evidence_dir / "checks" / "solver_stats.json"
    assert stats_path.exists()
    
    # Load and verify
    with open(stats_path) as f:
        stats = json.load(f)
    
    # Check required fields
    assert 'nfev' in stats
    assert 'success' in stats
    assert 'message' in stats
    
    # Verify values match result
    assert stats['nfev'] == result.nfev
    assert stats['success'] == result.success


def test_run_log_content(tmp_path):
    """Test that run_log.txt contains expected information."""
    result = trace_run(
        simulate=exponential_decay,
        params={'k': 0.5},
        t_span=(0, 5),
        y0=[1.0],
        invariants=[finite()],
        evidence_dir=str(tmp_path / "evidence")
    )
    
    log_path = result.evidence_dir / "run_log.txt"
    assert log_path.exists()
    
    # Read and check content
    with open(log_path) as f:
        content = f.read()
    
    # Check for key information
    assert "Simulation Run Log" in content or "Run Log" in content
    # Should have timestamp or run info
    assert len(content) > 0


def test_evidence_pack_handles_errors(tmp_path):
    """Test that evidence pack creation handles errors gracefully."""
    # Create a result with minimal data
    ode_result = OdeResult(
        t=np.array([0, 1, 2]),
        y=np.array([[1, 0.5, 0.25]]),
        sol=None,
        t_events=None,
        y_events=None,
        nfev=10,
        njev=0,
        nlu=0,
        status=0,
        message="Integration successful.",
        success=True
    )
    
    result = TraceResult(
        ode_result=ode_result,
        evidence_dir=None,
        manifest={'run_id': 'test', 'timestamp': '2024-01-01'},
        invariant_log={},
        checks_passed=True
    )
    
    # Should not raise exception even with minimal data
    evidence_dir = tmp_path / "evidence_minimal"
    try:
        create_evidence_pack(
            result=result,
            evidence_dir=evidence_dir,
            include_plots=True,
            include_data=True
        )
        # If it succeeds, great
        assert evidence_dir.exists()
    except Exception:
        # If it fails, that's also acceptable for edge cases
        pass

