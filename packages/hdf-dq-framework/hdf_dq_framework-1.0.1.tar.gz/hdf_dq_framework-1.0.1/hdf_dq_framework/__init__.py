"""
Data Quality Framework

A framework for filtering DataFrames based on Great Expectations quality rules.
Returns qualified rows and bad rows as separate DataFrames.
"""

__version__ = "0.0.0"  # Will be replaced by poetry-dynamic-versioning

try:
    from .dq_framework import DQFramework
    from .rule_processor import RuleProcessor
    from .config_examples import DQConfigExamples
except ImportError:
    from dq_framework import DQFramework
    from rule_processor import RuleProcessor
    from config_examples import DQConfigExamples

__all__ = [
    "DQFramework",
    "RuleProcessor", 
    "DQConfigExamples"
] 