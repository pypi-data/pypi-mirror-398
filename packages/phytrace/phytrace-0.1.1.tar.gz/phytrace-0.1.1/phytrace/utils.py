"""
Utility functions for improved error messages and user experience.
"""

import sys
from typing import Any, Dict, Optional

try:
    from colorama import init, Fore, Style
    COLORAMA_AVAILABLE = True
    init(autoreset=True)
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback
    class Fore:
        RED = ''
        YELLOW = ''
        GREEN = ''
        BLUE = ''
        CYAN = ''
    class Style:
        RESET_ALL = ''
        BRIGHT = ''


def format_error(message: str, suggestion: Optional[str] = None) -> str:
    """Format an error message with optional suggestion.
    
    Args:
        message: Error message
        suggestion: Optional suggestion for fixing the error
    
    Returns:
        Formatted error string
    """
    if COLORAMA_AVAILABLE:
        error_str = f"{Fore.RED}Error: {message}{Style.RESET_ALL}"
        if suggestion:
            error_str += f"\n{Fore.CYAN}💡 Suggestion: {suggestion}{Style.RESET_ALL}"
    else:
        error_str = f"Error: {message}"
        if suggestion:
            error_str += f"\n💡 Suggestion: {suggestion}"
    
    return error_str


def format_warning(message: str, action: Optional[str] = None) -> str:
    """Format a warning message with optional action.
    
    Args:
        message: Warning message
        action: Optional action the user can take
    
    Returns:
        Formatted warning string
    """
    if COLORAMA_AVAILABLE:
        warn_str = f"{Fore.YELLOW}Warning: {message}{Style.RESET_ALL}"
        if action:
            warn_str += f"\n{Fore.CYAN}→ {action}{Style.RESET_ALL}"
    else:
        warn_str = f"Warning: {message}"
        if action:
            warn_str += f"\n→ {action}"
    
    return warn_str


def format_success(message: str) -> str:
    """Format a success message.
    
    Args:
        message: Success message
    
    Returns:
        Formatted success string
    """
    if COLORAMA_AVAILABLE:
        return f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}"
    else:
        return f"✓ {message}"


def validate_params(params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate simulation parameters.
    
    Args:
        params: Parameter dictionary
    
    Returns:
        (is_valid, error_message) tuple
    """
    import numpy as np
    
    for key, value in params.items():
        if isinstance(value, (int, float, np.number)):
            if not np.isfinite(value):
                return False, f"Parameter '{key}' is not finite (NaN or inf)"
        elif isinstance(value, np.ndarray):
            if not np.all(np.isfinite(value)):
                return False, f"Parameter '{key}' contains non-finite values"
        # Other types are allowed (strings, etc.)
    
    return True, None


def validate_initial_state(y0, expected_dim: Optional[int] = None) -> tuple[bool, Optional[str]]:
    """Validate initial state vector.
    
    Args:
        y0: Initial state
        expected_dim: Expected dimension (optional)
    
    Returns:
        (is_valid, error_message) tuple
    """
    import numpy as np
    
    y0_array = np.asarray(y0)
    
    if len(y0_array.shape) == 0:
        return False, "Initial state must be a vector, not a scalar"
    
    if len(y0_array.shape) > 2:
        return False, f"Initial state has too many dimensions: {y0_array.shape}"
    
    if not np.all(np.isfinite(y0_array)):
        return False, "Initial state contains non-finite values (NaN or inf)"
    
    if expected_dim is not None:
        actual_dim = y0_array.shape[0] if len(y0_array.shape) > 1 else len(y0_array)
        if actual_dim != expected_dim:
            return False, f"Initial state dimension mismatch: expected {expected_dim}, got {actual_dim}"
    
    return True, None


def format_invariant_violation(
    name: str,
    time: float,
    state: Any,
    severity: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Format an invariant violation message with helpful context.
    
    Args:
        name: Invariant name
        time: Time of violation
        state: State vector at violation
        severity: Severity level
        context: Optional additional context
    
    Returns:
        Formatted violation message
    """
    import numpy as np
    
    state_str = str(np.asarray(state)[:5])  # Show first 5 elements
    if len(np.asarray(state).flatten()) > 5:
        state_str += "..."
    
    message = f"Invariant '{name}' violated at t={time:.6f}s"
    message += f"\n  State: {state_str}"
    message += f"\n  Severity: {severity}"
    
    if context:
        for key, value in context.items():
            message += f"\n  {key}: {value}"
    
    # Add suggestions based on invariant type
    if 'energy' in name.lower():
        message += "\n  💡 Consider checking: damping term, time step size, solver tolerance"
    elif 'bounded' in name.lower():
        message += "\n  💡 Consider checking: initial conditions, parameter values, system stability"
    elif 'finite' in name.lower():
        message += "\n  💡 Consider checking: parameter values, numerical stability, solver method"
    
    return message


def print_progress(
    current_time: float,
    total_time: float,
    n_invariants_ok: int,
    total_invariants: int,
    eta: Optional[float] = None
):
    """Print progress information for long simulations.
    
    Args:
        current_time: Current simulation time
        total_time: Total simulation time
        n_invariants_ok: Number of invariants that are OK
        total_invariants: Total number of invariants
        eta: Estimated time remaining (seconds)
    """
    progress_pct = (current_time / total_time * 100) if total_time > 0 else 0
    
    if COLORAMA_AVAILABLE:
        progress_str = (
            f"{Fore.BLUE}Simulation {progress_pct:.0f}% complete{Style.RESET_ALL} | "
            f"t={current_time:.2f}/{total_time:.2f}s | "
            f"{Fore.GREEN}{n_invariants_ok}/{total_invariants} invariants OK{Style.RESET_ALL}"
        )
        if eta is not None:
            progress_str += f" | ETA {eta:.1f}s"
    else:
        progress_str = (
            f"Simulation {progress_pct:.0f}% complete | "
            f"t={current_time:.2f}/{total_time:.2f}s | "
            f"{n_invariants_ok}/{total_invariants} invariants OK"
        )
        if eta is not None:
            progress_str += f" | ETA {eta:.1f}s"
    
    print(progress_str, end='\r', file=sys.stderr)

