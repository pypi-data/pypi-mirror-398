"""
Evidence pack generation module for phytrace.

Creates structured evidence packs containing all information needed to
reproduce and audit simulation results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import h5py
    H5PY_AVAILABLE = True
except ImportError:
    H5PY_AVAILABLE = False

# Import OdeResult with fallback
try:
    from scipy.integrate import OdeResult
except ImportError:
    from scipy.integrate._ivp.ivp import OdeResult

from .plotting import generate_all_plots
from .types import TraceResult


def create_evidence_pack(
    result: TraceResult,
    evidence_dir: Path,
    include_plots: bool = True,
    include_data: bool = True
) -> Path:
    """Create a structured evidence pack from a TraceResult.
    
    Creates a directory structure containing all information needed to
    reproduce and audit the simulation:
    - manifest.json: Environment and configuration
    - run_log.txt: Timestamped execution log
    - invariants.json: Invariant check results
    - data/: Trajectory data in CSV and optionally HDF5
    - plots/: Generated plots (time series, phase space, etc.)
    - checks/: Solver statistics
    - report.md: Human-readable summary
    
    Args:
        result: TraceResult from trace_run
        evidence_dir: Directory path for evidence pack
        include_plots: Whether to generate plots
        include_data: Whether to export trajectory data
    
    Returns:
        Path to the created evidence pack directory
    
    Example:
        >>> result = trace_run(...)
        >>> pack_path = create_evidence_pack(result, Path('./evidence/run_001'))
    """
    # Create directory structure
    evidence_path = Path(evidence_dir)
    evidence_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    data_dir = evidence_path / 'data'
    plots_dir = evidence_path / 'plots'
    checks_dir = evidence_path / 'checks'
    
    data_dir.mkdir(exist_ok=True)
    plots_dir.mkdir(exist_ok=True)
    checks_dir.mkdir(exist_ok=True)
    
    # 1. Write manifest.json
    manifest_path = evidence_path / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(result.manifest, f, indent=2, default=str)
    
    # 2. Write run_log.txt
    log_path = evidence_path / 'run_log.txt'
    _write_run_log(log_path, result)
    
    # 3. Write invariants.json
    invariants_path = evidence_path / 'invariants.json'
    with open(invariants_path, 'w') as f:
        json.dump(result.invariant_log, f, indent=2, default=str)
    
    # 4. Export trajectory data
    if include_data:
        _export_trajectory_data(result, data_dir)
    
    # 5. Generate plots
    if include_plots:
        generate_all_plots(result, plots_dir)
    
    # 6. Write solver stats
    solver_stats_path = checks_dir / 'solver_stats.json'
    solver_stats = {
        'nfev': int(result.nfev),
        'njev': int(result.njev) if result.njev else 0,
        'nlu': int(result.nlu) if result.nlu else 0,
        'success': bool(result.success),
        'message': str(result.message),
        'status': int(result.status)
    }
    with open(solver_stats_path, 'w') as f:
        json.dump(solver_stats, f, indent=2)
    
    # 7. Generate report.md
    report_path = evidence_path / 'report.md'
    _write_report(report_path, result)
    
    return evidence_path


def _write_run_log(log_path: Path, result: TraceResult):
    """Write timestamped run log."""
    with open(log_path, 'w') as f:
        f.write(f"Simulation Run Log\n")
        f.write(f"{'=' * 50}\n\n")
        f.write(f"Timestamp: {result.manifest.get('timestamp', 'unknown')}\n")
        f.write(f"Run ID: {result.manifest.get('run_id', 'unknown')}\n\n")
        
        f.write(f"Simulation:\n")
        sim_info = result.manifest.get('simulation', {})
        f.write(f"  Function: {sim_info.get('function', 'unknown')}\n")
        f.write(f"  Time span: {sim_info.get('t_span', [])}\n")
        f.write(f"  Solver: {sim_info.get('solver', {}).get('method', 'unknown')}\n\n")
        
        f.write(f"Solver Statistics:\n")
        stats = result.manifest.get('solver_stats', {})
        f.write(f"  Function evaluations: {stats.get('nfev', 0)}\n")
        f.write(f"  Success: {stats.get('success', False)}\n")
        f.write(f"  Message: {stats.get('message', '')}\n\n")
        
        f.write(f"Invariants:\n")
        inv_summary = result.invariant_log
        if inv_summary:
            f.write(f"  Total checks: {inv_summary.get('total_checks', 0)}\n")
            f.write(f"  Total violations: {inv_summary.get('total_violations', 0)}\n")
            for inv in inv_summary.get('invariants', []):
                f.write(f"  - {inv.get('name', 'unknown')}: "
                       f"{inv.get('violations', 0)}/{inv.get('checks', 0)} violations "
                       f"({inv.get('severity', 'unknown')})\n")
        else:
            f.write("  No invariants checked\n")
        
        violations = result.manifest.get('violations', [])
        if violations:
            f.write(f"\nViolations:\n")
            for v in violations[:10]:  # Limit to first 10
                f.write(f"  t={v.get('time', 0):.6f}: {v.get('invariant', 'unknown')} "
                       f"({v.get('severity', 'unknown')})\n")
            if len(violations) > 10:
                f.write(f"  ... and {len(violations) - 10} more\n")


def _export_trajectory_data(result: TraceResult, data_dir: Path):
    """Export trajectory data to CSV and optionally HDF5."""
    t = result.t
    y = result.y
    
    # Export to CSV using pandas if available
    if PANDAS_AVAILABLE:
        # Create DataFrame
        data_dict = {'time': t}
        n_states = y.shape[0] if len(y.shape) > 1 else 1
        if len(y.shape) == 1:
            data_dict['state_0'] = y
        else:
            for i in range(n_states):
                data_dict[f'state_{i}'] = y[i, :]
        
        df = pd.DataFrame(data_dict)
        csv_path = data_dir / 'trajectory.csv'
        df.to_csv(csv_path, index=False)
    else:
        # Fallback: write simple CSV manually
        csv_path = data_dir / 'trajectory.csv'
        with open(csv_path, 'w') as f:
            # Write header
            n_states = y.shape[0] if len(y.shape) > 1 else 1
            header = 'time,' + ','.join(f'state_{i}' for i in range(n_states))
            f.write(header + '\n')
            
            # Write data
            if len(y.shape) == 1:
                for i, t_val in enumerate(t):
                    f.write(f'{t_val},{y[i]}\n')
            else:
                for i, t_val in enumerate(t):
                    row = f'{t_val},' + ','.join(str(y[j, i]) for j in range(n_states))
                    f.write(row + '\n')
    
    # Export to HDF5 if available
    if H5PY_AVAILABLE:
        h5_path = data_dir / 'trajectory.h5'
        with h5py.File(h5_path, 'w') as f:
            f.create_dataset('time', data=t)
            f.create_dataset('state', data=y)
            # Store metadata
            f.attrs['n_states'] = y.shape[0] if len(y.shape) > 1 else 1
            f.attrs['n_points'] = len(t)


def _write_report(report_path: Path, result: TraceResult):
    """Write human-readable markdown report."""
    with open(report_path, 'w') as f:
        f.write("# Simulation Evidence Report\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        manifest = result.manifest
        sim_info = manifest.get('simulation', {})
        stats = manifest.get('solver_stats', {})
        
        f.write(f"- **Run ID**: `{manifest.get('run_id', 'unknown')}`\n")
        f.write(f"- **Timestamp**: {manifest.get('timestamp', 'unknown')}\n")
        f.write(f"- **Function**: `{sim_info.get('function', 'unknown')}`\n")
        f.write(f"- **Solver**: {sim_info.get('solver', {}).get('method', 'unknown')}\n")
        f.write(f"- **Status**: {'✓ Success' if stats.get('success') else '✗ Failed'}\n")
        f.write(f"- **Function Evaluations**: {stats.get('nfev', 0)}\n\n")
        
        # Environment
        f.write("## Environment\n\n")
        env = manifest.get('environment', {})
        python_info = env.get('python', {})
        f.write(f"- **Python**: {python_info.get('version', 'unknown')} "
               f"({python_info.get('implementation', 'unknown')})\n")
        
        platform_info = env.get('platform', {})
        f.write(f"- **Platform**: {platform_info.get('system', 'unknown')} "
               f"{platform_info.get('release', '')} on {platform_info.get('machine', 'unknown')}\n")
        
        git_info = env.get('git')
        if git_info:
            f.write(f"- **Git**: {git_info.get('branch', 'unknown')} @ "
                   f"{git_info.get('commit', 'unknown')[:8]}\n")
        f.write("\n")
        
        # Simulation Parameters
        f.write("## Simulation Parameters\n\n")
        params = sim_info.get('params', {})
        for key, value in params.items():
            if isinstance(value, (int, float)):
                f.write(f"- **{key}**: {value}\n")
            elif isinstance(value, list) and len(value) <= 5:
                f.write(f"- **{key}**: {value}\n")
            else:
                f.write(f"- **{key}**: `{type(value).__name__}`\n")
        f.write("\n")
        
        # Invariants
        f.write("## Invariant Checks\n\n")
        inv_log = result.invariant_log
        if inv_log and inv_log.get('invariants'):
            f.write("| Name | Severity | Checks | Violations | Rate |\n")
            f.write("|------|----------|--------|------------|------|\n")
            for inv in inv_log['invariants']:
                name = inv.get('name', 'unknown')
                severity = inv.get('severity', 'unknown')
                checks = inv.get('checks', 0)
                violations = inv.get('violations', 0)
                rate = inv.get('violation_rate', 0.0)
                f.write(f"| {name} | {severity} | {checks} | {violations} | {rate:.2%} |\n")
        else:
            f.write("No invariants were checked.\n")
        f.write("\n")
        
        # Solver Statistics
        f.write("## Solver Statistics\n\n")
        f.write(f"- **Function Evaluations**: {stats.get('nfev', 0)}\n")
        if stats.get('njev', 0) > 0:
            f.write(f"- **Jacobian Evaluations**: {stats.get('njev', 0)}\n")
        if stats.get('nlu', 0) > 0:
            f.write(f"- **LU Decompositions**: {stats.get('nlu', 0)}\n")
        f.write(f"- **Message**: {stats.get('message', '')}\n\n")
        
        # Files
        f.write("## Evidence Pack Contents\n\n")
        f.write("- `manifest.json`: Complete run metadata\n")
        f.write("- `run_log.txt`: Execution log\n")
        f.write("- `invariants.json`: Invariant check results\n")
        f.write("- `data/trajectory.csv`: Full trajectory data\n")
        if H5PY_AVAILABLE:
            f.write("- `data/trajectory.h5`: Trajectory data (HDF5)\n")
        f.write("- `plots/`: Generated visualization plots\n")
        f.write("- `checks/solver_stats.json`: Detailed solver statistics\n")

