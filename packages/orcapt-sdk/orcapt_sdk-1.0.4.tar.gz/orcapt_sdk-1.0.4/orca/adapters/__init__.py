"""
Adapters
========

Adapters for different deployment environments.
"""

from .lambda_adapter import LambdaAdapter, create_lambda_handler

__all__ = [
    'LambdaAdapter',
    'create_lambda_handler',
]

