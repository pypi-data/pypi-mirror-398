"""
Automated plotting module for phytrace.

Generates publication-ready plots for simulation results including time series,
phase space portraits, and solver statistics.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

# Import OdeResult with fallback
try:
    from scipy.integrate import OdeResult
except ImportError:
    from scipy.integrate._ivp.ivp import OdeResult

try:
    import seaborn as sns
    sns.set_style("whitegrid")
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

from .types import TraceResult


def plot_time_series(
    t: np.ndarray,
    y: np.ndarray,
    labels: Optional[List[str]] = None
) -> Figure:
    """Plot time series for all state variables.
    
    Creates a subplot for each state variable showing its evolution over time.
    
    Args:
        t: Time array
        y: State array (shape: [n_states, n_points] or [n_points] for 1D)
        labels: Optional labels for each state variable
    
    Returns:
        matplotlib Figure object
    
    Example:
        >>> fig = plot_time_series(t, y, labels=['position', 'velocity'])
        >>> fig.savefig('time_series.png')
    """
    # Handle 1D case
    if len(y.shape) == 1:
        y = y.reshape(1, -1)
    
    n_states = y.shape[0]
    n_points = y.shape[1] if len(y.shape) > 1 else len(y)
    
    # Create subplots
    fig, axes = plt.subplots(n_states, 1, figsize=(10, 3 * n_states), sharex=True)
    
    if n_states == 1:
        axes = [axes]
    
    for i in range(n_states):
        ax = axes[i]
        state_data = y[i, :] if len(y.shape) > 1 else y
        
        ax.plot(t, state_data, linewidth=2)
        ax.set_ylabel(labels[i] if labels and i < len(labels) else f'State {i}', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(t[0], t[-1])
    
    axes[-1].set_xlabel('Time', fontsize=12)
    fig.suptitle('Time Series', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return fig


def plot_phase_space(
    y: np.ndarray,
    indices: Tuple[int, int] = (0, 1),
    labels: Optional[Tuple[str, str]] = None
) -> Figure:
    """Plot 2D phase space portrait.
    
    Creates a phase portrait showing the trajectory in a 2D projection
    of the state space, with start/end markers and direction arrows.
    
    Args:
        y: State array (shape: [n_states, n_points] or [n_points] for 1D)
        indices: Tuple of two state indices to plot (default: (0, 1))
        labels: Optional labels for the two axes
    
    Returns:
        matplotlib Figure object
    
    Example:
        >>> fig = plot_phase_space(y, indices=(0, 1), labels=('x', 'v'))
        >>> fig.savefig('phase_space.png')
    """
    # Handle 1D case
    if len(y.shape) == 1:
        raise ValueError("Phase space plot requires at least 2D state. "
                        "Use plot_time_series for 1D systems.")
    
    idx1, idx2 = indices
    n_states = y.shape[0]
    
    if idx1 >= n_states or idx2 >= n_states:
        raise ValueError(f"Indices {indices} out of range for {n_states} states")
    
    state1 = y[idx1, :]
    state2 = y[idx2, :]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Plot trajectory
    ax.plot(state1, state2, 'b-', linewidth=2, alpha=0.7, label='Trajectory')
    
    # Mark start and end
    ax.plot(state1[0], state2[0], 'go', markersize=10, label='Start', zorder=5)
    ax.plot(state1[-1], state2[-1], 'ro', markersize=10, label='End', zorder=5)
    
    # Add direction arrows (sample every nth point)
    n_arrows = min(20, len(state1) // 10)
    if n_arrows > 1:
        step = len(state1) // n_arrows
        for i in range(0, len(state1) - step, step):
            dx = state1[i + step] - state1[i]
            dy = state2[i + step] - state2[i]
            # Normalize arrow length
            scale = 0.02 * np.sqrt((state1[-1] - state1[0])**2 + (state2[-1] - state2[0])**2)
            if np.sqrt(dx**2 + dy**2) > 0:
                dx_norm = dx / np.sqrt(dx**2 + dy**2) * scale
                dy_norm = dy / np.sqrt(dx**2 + dy**2) * scale
                ax.arrow(state1[i], state2[i], dx_norm, dy_norm,
                        head_width=scale*0.3, head_length=scale*0.3,
                        fc='blue', ec='blue', alpha=0.5)
    
    label1 = labels[0] if labels and len(labels) > 0 else f'State {idx1}'
    label2 = labels[1] if labels and len(labels) > 1 else f'State {idx2}'
    
    ax.set_xlabel(label1, fontsize=12)
    ax.set_ylabel(label2, fontsize=12)
    ax.set_title('Phase Space Portrait', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_aspect('auto')
    
    plt.tight_layout()
    return fig


def plot_solver_stats(result: OdeResult) -> Optional[Figure]:
    """Plot solver statistics including step size and evaluation counts.
    
    Creates plots showing:
    - Step size vs time (if dense output available)
    - Function evaluation count over time
    
    Args:
        result: OdeResult from scipy.integrate.solve_ivp
    
    Returns:
        matplotlib Figure object, or None if insufficient data
    
    Example:
        >>> fig = plot_solver_stats(ode_result)
        >>> if fig:
        ...     fig.savefig('solver_stats.png')
    """
    if not hasattr(result, 't') or result.t is None or len(result.t) < 2:
        return None
    
    t = result.t
    n_points = len(t)
    
    # Calculate step sizes
    dt = np.diff(t)
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Plot 1: Step size vs time
    ax1 = axes[0]
    ax1.semilogy(t[:-1], dt, 'b-', linewidth=2, alpha=0.7)
    ax1.set_ylabel('Step Size (log scale)', fontsize=12)
    ax1.set_title('Solver Step Size', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, which='both')
    
    # Plot 2: Cumulative function evaluations (approximate)
    ax2 = axes[1]
    # Approximate: assume evaluations are roughly proportional to steps
    # This is a simplification - actual nfev is stored in result.nfev
    cumulative_evals = np.arange(1, n_points) * (result.nfev / max(n_points - 1, 1))
    ax2.plot(t[:-1], cumulative_evals, 'g-', linewidth=2, alpha=0.7)
    ax2.set_xlabel('Time', fontsize=12)
    ax2.set_ylabel('Cumulative Evaluations (approx)', fontsize=12)
    ax2.set_title(f'Function Evaluations (total: {result.nfev})', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    fig.suptitle('Solver Statistics', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return fig


def generate_all_plots(result: TraceResult, output_dir: Path):
    """Generate all applicable plots and save to output directory.
    
    Creates and saves:
    - time_series.png: Time evolution of all state variables
    - phase_space.png: 2D phase portrait (if state dimension >= 2)
    - solver_stats.png: Solver statistics
    
    Args:
        result: TraceResult from trace_run
        output_dir: Directory to save plots
    
    Example:
        >>> generate_all_plots(result, Path('./evidence/plots'))
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Plot 1: Time series
    try:
        if hasattr(result, 't') and hasattr(result, 'y') and result.t is not None and result.y is not None:
            fig = plot_time_series(result.t, result.y)
            fig.savefig(output_dir / 'time_series.png', dpi=300, bbox_inches='tight')
            plt.close(fig)
    except Exception as e:
        # Log error but continue
        print(f"Warning: Could not generate time series plot: {e}")
    
    # Plot 2: Phase space (if applicable)
    try:
        if (hasattr(result, 'y') and result.y is not None and
            len(result.y.shape) > 1 and result.y.shape[0] >= 2):
            fig = plot_phase_space(result.y)
            fig.savefig(output_dir / 'phase_space.png', dpi=300, bbox_inches='tight')
            plt.close(fig)
    except Exception as e:
        # Log error but continue
        print(f"Warning: Could not generate phase space plot: {e}")
    
    # Plot 3: Solver statistics
    try:
        fig = plot_solver_stats(result)
        if fig:
            fig.savefig(output_dir / 'solver_stats.png', dpi=300, bbox_inches='tight')
            plt.close(fig)
    except Exception as e:
        # Log error but continue
        print(f"Warning: Could not generate solver stats plot: {e}")

