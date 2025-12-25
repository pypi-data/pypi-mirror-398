"""
Configuration system for phytrace.

Supports configuration via TOML file and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomli
    TOMLI_AVAILABLE = True
except ImportError:
    try:
        import tomllib
        TOMLI_AVAILABLE = True
        tomli = tomllib  # Python 3.11+ has tomllib built-in
    except ImportError:
        TOMLI_AVAILABLE = False

# Default configuration
DEFAULT_CONFIG = {
    'evidence': {
        'default_dir': './evidence',
        'auto_plots': True,
        'plot_format': 'png',
        'plot_dpi': 300
    },
    'solvers': {
        'default_method': 'RK45',
        'default_rtol': 1e-6,
        'default_atol': 1e-9
    },
    'invariants': {
        'fail_on_warning': False,
        'fail_on_error': False,
        'fail_on_critical': True
    },
    'seeds': {
        'default_seed': 42
    }
}


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from TOML file and environment variables.
    
    Configuration is loaded in this order (later overrides earlier):
    1. Default configuration
    2. TOML file (if exists)
    3. Environment variables
    
    Environment variables use format: PHYTRACE_<SECTION>_<KEY>
    Example: PHYTRACE_EVIDENCE_DEFAULT_DIR
    
    Args:
        config_path: Path to config file (default: phytrace.toml in current dir)
    
    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Try to find config file
    if config_path is None:
        # Look in current directory and parent directories
        current = Path.cwd()
        for path in [current] + list(current.parents)[:3]:  # Check up to 3 levels up
            candidate = path / 'phytrace.toml'
            if candidate.exists():
                config_path = candidate
                break
    
    # Load from TOML if available
    if config_path and Path(config_path).exists() and TOMLI_AVAILABLE:
        try:
            with open(config_path, 'rb') as f:
                toml_config = tomli.load(f)
            
            # Merge with defaults
            for section, values in toml_config.items():
                if section in config:
                    config[section].update(values)
                else:
                    config[section] = values
        except Exception as e:
            # Silently fail - use defaults
            pass
    
    # Override with environment variables
    for section, values in config.items():
        for key in list(values.keys()):
            env_key = f"PHYTRACE_{section.upper()}_{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                # Try to convert to appropriate type
                original_value = values[key]
                if isinstance(original_value, bool):
                    config[section][key] = env_value.lower() in ('true', '1', 'yes', 'on')
                elif isinstance(original_value, int):
                    try:
                        config[section][key] = int(env_value)
                    except ValueError:
                        pass
                elif isinstance(original_value, float):
                    try:
                        config[section][key] = float(env_value)
                    except ValueError:
                        pass
                else:
                    config[section][key] = env_value
    
    return config


def get_config_value(section: str, key: str, default: Any = None) -> Any:
    """Get a configuration value.
    
    Args:
        section: Configuration section (e.g., 'evidence')
        key: Configuration key (e.g., 'default_dir')
        default: Default value if not found
    
    Returns:
        Configuration value
    """
    config = load_config()
    return config.get(section, {}).get(key, default)


# Convenience functions
def get_evidence_dir() -> str:
    """Get default evidence directory."""
    return get_config_value('evidence', 'default_dir', './evidence')


def get_default_solver_method() -> str:
    """Get default solver method."""
    return get_config_value('solvers', 'default_method', 'RK45')


def get_default_seed() -> int:
    """Get default seed."""
    return get_config_value('seeds', 'default_seed', 42)


def should_fail_on_severity(severity: str) -> bool:
    """Check if simulation should fail on invariant violation of given severity.
    
    Args:
        severity: 'warning', 'error', or 'critical'
    
    Returns:
        True if simulation should fail
    """
    return get_config_value('invariants', f'fail_on_{severity}', False)

