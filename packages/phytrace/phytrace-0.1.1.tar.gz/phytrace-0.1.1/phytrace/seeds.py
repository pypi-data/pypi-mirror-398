"""
Seed management module for deterministic random number generation.

This module provides utilities for setting and managing random number generator
seeds across multiple libraries (numpy, random, torch, jax) to ensure
reproducible simulations.
"""

import random
from contextlib import contextmanager
from typing import Dict, Optional

import numpy as np

# Optional imports with graceful fallback
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import jax
    import jax.random as jrandom
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False


def set_global_seeds(seed: int = 42) -> Dict[str, bool]:
    """Set random number generator seeds for all available libraries.
    
    Sets seeds for:
    - numpy.random
    - Python's random module
    - torch (if available)
    - jax (if available)
    
    This is critical for reproducibility - without setting seeds, simulations
    that use random numbers will produce different results on each run.
    
    Args:
        seed: Integer seed value to use for all RNGs.
    
    Returns:
        Dictionary indicating which seeds were successfully set.
        Keys: 'numpy', 'random', 'torch', 'jax'
        Values: True if seed was set, False if library unavailable
    
    Example:
        >>> seeds_set = set_global_seeds(42)
        >>> print(seeds_set)
        {'numpy': True, 'random': True, 'torch': False, 'jax': False}
    """
    results: Dict[str, bool] = {}
    
    # NumPy
    try:
        np.random.seed(seed)
        results['numpy'] = True
    except Exception:
        results['numpy'] = False
    
    # Python random
    try:
        random.seed(seed)
        results['random'] = True
    except Exception:
        results['random'] = False
    
    # PyTorch (optional)
    if TORCH_AVAILABLE:
        try:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
            results['torch'] = True
        except Exception:
            results['torch'] = False
    else:
        results['torch'] = False
    
    # JAX (optional)
    if JAX_AVAILABLE:
        try:
            # JAX uses PRNG keys, so we create one with the seed
            # Note: This doesn't set a global state, but creates a key
            # Users should use this key for their JAX operations
            key = jrandom.PRNGKey(seed)
            results['jax'] = True
            results['jax_key'] = key  # Store the key for potential use
        except Exception:
            results['jax'] = False
    else:
        results['jax'] = False
    
    return results


def get_current_seeds() -> Dict[str, Optional[int]]:
    """Get the current state of random number generator seeds.
    
    Note: Not all RNGs expose their current state. This function returns
    what information is available.
    
    Returns:
        Dictionary with current seed/state information where available.
        None values indicate the state cannot be retrieved.
    
    Example:
        >>> state = get_current_seeds()
        >>> print(state)
        {'numpy': <numpy.random._generator.Generator object>, ...}
    """
    state: Dict[str, Optional[Any]] = {}
    
    # NumPy - get the generator state
    try:
        state['numpy'] = np.random.get_state()
    except Exception:
        state['numpy'] = None
    
    # Python random - get the state
    try:
        state['random'] = random.getstate()
    except Exception:
        state['random'] = None
    
    # PyTorch - not easily retrievable
    if TORCH_AVAILABLE:
        state['torch'] = 'available'  # Can't easily get current seed
    else:
        state['torch'] = None
    
    # JAX - uses functional PRNG, no global state
    if JAX_AVAILABLE:
        state['jax'] = 'functional_prng'  # No global state to retrieve
    else:
        state['jax'] = None
    
    return state


@contextmanager
def SeedContext(seed: int = 42):
    """Context manager for temporary seed setting.
    
    Sets seeds on entry and restores original state on exit. This is useful
    for ensuring deterministic behavior within a specific code block while
    preserving the original RNG state.
    
    Args:
        seed: Integer seed value to use within the context.
    
    Example:
        >>> with SeedContext(seed=42):
        ...     result1 = np.random.rand()
        >>> with SeedContext(seed=42):
        ...     result2 = np.random.rand()
        >>> assert result1 == result2  # Same seed, same result
    """
    # Save current states
    numpy_state = np.random.get_state() if hasattr(np.random, 'get_state') else None
    random_state = random.getstate()
    
    # Set new seeds
    set_global_seeds(seed)
    
    try:
        yield
    finally:
        # Restore original states
        if numpy_state is not None:
            try:
                np.random.set_state(numpy_state)
            except Exception:
                pass
        
        try:
            random.setstate(random_state)
        except Exception:
            pass
        
        # Note: torch and jax don't have easy state restoration
        # The context manager at least ensures seeds are set on entry

