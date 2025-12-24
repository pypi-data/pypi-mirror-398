# -*- coding: utf-8 -*-
################################################################################
#
#  sqlalchemy-zen -- SQLAlchemy Dialect for Actian Zen
#  Copyright © 2025 Actian Corporation
#  See LICENSE.txt
#
################################################################################

from sqlalchemy.testing.requirements import SuiteRequirements
from sqlalchemy.testing import exclusions

class Requirements(SuiteRequirements):
    """
    Define capability requirements for the Zen dialect.
    Defaults are set for a typical ODBC-connected database.
    Modify the @property methods to reflect your dialect's actual capabilities.
    """
    # ======================
    # General Requirements
    # ======================
    @property
    def autocommit(self):
        """Target database supports 'AUTOCOMMIT' as an isolation level."""
        return exclusions.closed()

    @property
    def temporary_tables(self):
        """Target database supports temporary tables.

        Zen uses # prefix for temp tables. The dialect auto-transforms
        SQLAlchemy's TEMPORARY keyword to # prefix.
        """
        return exclusions.open()

    @property
    def temp_table_reflection(self):
        """Target database supports reflection of temporary tables."""
        return exclusions.closed()

    # ======================
    # Identifier Handling
    # ======================
    @property
    def quoted_identifiers(self):
        """Target database supports quoted identifiers."""
        return exclusions.open()

    @property
    def emulated_quoted_identifiers(self):
        """Target database requires quoting of certain identifiers."""
        return exclusions.open()

    # ======================
    # SQL Features
    # ======================
    @property
    def subqueries(self):
        """Target database supports subqueries."""
        return exclusions.open()

    @property
    def offset(self):
        """Target database supports OFFSET with LIMIT."""
        return exclusions.open()

    @property
    def update_returning(self):
        """Target database supports UPDATE RETURNING."""
        return exclusions.closed()

    @property
    def bound_limit_offset(self):
        """Target database supports LIMIT/OFFSET using bound parameters."""
        return exclusions.open()

    @property
    def select_literals_in_parameters(self):
        """Target database supports literal parameters in SELECT list (e.g., SELECT ?)."""
        return exclusions.closed()

    @property
    def bitwise_operations(self):
        """Target database supports bitwise operations (&, |, ^, ~)."""
        return exclusions.open()  # Basic bitwise ops verified working: &, |, ^, ~

    @property
    def supports_bitwise_or(self):
        """Target database supports bitwise OR operation (|)."""
        return exclusions.open()  # Verified working

    @property
    def supports_bitwise_and(self):
        """Target database supports bitwise AND operation (&)."""
        return exclusions.open()  # Verified working

    @property
    def supports_bitwise_not(self):
        """Target database supports bitwise NOT operation (~)."""
        return exclusions.open()  # Verified working

    @property
    def supports_bitwise_xor(self):
        """Target database supports bitwise XOR operation (^)."""
        return exclusions.open()  # Verified working

    @property
    def supports_bitwise_shift(self):
        """Target database supports bitwise shift operations (<<, >>)."""
        return exclusions.skip("Bitwise shift operations (<<, >>) not supported by Zen")

    @property
    def case_statements(self):
        """Target database supports CASE statements."""
        return exclusions.open()  # All CASE features verified working

    @property
    def ctes(self):
        """Target database supports CTEs (WITH clause)."""
        return exclusions.closed()  # Tested 25-12-16: Zen returns "Syntax Error: WITH"
    
    @property
    def lateral_selects(self):
        """Target database supports LATERAL subqueries."""
        return exclusions.closed()
    
    @property
    def lateral_subqueries_in_select(self):
        """Target database supports LATERAL subqueries in SELECT statements."""
        return exclusions.closed()
    
    @property
    def lateral_subqueries(self):
        """Target database supports LATERAL subqueries in FROM clauses."""
        return exclusions.closed()
    
    @property
    def lateral_functions(self):
        """Target database supports LATERAL function calls."""
        return exclusions.closed()
    
    @property
    def from_linting(self):
        """Target database supports FROM clause linting for cartesian product detection."""
        return exclusions.closed()
    
    @property
    def update_from(self):
        """Target database supports UPDATE FROM syntax."""
        return exclusions.closed()

    @property
    def delete_from(self):
        """Target database supports DELETE FROM syntax."""
        return exclusions.closed()

    @property
    def window_functions(self):
        """Target database supports window functions."""
        return exclusions.open()

    # ======================
    # DDL Features
    # ======================
    @property
    def schemas(self):
        """Target database supports schemas (verified via test_schema_support_verification.py)."""
        return exclusions.open()

    @property
    def views(self):
        """Target database supports VIEWs."""
        return exclusions.open()

    @property
    def stored_procedures(self):
        """Target database supports stored procedures."""
        return exclusions.open()

    @property
    def triggers(self):
        """Target database supports triggers."""
        return exclusions.open()

    @property
    def user_defined_functions(self):
        """Target database supports user-defined functions."""
        return exclusions.open()

    @property
    def sequences(self):
        """Target database supports SEQUENCEs."""
        return exclusions.closed()

    @property
    def foreign_keys(self):
        """Target database supports basic foreign keys (limited enforcement)."""
        return exclusions.open()

    @property
    def check_constraints(self):
        """Target database supports CHECK constraints."""
        return exclusions.closed()  # Tested 25-12-16: Zen returns "Unsupported SQL: CHECK"

    @property
    def named_constraints(self):
        """Target database supports names for constraints."""
        return exclusions.open()

    # ======================
    # Data Types
    # ======================
    @property
    def native_boolean(self):
        """Target database supports native BOOLEAN type."""
        return exclusions.closed()

    @property
    def json_type(self):
        """Target database supports JSON type (emulated via LONGVARCHAR)."""
        return exclusions.open()  # Emulated 25-12-16: Stored as LONGVARCHAR with auto serialization

    @property
    def datetime_microseconds(self):
        """Target database supports datetime with microseconds."""
        return exclusions.open()  # Changed: Zen supports microseconds in DATETIME/TIMESTAMP

    # ======================
    # Function Support (Based on Feature Discovery)
    # ======================
    @property
    def temporal_functions(self):
        """Target database supports temporal/date-time functions."""
        return exclusions.open()  # 66.7% success rate in testing

    @property
    def mathematical_functions(self):
        """Target database supports mathematical functions."""
        return exclusions.open()  # 52.5% success rate in testing

    @property
    def string_functions(self):
        """Target database supports string manipulation functions."""
        return exclusions.open()  # 50% success rate in testing

    @property
    def uuid_functions(self):
        """Target database supports UUID/GUID generation functions."""
        return exclusions.open()  # NEWID() and UNIQUEIDENTIFIER confirmed working

    @property
    def binary_data_types(self):
        """Target database supports binary data types (BINARY, BLOB)."""
        return exclusions.open()  # BINARY and BLOB types confirmed working

    @property
    def advanced_numeric_types(self):
        """Target database supports advanced numeric types (CURRENCY, IDENTITY)."""
        return exclusions.open()  # CURRENCY and IDENTITY types confirmed working

    # ======================
    # Transaction Features
    # ======================
    @property
    def savepoints(self):
        """Target database supports savepoints."""
        return exclusions.open()

    @property
    def savepoints_w_release(self):
        """Target database supports SAVEPOINT with RELEASE."""
        return exclusions.open()

    @property
    def two_phase_transactions(self):
        """Target database supports two-phase transactions."""
        return exclusions.closed()

    # ======================
    # Connection Features
    # ======================
    @property
    def independent_cursors(self):
        """Target database supports multiple independent cursors."""
        return exclusions.open()

    @property
    def cursor_works_post_rollback(self):
        """Target database allows cursor use after rollback."""
        return exclusions.open()

    # ======================
    # Dialect-Specific Features
    # ======================
    @property
    def zen_odbc_multiple_results(self):
        """Zen ODBC driver supports multiple result sets."""
        return exclusions.closed()

    @property
    def zen_odbc_fast_executemany(self):
        """Zen ODBC driver supports fast executemany operations."""
        return exclusions.open()

    # ======================
    # Test Suite Requirements
    # ======================
    @property
    def reflects_pk_names(self):
        """Target database reflects primary key names."""
        return exclusions.closed()

    @property
    def unicode_ddl(self):
        """Target database supports Unicode in DDL statements."""
        return exclusions.open()

    # ======================
    # Error Handling
    # ======================
    @property
    def graceful_disconnects(self):
        """Target database gracefully handles connection drops."""
        return exclusions.closed()

    # ======================
    # All Other Requirements (from error messages)
    # ======================
    @property
    def returning(self):
        """Target database supports RETURNING clause."""
        return exclusions.closed()  # Tested 25-12-16: Zen returns "Syntax Error: RETURNING"

    @property
    def has_json_each(self):
        return exclusions.closed()

    @property
    def updateable_autoincrement_pks(self):
        return exclusions.closed()

    @property
    def returning_star(self):
        return exclusions.closed()

    @property
    def computed_columns_on_update_returning(self):
        return exclusions.closed()

    @property
    def dupe_order_by_ok(self):
        return exclusions.closed()

    @property
    def non_broken_binary(self):
        return exclusions.closed()

    @property
    def sequences_as_server_defaults(self):
        return exclusions.closed()

    @property
    def update_nowait(self):
        return exclusions.closed()

    @property
    def delete_using(self):
        return exclusions.closed()

    @property
    def supports_autoincrement_w_composite_pk(self):
        return exclusions.closed()

    @property
    def no_quoting_special_bind_names(self):
        return exclusions.closed()

    @property
    def select_star_mixed(self):
        return exclusions.closed()

    @property
    def provisioned_upsert(self):
        return exclusions.closed()

    @property
    def sequences_in_other_clauses(self):
        return exclusions.closed()

    @property
    def enforces_check_constraints(self):
        """Target database enforces CHECK constraints."""
        return exclusions.closed()  # Tested 25-12-16: CHECK not supported

    @property
    def multi_table_update(self):
        return exclusions.closed()

    @property
    def delete_returning(self):
        return exclusions.closed()

    # ======================
    # Missing Requirements (from error messages)
    # ======================
    
    # MSSQL-specific requirements
    @property
    def mssql_freetds(self):
        return exclusions.closed()

    @property
    def mssql_filestream(self):
        return exclusions.closed()

    # MySQL-specific requirements
    @property
    def mysql_expression_defaults(self):
        return exclusions.closed()

    @property
    def mysql_notnull_generated_columns(self):
        return exclusions.closed()

    @property
    def mysql_zero_date(self):
        return exclusions.closed()

    @property
    def mysql_non_strict(self):
        return exclusions.closed()

    @property
    def _mysql_not_mariadb_104_not_mysql8031(self):
        return exclusions.closed()

    # Oracle-specific requirements
    @property
    def cxoracle6_or_greater(self):
        return exclusions.closed()

    @property
    def oracle_test_dblink(self):
        return exclusions.closed()

    # PostgreSQL-specific requirements
    @property
    def psycopg2_compatibility(self):
        return exclusions.closed()

    @property
    def pyformat_paramstyle(self):
        return exclusions.closed()

    @property
    def btree_gist(self):
        return exclusions.closed()

    @property
    def postgresql_working_nullable_domains(self):
        return exclusions.closed()

    # SQLite-specific requirements
    @property
    def reflects_json_type(self):
        return exclusions.closed()

    # Engine-specific requirements
    @property
    def qmark_paramstyle(self):
        return exclusions.closed()

    @property
    def two_phase_recovery(self):
        return exclusions.closed()

    # ORM-specific requirements
    @property
    def update_from_returning(self):
        return exclusions.closed()

    @property
    def compat_savepoints(self):
        return exclusions.closed()

    @property
    def sql_expressions_inserted_as_primary_key(self):
        return exclusions.closed()

    # SQL-specific requirements
    @property
    def supports_sequence_for_autoincrement_column(self):
        return exclusions.closed()

    @property
    def non_native_boolean_unconstrained(self):
        return exclusions.closed()

    # Additional missing requirements from latest test run
    @property
    def mysql_fsp(self):
        return exclusions.closed()

    @property
    def mysql_ngram_fulltext(self):
        return exclusions.closed()

    @property
    def oracle_test_dblink2(self):
        return exclusions.closed()

    @property
    def any_psycopg_compatibility(self):
        return exclusions.closed()

    @property
    def hstore(self):
        return exclusions.closed()

    @property
    def sqlite_partial_indexes(self):
        return exclusions.closed()

    @property
    def format_paramstyle(self):
        return exclusions.closed()

    @property
    def update_from_using_alias(self):
        return exclusions.closed()

    @property
    def database_discards_null_for_autoincrement(self):
        return exclusions.closed()

    # Final missing requirements from latest test run
    @property
    def multiple_identity_columns(self):
        return exclusions.closed()

    @property
    def mysql_fully_case_sensitive(self):
        return exclusions.closed()

    @property
    def psycopg_or_pg8000_compatibility(self):
        return exclusions.closed()

    @property
    def postgresql_jsonb(self):
        return exclusions.closed()

    @property
    def named_paramstyle(self):
        return exclusions.closed()

    @property
    def delete_using_alias(self):
        return exclusions.closed()

    # Final missing requirement
    @property
    def native_hstore(self):
        return exclusions.closed()

    # Final missing requirement
    @property
    def postgresql_utf8_server_encoding(self):
        return exclusions.closed()

    # ======================
    # Referential Integrity Limitations (Based on RI Test Results)
    # ======================
    
    @property
    def foreign_key_constraint_reflection(self):
        """Target database accurately reflects foreign key constraints."""
        return exclusions.closed()

    @property
    def special_character_identifiers(self):
        """Target database supports identifiers with special characters like brackets, percent signs, etc."""
        return exclusions.skip("Zen database has limited support for special characters in identifiers")
    
    @property
    def check_constraint_reflection(self):
        """Target database reflects CHECK constraints."""
        return exclusions.closed()  # Tested 25-12-16: CHECK not supported
    
    @property
    def self_referencing_foreign_keys(self):
        """Target database supports self-referencing FKs in CREATE TABLE."""
        return exclusions.closed()
    
    @property
    def inline_foreign_key_constraints(self):
        """Target database supports inline FK constraints for complex scenarios."""
        return exclusions.closed()
    
    @property
    def cyclic_foreign_key_ddl(self):
        """Target database supports cyclic FK creation in single DDL batch."""
        return exclusions.closed()
    
    @property
    def deferrable_foreign_keys(self):
        """Target database supports deferrable foreign key constraints."""
        return exclusions.closed()
    
    @property
    def referential_integrity_enforcement(self):
        """Target database reliably enforces foreign key constraints."""
        return exclusions.closed()
    
    @property
    def foreign_key_cascades_set_null(self):
        """Target database supports ON DELETE SET NULL."""
        return exclusions.closed()
    
    @property
    def foreign_key_cascades_set_default(self):
        """Target database supports ON DELETE SET DEFAULT."""
        return exclusions.closed()
    
    @property
    def foreign_key_update_cascades(self):
        """Target database supports ON UPDATE CASCADE."""
        return exclusions.closed()
    
    @property
    def filtered_unique_constraints(self):
        """Target database supports filtered/partial UNIQUE constraints."""
        return exclusions.closed()
    
    @property
    def constraint_modification(self):
        """Target database supports direct constraint modification."""
        return exclusions.closed()
    
    @property
    def check_constraint_ddl(self):
        """Target database supports CHECK constraint DDL."""
        return exclusions.closed()  # Tested 25-12-16: CHECK not supported
    
    @property
    def named_check_constraints(self):
        """Target database supports named CHECK constraints."""
        return exclusions.closed()  # Tested 25-12-16: CHECK not supported
    
    @property
    def table_check_constraints(self):
        """Target database supports table-level CHECK constraints."""
        return exclusions.closed()  # Tested 25-12-16: CHECK not supported
    
    @property
    def column_check_constraints(self):
        """Target database supports column-level CHECK constraints."""
        return exclusions.closed()  # Tested 25-12-16: CHECK not supported
    
    @property
    def check_constraints_w_enforcement(self):
        """Target database enforces CHECK constraints."""
        return exclusions.closed()  # Tested 25-12-16: CHECK not supported
    
    @property
    def foreign_key_match_full(self):
        """Target database supports MATCH FULL in foreign keys."""
        return exclusions.closed()
    
    @property
    def foreign_key_match_partial(self):
        """Target database supports MATCH PARTIAL in foreign keys."""
        return exclusions.closed()
    
    @property
    def composite_foreign_key_nullable_components(self):
        """Target database handles composite FKs with nullable components reliably."""
        return exclusions.closed()
    
    @property
    def constraint_validation_control(self):
        """Target database supports VALIDATE/NOVALIDATE constraint control."""
        return exclusions.closed()
    
    @property
    def foreign_key_constraint_option_reflection_ondelete(self):
        """Target database reflects ON DELETE actions in foreign keys."""
        return exclusions.closed()
    
    @property
    def foreign_key_constraint_option_reflection_onupdate(self):
        """Target database reflects ON UPDATE actions in foreign keys."""
        return exclusions.closed()
    
    @property
    def reflects_fk_options(self):
        """Target database reflects foreign key options (ON DELETE, ON UPDATE)."""
        return exclusions.closed()
    
    @property
    def foreign_key_constraint_name_reflection(self):
        """Target database reflects foreign key constraint names."""
        return exclusions.closed()
    
    @property
    def autoincrement_insert(self):
        """Target database supports autoincrement on insert."""
        return exclusions.open()
    
    @property
    def implicitly_named_constraints(self):
        """Target database creates implicit names for unnamed constraints."""
        return exclusions.open()
    
    @property 
    def unique_constraint_reflection(self):
        """Target database reflects unique constraints."""
        return exclusions.open()
    
    @property
    def primary_key_constraint_reflection(self):
        """Target database reflects primary key constraints."""
        return exclusions.open()
    
    @property
    def index_reflection(self):
        """Target database reflects indexes."""
        return exclusions.open()
    
    @property
    def cross_schema_fk_reflection(self):
        """Target database reflects foreign keys across schemas."""
        return exclusions.closed()
    
    @property
    def fk_constraint_option_reflection_ondelete_restrict(self):
        """Target database reflects ON DELETE RESTRICT correctly."""
        return exclusions.open()
    
    @property
    def fk_constraint_option_reflection_ondelete_cascade(self):
        """Target database reflects ON DELETE CASCADE correctly."""
        return exclusions.open()
    
    @property
    def fk_constraint_option_reflection_onupdate_restrict(self):
        """Target database reflects ON UPDATE RESTRICT correctly.""" 
        return exclusions.open()
    
    @property
    def drop_table_with_foreign_key_references(self):
        """Target database allows dropping tables that are referenced by foreign keys."""
        return exclusions.closed()
    
    @property
    def fk_cyclic_table_creation(self):
        """Target database supports creating cyclic FK relationships in single DDL batch."""
        return exclusions.closed()
        
    @property 
    def fk_cyclic_constraint_handling(self):
        """Target database handles cyclic foreign key constraints properly."""
        return exclusions.closed()
        
    @property
    def fk_use_alter_constraint_creation(self):
        """Target database supports FK constraint creation with use_alter=True."""
        return exclusions.closed()
        
    @property
    def cyclic_foreign_key_reflection(self):
        """Target database reflects cyclic foreign key relationships."""
        return exclusions.closed() 