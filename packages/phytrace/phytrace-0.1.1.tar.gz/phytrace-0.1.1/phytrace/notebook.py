"""
Jupyter notebook integration for phytrace.

Provides magic commands and utilities for interactive use in Jupyter notebooks.
"""

from pathlib import Path
from typing import Optional

try:
    from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
    from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
    from IPython.display import display, HTML, Markdown, Image
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False

from .core import trace_run
from .evidence import create_evidence_pack
from .types import TraceResult


if IPYTHON_AVAILABLE:
    @magics_class
    class PhysimTraceMagics(Magics):
        """Magic commands for phytrace."""
        
        @cell_magic
        @magic_arguments()
        @argument('--evidence-dir', type=str, default='./evidence/notebook_run')
        @argument('--seed', type=int, default=42)
        @argument('--method', type=str, default='RK45')
        def trace_run(self, line: str, cell: str):
            """Execute a cell as a traced simulation.
            
            Usage:
                %%trace_run --evidence-dir="./evidence/run_001" --seed=42
                result = trace_run(simulate=my_func, params={...}, ...)
            """
            args = parse_argstring(self.trace_run, line)
            
            # Execute the cell
            result = self.shell.run_cell(cell)
            
            # The cell should contain trace_run call
            # We can't easily intercept it, so this is a placeholder
            # Users should call trace_run directly in the cell
            
            return result
        
        @line_magic
        def trace_display(self, line: str):
            """Display evidence pack inline.
            
            Usage:
                %trace_display ./evidence/run_001
            """
            evidence_dir = Path(line.strip())
            display_evidence(evidence_dir)
    
    def load_ipython_extension(ipython):
        """Load the extension."""
        ipython.register_magics(PhysimTraceMagics)


def display_evidence(evidence_dir: Path, inline: bool = True):
    """Display evidence pack inline in Jupyter notebook.
    
    Shows key plots and summary information from an evidence pack.
    
    Args:
        evidence_dir: Path to evidence pack directory
        inline: Whether to show inline (True) or just links (False)
    """
    if not IPYTHON_AVAILABLE:
        print("IPython is required for display_evidence")
        return
    
    evidence_path = Path(evidence_dir)
    
    if not evidence_path.exists():
        display(HTML(f"<p style='color: red;'>Evidence pack not found: {evidence_dir}</p>"))
        return
    
    # Load manifest
    manifest_path = evidence_path / 'manifest.json'
    if manifest_path.exists():
        import json
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # Display summary
        summary_html = f"""
        <h3>Simulation Summary</h3>
        <ul>
            <li><strong>Run ID:</strong> {manifest.get('run_id', 'unknown')}</li>
            <li><strong>Timestamp:</strong> {manifest.get('timestamp', 'unknown')}</li>
            <li><strong>Function:</strong> {manifest.get('simulation', {}).get('function', 'unknown')}</li>
            <li><strong>Success:</strong> {manifest.get('solver_stats', {}).get('success', False)}</li>
        </ul>
        """
        display(HTML(summary_html))
    
    # Display plots if available
    plots_dir = evidence_path / 'plots'
    if plots_dir.exists() and inline:
        plot_files = list(plots_dir.glob('*.png'))
        for plot_file in plot_files[:3]:  # Show first 3 plots
            display(Image(str(plot_file)))
    
    # Link to full evidence pack
    display(HTML(f"<p><a href='{evidence_path}' target='_blank'>Open full evidence pack</a></p>"))


def notebook_to_evidence(notebook_path: Path, output_dir: Optional[Path] = None):
    """Extract all trace_run calls from a notebook and generate combined evidence pack.
    
    Args:
        notebook_path: Path to Jupyter notebook (.ipynb)
        output_dir: Output directory for combined evidence pack
    """
    if not IPYTHON_AVAILABLE:
        print("IPython is required for notebook_to_evidence")
        return
    
    import json
    
    notebook_path = Path(notebook_path)
    
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")
    
    # Load notebook
    with open(notebook_path) as f:
        notebook = json.load(f)
    
    # Extract trace_run calls (simplified - would need AST parsing for full extraction)
    # This is a placeholder implementation
    
    if output_dir is None:
        output_dir = notebook_path.parent / 'evidence' / 'notebook_combined'
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create summary report
    report = f"""# Combined Evidence Pack from Notebook
    
    Source: {notebook_path.name}
    Generated: {Path(__file__).stat().st_mtime}
    
    This is a placeholder. Full implementation would:
    1. Parse notebook cells
    2. Extract all trace_run calls
    3. Collect evidence packs
    4. Generate cross-referenced report
    """
    
    (output_dir / 'README.md').write_text(report)
    
    return output_dir

