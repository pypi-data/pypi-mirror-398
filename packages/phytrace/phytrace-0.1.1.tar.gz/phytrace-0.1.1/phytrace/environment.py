"""
Environment capture module for phytrace.

Captures execution environment information including Python version, platform
details, installed packages, and git repository state for reproducibility.
"""

import datetime
import platform
import socket
import sys
from typing import Any, Dict, Optional

try:
    from importlib.metadata import distributions, version
except ImportError:
    # Python < 3.8 fallback
    from importlib_metadata import distributions, version

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


def capture_environment() -> Dict[str, Any]:
    """Capture the current execution environment.
    
    Returns a dictionary containing:
    - timestamp: ISO 8601 timestamp of capture
    - python: Python version and implementation details
    - platform: System information (OS, release, machine, hostname)
    - packages: Installed package versions
    - git: Git repository state (if available)
    
    Returns:
        Dictionary with environment information. Partial information is
        returned even if some components fail to capture.
    
    Example:
        >>> env = capture_environment()
        >>> print(env['python']['version'])
        '3.11.5'
    """
    env: Dict[str, Any] = {}
    
    # Timestamp
    env['timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Python information
    try:
        env['python'] = {
            'version': platform.python_version(),
            'implementation': platform.python_implementation(),
            'executable': sys.executable,
        }
    except Exception as e:
        env['python'] = {'error': str(e)}
    
    # Platform information
    try:
        env['platform'] = {
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'hostname': socket.gethostname(),
        }
    except Exception as e:
        env['platform'] = {'error': str(e)}
    
    # Package versions
    env['packages'] = {}
    try:
        # Get versions for key packages
        key_packages = ['numpy', 'scipy', 'matplotlib', 'pandas', 'h5py']
        for pkg_name in key_packages:
            try:
                env['packages'][pkg_name] = version(pkg_name)
            except Exception:
                pass  # Package not installed
        
        # Optionally include all packages (can be large)
        # For now, we'll just include the key ones
    except Exception as e:
        env['packages'] = {'error': str(e)}
    
    # Git information (optional)
    env['git'] = _capture_git_info()
    
    return env


def _capture_git_info() -> Optional[Dict[str, Any]]:
    """Capture git repository information.
    
    Returns:
        Dictionary with git info if in a git repo, None otherwise.
    """
    if not GIT_AVAILABLE:
        return None
    
    try:
        repo = git.Repo(search_parent_directories=True)
        
        # Check if we're in a git repository
        if repo.bare:
            return None
        
        git_info: Dict[str, Any] = {
            'commit': repo.head.commit.hexsha[:8],  # Short commit hash
            'branch': repo.active_branch.name if not repo.head.is_detached else None,
            'dirty': repo.is_dirty(),
        }
        
        # Try to get remote information
        try:
            if repo.remotes:
                remote = repo.remotes[0]
                git_info['remote'] = remote.name
                git_info['remote_url'] = remote.url
        except Exception:
            pass  # No remote or error accessing it
        
        return git_info
    except (git.InvalidGitRepositoryError, git.GitCommandError, Exception):
        # Not in a git repository or git error
        return None

