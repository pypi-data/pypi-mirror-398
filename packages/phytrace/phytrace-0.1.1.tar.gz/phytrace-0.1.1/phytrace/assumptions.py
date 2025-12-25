"""
Assumption ledger module for phytrace.

[For v0.2] Tracks modeling assumptions and validates them during simulation.
"""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from .types import TraceResult


class AssumptionViolation(Exception):
    """Exception raised when a modeling assumption is violated."""
    
    def __init__(self, assumption_name: str, actual_value: Any, message: str = ""):
        self.assumption_name = assumption_name
        self.actual_value = actual_value
        self.message = message
        super().__init__(f"Assumption '{assumption_name}' violated: {message}")


class Assumption:
    """Represents a modeling assumption."""
    
    def __init__(self, name: str, description: str, check_func: Callable):
        self.name = name
        self.description = description
        self.check_func = check_func
        self.violations: List[Dict[str, Any]] = []
    
    def check(self, *args, **kwargs) -> bool:
        """Check if assumption holds."""
        try:
            result = self.check_func(*args, **kwargs)
            if not result:
                self.violations.append({
                    'args': args,
                    'kwargs': kwargs
                })
            return result
        except Exception as e:
            self.violations.append({
                'args': args,
                'kwargs': kwargs,
                'error': str(e)
            })
            return False


def AssumptionDecorator(assumption_name: str, description: str):
    """Decorator to mark a function with a modeling assumption.
    
    Usage:
        @Assumption("small_angle", "θ < 0.1 rad for linear approximation")
        def pendulum_linear(t, y, params):
            theta, omega = y
            if abs(theta) > 0.1:
                raise AssumptionViolation("small_angle", actual=theta)
            # linear dynamics
            ...
    
    Args:
        assumption_name: Name of the assumption
        description: Description of the assumption
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        # Store assumption metadata on function
        if not hasattr(func, '_assumptions'):
            func._assumptions = []
        
        assumption = Assumption(
            name=assumption_name,
            description=description,
            check_func=lambda *args, **kwargs: True  # Placeholder
        )
        
        func._assumptions.append(assumption)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check assumptions before execution
            for assumption in func._assumptions:
                # This is a simplified check - full implementation would
                # extract relevant values from args/kwargs
                pass
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class AssumptionLedger:
    """Tracks and validates modeling assumptions."""
    
    def __init__(self):
        self.assumptions: List[Assumption] = []
        self.violations: List[Dict[str, Any]] = []
    
    def add_assumption(self, assumption: Assumption):
        """Add an assumption to track."""
        self.assumptions.append(assumption)
    
    def check_all(self, *args, **kwargs) -> List[str]:
        """Check all assumptions and return list of violated ones."""
        violated = []
        for assumption in self.assumptions:
            if not assumption.check(*args, **kwargs):
                violated.append(assumption.name)
                self.violations.append({
                    'assumption': assumption.name,
                    'args': args,
                    'kwargs': kwargs
                })
        return violated
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of assumption checks."""
        return {
            'total_assumptions': len(self.assumptions),
            'total_violations': len(self.violations),
            'assumptions': [
                {
                    'name': a.name,
                    'description': a.description,
                    'violations': len(a.violations)
                }
                for a in self.assumptions
            ]
        }
    
    def generate_report(self) -> str:
        """Generate human-readable assumption report."""
        summary = self.get_summary()
        report = f"# Assumption Ledger Report\n\n"
        report += f"Total assumptions: {summary['total_assumptions']}\n"
        report += f"Total violations: {summary['total_violations']}\n\n"
        
        for assumption in self.assumptions:
            report += f"## {assumption.name}\n"
            report += f"{assumption.description}\n"
            report += f"Violations: {len(assumption.violations)}\n\n"
        
        return report

