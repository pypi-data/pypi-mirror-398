# -*- coding: utf-8 -*-
################################################################################
#
#  sqlalchemy-zen -- SQLAlchemy Dialect for Actian Zen
#  Copyright © 2025 Actian Corporation
#  See LICENSE.txt
#
################################################################################

from sqlalchemy.dialects import registry
from .base import ZenDialect
from .ddl_generator import DDLGenerator
from .ddl_elements import (
    CreateProcedure, DropProcedure,
    CreateTrigger, DropTrigger,
    CreateFunction, DropFunction,
    create_procedure, drop_procedure,
    create_trigger, drop_trigger,
    create_function, drop_function
)
from .types import ZenJSON

# Import provision module to register testing support
try:
    from . import provision
except ImportError:
    # Provision module is optional for non-testing usage
    pass

# Register the dialect
registry.register(
    'zen',
    'sqlalchemy_zen.base',
    'ZenDialect'
)

# Make this package a pytest plugin
pytest_plugins = ['sqlalchemy_zen.pytest_plugin']

# Optional: Explicitly expose the public API
__all__ = [
    'ZenDialect', 'DDLGenerator',
    'CreateProcedure', 'DropProcedure',
    'CreateTrigger', 'DropTrigger',
    'CreateFunction', 'DropFunction',
    'create_procedure', 'drop_procedure',
    'create_trigger', 'drop_trigger',
    'create_function', 'drop_function',
    'ZenJSON'
] 