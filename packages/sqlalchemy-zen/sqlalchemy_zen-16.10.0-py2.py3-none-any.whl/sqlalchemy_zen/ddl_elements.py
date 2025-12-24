# -*- coding: utf-8 -*-
################################################################################
#
#  sqlalchemy-zen -- SQLAlchemy Dialect for Actian Zen
#  Copyright © 2025 Actian Corporation
#  See LICENSE.txt
#
################################################################################

"""
DDL Elements for Zen-specific database objects.

This module provides SQLAlchemy DDL constructs for Zen-specific features
like stored procedures, triggers, and user-defined functions.
"""

from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import ClauseElement
from typing import List, Tuple, Optional


class CreateProcedure(DDLElement):
    """Represents a CREATE PROCEDURE DDL statement."""

    def __init__(self, name: str, parameters: List[Tuple[str, str]], body: str, atomic: bool = True):
        """
        Create a CREATE PROCEDURE DDL element.

        Args:
            name: Procedure name
            parameters: List of (param_name, param_type) tuples
            body: Procedure body SQL
            atomic: Whether procedure should be ATOMIC
        """
        self.name = name
        self.parameters = parameters or []
        self.body = body
        self.atomic = atomic


class DropProcedure(DDLElement):
    """Represents a DROP PROCEDURE DDL statement."""

    def __init__(self, name: str):
        """
        Create a DROP PROCEDURE DDL element.

        Args:
            name: Procedure name to drop
        """
        self.name = name


class CreateTrigger(DDLElement):
    """Represents a CREATE TRIGGER DDL statement."""

    def __init__(self, name: str, table: str, timing: str, event: str,
                 body: str, referencing: Optional[str] = None, when: Optional[str] = None):
        """
        Create a CREATE TRIGGER DDL element.

        Args:
            name: Trigger name
            table: Table name the trigger is on
            timing: 'BEFORE' or 'AFTER'
            event: 'INSERT', 'UPDATE', or 'DELETE'
            body: Trigger body SQL
            referencing: Referencing clause (e.g., "NEW AS NewRow")
            when: Optional WHEN condition
        """
        self.name = name
        self.table = table
        self.timing = timing.upper()
        self.event = event.upper()
        self.body = body
        self.referencing = referencing
        self.when = when


class DropTrigger(DDLElement):
    """Represents a DROP TRIGGER DDL statement."""

    def __init__(self, name: str):
        """
        Create a DROP TRIGGER DDL element.

        Args:
            name: Trigger name to drop
        """
        self.name = name


class CreateFunction(DDLElement):
    """Represents a CREATE FUNCTION DDL statement."""

    def __init__(self, name: str, parameters: List[Tuple[str, str]],
                 returns: str, body: str):
        """
        Create a CREATE FUNCTION DDL element.

        Args:
            name: Function name
            parameters: List of (param_name, param_type) tuples
            returns: Return type
            body: Function body SQL
        """
        self.name = name
        self.parameters = parameters or []
        self.returns = returns
        self.body = body


class DropFunction(DDLElement):
    """Represents a DROP FUNCTION DDL statement."""

    def __init__(self, name: str):
        """
        Create a DROP FUNCTION DDL element.

        Args:
            name: Function name to drop
        """
        self.name = name


# Convenience functions for creating DDL elements
def create_procedure(name: str, parameters: List[Tuple[str, str]] = None,
                    body: str = "", atomic: bool = True) -> CreateProcedure:
    """Create a CREATE PROCEDURE DDL element."""
    return CreateProcedure(name, parameters, body, atomic)


def drop_procedure(name: str) -> DropProcedure:
    """Create a DROP PROCEDURE DDL element."""
    return DropProcedure(name)


def create_trigger(name: str, table: str, timing: str, event: str,
                  body: str, referencing: Optional[str] = None,
                  when: Optional[str] = None) -> CreateTrigger:
    """Create a CREATE TRIGGER DDL element."""
    return CreateTrigger(name, table, timing, event, body, referencing, when)


def drop_trigger(name: str) -> DropTrigger:
    """Create a DROP TRIGGER DDL element."""
    return DropTrigger(name)


def create_function(name: str, parameters: List[Tuple[str, str]] = None,
                   returns: str = "INTEGER", body: str = "") -> CreateFunction:
    """Create a CREATE FUNCTION DDL element."""
    return CreateFunction(name, parameters, returns, body)


def drop_function(name: str) -> DropFunction:
    """Create a DROP FUNCTION DDL element."""
    return DropFunction(name)