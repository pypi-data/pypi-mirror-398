# -*- coding: utf-8 -*-
################################################################################
#
#  sqlalchemy-zen -- SQLAlchemy Dialect for Actian Zen
#  Copyright © 2025 Actian Corporation
#  See LICENSE.txt
#
################################################################################

"""
Shared utilities for DDL processing in the Zen dialect.
Centralizes CASE and COLLATE handling to avoid duplication
between the DDL compiler and the ad-hoc DDL generator.
"""
from __future__ import annotations

import re
from typing import Optional

try:
    # SQLAlchemy column type
    from sqlalchemy.sql.schema import Column
    from sqlalchemy import Table
except Exception:  # pragma: no cover - typing/import fallback
    Column = object  # type: ignore
    Table = object  # type: ignore


def _get_collation_for_column(column: Column) -> Optional[str]:
    """Return the effective collation configured for a column, if any.
    Checks both column.type.collation and column.info["collation"].
    """
    collation = getattr(getattr(column, "type", None), "collation", None)
    if not collation and hasattr(column, "info"):
        collation = column.info.get("collation")
    return collation


def _is_case_insensitive(column: Column) -> bool:
    """Return True if the column is explicitly marked as case-insensitive.
    Driven by column.info["case_sensitive"] == False.
    """
    return bool(getattr(column, "info", {}).get("case_sensitive") is False)


def apply_case_and_collation_to_colspec(column: Column, colspec: str) -> str:
    """Normalize and append CASE/COLLATE to a single column specification.

    - Remove any pre-existing COLLATE clause
    - Append COLLATE 'name' if configured
    - Append CASE if case-insensitive is requested
    """
    # Strip any pre-existing COLLATE - handle both quoted strings (with any content including backslashes) and identifiers
    # Pattern matches: COLLATE "..." or COLLATE '...' or COLLATE identifier
    colspec = re.sub(r"\s+COLLATE\s+(?:\"[^\"]*\"|'[^']*'|\w+)", "", colspec)

    collation = _get_collation_for_column(column)
    if collation:
        # Split at COLLATE to ensure no duplicates remain (belt-and-suspenders approach)
        colspec = colspec.split(" COLLATE")[0]
        colspec += " COLLATE '" + str(collation) + "'"

    if _is_case_insensitive(column):
        # Append CASE marker (Zen extension)
        colspec += " CASE"

    return colspec


def apply_case_and_collation_to_ddl(table: Table, ddl: str) -> str:
    """Apply CASE and COLLATE to a compiled CREATE TABLE DDL string.

    This function iterates columns and injects CASE / COLLATE after the
    type token for each column, mirroring apply_case_and_collation_to_colspec.

    IMPORTANT: First strips any existing COLLATE clauses to prevent duplicates,
    since visit_create_table may have already added them.
    """
    # First, strip ALL existing COLLATE clauses from the DDL to prevent duplicates
    # This handles cases where visit_create_table already added COLLATE
    ddl = re.sub(r'\s+COLLATE\s+(?:"[^"]*"|\'[^\']*\'|\w+)', '', ddl)

    for column in table.columns:
        colname_token = f'"{column.name}"'
        # Basic pattern: "col" TYPE or "col" TYPE(precision[,scale])
        base_pattern = rf'({re.escape(colname_token)}\s+\w+(?:\(\d+(?:,\d+)?\))?)'

        # Build suffix based on settings
        suffix = ""
        if _is_case_insensitive(column):
            suffix += " CASE"
        collation = _get_collation_for_column(column)
        if collation:
            collate_clause = " COLLATE '" + str(collation) + "'"
            suffix = (suffix + collate_clause) if suffix else collate_clause

        if suffix:
            # Use re.escape on the suffix to handle backslashes in collation paths
            escaped_suffix = suffix.replace('\\', '\\\\')
            ddl = re.sub(base_pattern, rf"\1{escaped_suffix}", ddl)

    # Final cleanup of artifacts
    ddl = ddl.replace('<< ??? >>', '').replace('<<<???>>', '')
    return ddl 