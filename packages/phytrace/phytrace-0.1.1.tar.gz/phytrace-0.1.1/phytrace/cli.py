"""
Command-line interface for phytrace.

Provides utilities for working with evidence packs, validating results,
and managing golden tests.
"""

import json
from pathlib import Path
from typing import Optional

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False
    # Fallback if click not available
    def click(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

try:
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    rprint = print

from .evidence import create_evidence_pack
from .golden import store_golden, load_golden, compare_results
from .types import TraceResult


if RICH_AVAILABLE:
    console = Console()
else:
    console = None


@click.group()
def cli():
    """phytrace: Provenance tracking for scientific simulations."""
    pass


@cli.command()
@click.argument('directory', type=click.Path())
def init(directory: str):
    """Initialize a new phytrace project.
    
    Creates example project structure with template simulation file
    and configuration.
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create example simulation file
    sim_file = dir_path / "simulation.py"
    sim_file.write_text('''"""
Example simulation using phytrace.
"""

import numpy as np
from phytrace import trace_run
from phytrace.invariants import finite, bounded

def my_system(t, y, k):
    """Example ODE: dy/dt = -k*y"""
    return -k * y

if __name__ == "__main__":
    result = trace_run(
        simulate=my_system,
        params={'k': 0.5},
        t_span=(0, 10),
        y0=[1.0],
        invariants=[finite(), bounded(-10, 10)],
        evidence_dir='./evidence/run_001'
    )
    
    print(f"Success: {result.success}")
    print(f"Function evaluations: {result.nfev}")
''')
    
    # Create configuration file
    config_file = dir_path / "phytrace.toml"
    config_file.write_text('''[evidence]
default_dir = "./evidence"
auto_plots = true
plot_format = "png"
plot_dpi = 300

[solvers]
default_method = "RK45"
default_rtol = 1e-6
default_atol = 1e-9

[invariants]
fail_on_warning = false
fail_on_error = false
fail_on_critical = true

[seeds]
default_seed = 42
''')
    
    # Create .gitignore
    gitignore = dir_path / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text('''# Evidence packs
evidence/
.golden/

# Python
__pycache__/
*.pyc
*.pyo
''')
    
    click.echo(f"✓ Initialized project in {directory}")
    click.echo(f"  Created: {sim_file.name}")
    click.echo(f"  Created: {config_file.name}")


@cli.command()
@click.argument('evidence_dir', type=click.Path(exists=True))
def validate(evidence_dir: str):
    """Validate an evidence pack.
    
    Checks completeness, verifies JSON validity, and lists any issues.
    """
    evidence_path = Path(evidence_dir)
    issues = []
    
    # Check required files
    required_files = [
        'manifest.json',
        'run_log.txt',
        'invariants.json',
        'report.md'
    ]
    
    for file in required_files:
        if not (evidence_path / file).exists():
            issues.append(f"Missing required file: {file}")
    
    # Check directories
    required_dirs = ['data', 'plots', 'checks']
    for dir_name in required_dirs:
        if not (evidence_path / dir_name).exists():
            issues.append(f"Missing required directory: {dir_name}")
    
    # Validate JSON files
    json_files = ['manifest.json', 'invariants.json']
    for json_file in json_files:
        json_path = evidence_path / json_file
        if json_path.exists():
            try:
                with open(json_path) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                issues.append(f"Invalid JSON in {json_file}: {e}")
    
    # Check data files
    data_dir = evidence_path / 'data'
    if data_dir.exists():
        if not (data_dir / 'trajectory.csv').exists():
            issues.append("Missing trajectory.csv in data/")
    
    # Report results
    if issues:
        click.echo("✗ Validation failed. Issues found:")
        for issue in issues:
            click.echo(f"  - {issue}")
        click.echo(f"\nTotal issues: {len(issues)}")
    else:
        click.echo("✓ Evidence pack is valid and complete")
        
        # Show summary
        manifest_path = evidence_path / 'manifest.json'
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            click.echo(f"\nSummary:")
            click.echo(f"  Run ID: {manifest.get('run_id', 'unknown')}")
            click.echo(f"  Timestamp: {manifest.get('timestamp', 'unknown')}")
            sim = manifest.get('simulation', {})
            click.echo(f"  Function: {sim.get('function', 'unknown')}")
            stats = manifest.get('solver_stats', {})
            click.echo(f"  Success: {stats.get('success', False)}")
            click.echo(f"  Function evaluations: {stats.get('nfev', 0)}")


@cli.command()
@click.argument('dir1', type=click.Path(exists=True))
@click.argument('dir2', type=click.Path(exists=True))
@click.option('--tolerance', default=1e-8, help='Tolerance for comparison')
def compare(dir1: str, dir2: str, tolerance: float):
    """Compare two evidence packs.
    
    Shows parameter differences and trajectory divergence.
    """
    path1 = Path(dir1)
    path2 = Path(dir2)
    
    # Load manifests
    manifest1_path = path1 / 'manifest.json'
    manifest2_path = path2 / 'manifest.json'
    
    if not manifest1_path.exists() or not manifest2_path.exists():
        click.echo("Error: Both directories must contain manifest.json")
        return
    
    with open(manifest1_path) as f:
        manifest1 = json.load(f)
    with open(manifest2_path) as f:
        manifest2 = json.load(f)
    
    # Compare parameters
    sim1 = manifest1.get('simulation', {})
    sim2 = manifest2.get('simulation', {})
    params1 = sim1.get('params', {})
    params2 = sim2.get('params', {})
    
    click.echo("Parameter Comparison:")
    all_params = set(params1.keys()) | set(params2.keys())
    param_diffs = []
    for param in all_params:
        val1 = params1.get(param, 'N/A')
        val2 = params2.get(param, 'N/A')
        if val1 != val2:
            param_diffs.append((param, val1, val2))
            click.echo(f"  {param}: {val1} → {val2}")
    
    if not param_diffs:
        click.echo("  (No parameter differences)")
    
    # Compare trajectories if available
    data1_path = path1 / 'data' / 'trajectory.csv'
    data2_path = path2 / 'data' / 'trajectory.csv'
    
    if data1_path.exists() and data2_path.exists():
        try:
            import pandas as pd
            df1 = pd.read_csv(data1_path)
            df2 = pd.read_csv(data2_path)
            
            # Simple comparison (time series)
            if 'time' in df1.columns and 'time' in df2.columns:
                # Interpolate to common times
                from scipy.interpolate import interp1d
                import numpy as np
                
                t1 = df1['time'].values
                t2 = df2['time'].values
                t_common = np.linspace(max(t1[0], t2[0]), min(t1[-1], t2[-1]), 100)
                
                state_cols1 = [c for c in df1.columns if c.startswith('state_')]
                state_cols2 = [c for c in df2.columns if c.startswith('state_')]
                
                if state_cols1 and state_cols2:
                    # Compare first state variable
                    y1 = interp1d(t1, df1[state_cols1[0]].values)(t_common)
                    y2 = interp1d(t2, df2[state_cols2[0]].values)(t_common)
                    
                    max_diff = np.max(np.abs(y1 - y2))
                    rms_diff = np.sqrt(np.mean((y1 - y2)**2))
                    
                    click.echo(f"\nTrajectory Comparison:")
                    click.echo(f"  Max difference: {max_diff:.2e}")
                    click.echo(f"  RMS difference: {rms_diff:.2e}")
                    click.echo(f"  Tolerance: {tolerance:.2e}")
                    
                    if max_diff > tolerance:
                        click.echo(f"  ✗ Trajectories differ beyond tolerance")
                    else:
                        click.echo(f"  ✓ Trajectories match within tolerance")
        except ImportError:
            click.echo("\nNote: Install pandas for trajectory comparison")
        except Exception as e:
            click.echo(f"\nError comparing trajectories: {e}")


@cli.command()
@click.argument('evidence_dir', type=click.Path(exists=True))
@click.option('--format', 'output_format', default='pdf', type=click.Choice(['pdf', 'html']))
def export(evidence_dir: str, output_format: str):
    """Export evidence pack to publication-ready format.
    
    Generates a combined report with all plots and data.
    """
    evidence_path = Path(evidence_dir)
    
    if output_format == 'pdf':
        click.echo("PDF export not yet implemented")
        click.echo("Use the report.md file for now")
    elif output_format == 'html':
        click.echo("HTML export not yet implemented")
        click.echo("Use the report.md file for now")
    else:
        click.echo(f"Unsupported format: {output_format}")


@cli.command()
@click.argument('test_name')
@click.argument('evidence_dir', type=click.Path(exists=True))
def update_golden(test_name: str, evidence_dir: str):
    """Update golden test reference from evidence pack.
    
    Loads a TraceResult from an evidence pack and stores it as a new
    golden reference.
    """
    # This would require loading TraceResult from evidence pack
    # For now, provide instructions
    click.echo(f"To update golden test '{test_name}':")
    click.echo(f"  1. Load your TraceResult")
    click.echo(f"  2. Call: store_golden(result, '{test_name}')")
    click.echo(f"\nOr use the GoldenTest class:")
    click.echo(f"  from phytrace.golden import GoldenTest")
    click.echo(f"  gt = GoldenTest('{test_name}')")
    click.echo(f"  gt.store(result)")


def main():
    """Entry point for CLI."""
    if not CLICK_AVAILABLE:
        print("Error: click is required for CLI. Install with: pip install click")
        return
    
    cli()


if __name__ == '__main__':
    main()

