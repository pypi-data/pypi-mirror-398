# -*- coding: utf-8 -*-
################################################################################
#
#  sqlalchemy-zen -- SQLAlchemy Dialect for Actian Zen
#  Copyright © 2025 Actian Corporation
#  See LICENSE.txt
#
################################################################################

import sqlalchemy
from sqlalchemy import Table, Index
from sqlalchemy.schema import CreateTable, CreateIndex, DropIndex
import re
from .ddl_utils import apply_case_and_collation_to_ddl

class DDLGenerator:
    """
    DDLGenerator for Zen SQL constructs.
    - For CREATE FUNCTION/PROCEDURE, parameters must be declared as IN :param TYPE
      and referenced as :param in the body. The AS keyword is required before BEGIN.
    - Supports CASE keyword for case-insensitive columns (info={'case_sensitive': False})
    - Supports COLLATE keyword for collation (info={'collation': 'collation_name'})
    """
    def __init__(self, table, dialect):
        self.table = table
        self.dialect = dialect

    def create_table(self):
        # Use the dialect's visit_create_table to ensure Zen-specific options (like USING) are included
        from sqlalchemy.schema import CreateTable
        compiled = CreateTable(self.table).compile(dialect=self.dialect)
        ddl = str(compiled)
        
        # Remove NOT NULL from IDENTITY columns (robust to whitespace and line breaks)
        ddl = re.sub(r'(\bIDENTITY\b)\s*NOT NULL', r'\1', ddl, flags=re.IGNORECASE)
        # Remove any quotes around PRIMARY KEY clauses (should only quote column names)
        # Replace patterns like '"PRIMARY KEY (.*?)"' with 'PRIMARY KEY (\1)'
        ddl = re.sub(r'"PRIMARY KEY \((.*?)\)"', r'PRIMARY KEY (\1)', ddl)
        # Also handle possible cases where PRIMARY KEY is quoted alone
        ddl = ddl.replace('"PRIMARY KEY"', 'PRIMARY KEY')
        # Remove double parentheses if present (fix Zen SQL syntax)
        ddl = re.sub(r'\(\s*\((.*?)\)\s*\)', r'(\1)', ddl, flags=re.DOTALL)
        # Remove << ??? >> artifacts
        ddl = ddl.replace('<< ??? >>', '').replace('<<???>>', '')
        
        # Process case sensitivity and collation info AFTER removing artifacts
        ddl = apply_case_and_collation_to_ddl(self.table, ddl)
        
        # Ensure proper closing parenthesis - count opening and closing parentheses
        ddl = ddl.rstrip()
        open_count = ddl.count('(')
        close_count = ddl.count(')')
        # Add missing closing parentheses
        while close_count < open_count:
            ddl += ')'
            close_count += 1
        
        # Handle AUTOTIMESTAMP columns - ensure they have the correct syntax
        # AUTOTIMESTAMP should be added after the type but before NOT NULL
        # This is already handled in the dialect compiler, but we can add additional validation here
        
        return ddl

    # Removed duplicated _process_case_sensitivity_and_collation in favor of shared utility

    def create_index(self, index_name, *columns):
        index = Index(index_name, *columns)
        return str(CreateIndex(index).compile(dialect=self.dialect))

    def drop_index(self, index_name, *columns):
        index = Index(index_name, *columns)
        return str(DropIndex(index).compile(dialect=self.dialect))

    def add_column(self, col_name, col_type):
        # Compile type to SQL string (fixes ZenBit(<< ??? >>) bug)
        col_type_sql = col_type.compile(dialect=self.dialect)
        return f"ALTER TABLE {self.table.name} ADD COLUMN {col_name} {col_type_sql}"

    def drop_column(self, col_name):
        return f"ALTER TABLE {self.table.name} DROP COLUMN {col_name}"

    def alter_table_with(self, with_clause):
        """
        Generate ALTER TABLE statement with Zen table options.

        Zen syntax: ALTER TABLE table-name [option]
        Options are placed directly after table name, NOT preceded by WITH keyword.

        Example: ALTER TABLE my_table PAGESIZE = 4096 DCOMPRESS
        """
        return f"ALTER TABLE {self.table.name} {with_clause}"

    def create_view(self, view_name, select_clause):
        return f"CREATE VIEW {view_name} AS {select_clause}"

    def drop_view(self, view_name):
        return f"DROP VIEW {view_name}"

    def create_trigger(self, trigger_name, logic_body):
        return f"""
CREATE TRIGGER {trigger_name}
AFTER INSERT ON {self.table.name}
REFERENCING NEW AS NewRow
FOR EACH ROW
BEGIN
    {logic_body}
END;
""".strip()

    def drop_trigger(self, trigger_name):
        return f"DROP TRIGGER {trigger_name}"

    def create_function(self, func_name, args, returns, body):
        # Zen SQL: parameters must be IN :param TYPE, referenced as :param in body, AS before BEGIN
        # Compile types to SQL strings (fixes ZenBit(<< ??? >>) bug)
        args_str = ', '.join(f"IN :{name} {type_.compile(dialect=self.dialect) if hasattr(type_, 'compile') else type_}"
                             for name, type_ in args)
        # Compile return type if it's a type object
        returns_sql = returns.compile(dialect=self.dialect) if hasattr(returns, 'compile') else returns
        return f"""
CREATE FUNCTION {func_name}({args_str})
RETURNS {returns_sql}
AS
BEGIN
    {body}
END;
""".strip()

    def drop_function(self, func_name):
        return f"DROP FUNCTION {func_name}"

    def create_procedure(self, proc_name, args, body):
        # Zen SQL: parameters must be IN :param TYPE, referenced as :param in body, AS before BEGIN
        # Compile types to SQL strings (fixes ZenBit(<< ??? >>) bug)
        args_str = ', '.join(f"IN :{name} {type_.compile(dialect=self.dialect) if hasattr(type_, 'compile') else type_}"
                             for name, type_ in args)
        return f"""
CREATE PROCEDURE {proc_name}({args_str})
AS
BEGIN
    {body}
END;
""".strip()

    def drop_procedure(self, proc_name):
        return f"DROP PROCEDURE {proc_name}" 