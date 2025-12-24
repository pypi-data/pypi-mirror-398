# -*- coding: utf-8 -*-
################################################################################
#
#  sqlalchemy-zen -- SQLAlchemy Dialect for Actian Zen
#  Copyright © 2025 Actian Corporation
#  See LICENSE.txt
#
################################################################################

# Zen dialect testing provision support
"""
Testing provision support for Zen dialect.

This module provides the necessary functions for SQLAlchemy's testing
framework to work properly with Zen database.
"""

from sqlalchemy.testing.provision import temp_table_keyword_args
from sqlalchemy import text


def cleanup_existing_test_tables(connection):
    """Clean up existing test tables that might interfere with tests"""
    try:
        # Ensure we're in a clean transaction state
        try:
            connection.rollback()
        except Exception:
            pass
            
        # Use Zen-specific system catalog to get table list
        # fSQLTables takes 3 parameters: database_qualifier, table_name, type
        # We need to get ALL tables and filter them, since table names might be truncated
        query = text("""
            SELECT TABLE_NAME
            FROM dbo.fSQLTables(NULL, NULL, NULL)
            WHERE TABLE_NAME LIKE 'engine_%'
               OR TABLE_NAME LIKE 'test_%'
               OR TABLE_NAME LIKE '%temp%'
               OR TABLE_NAME LIKE 'ComponentReflectionTest%'
               OR TABLE_NAME LIKE 'BinaryTest%'
               OR TABLE_NAME LIKE 'BooleanTest%'
               OR TABLE_NAME = 'info_table'
               OR TABLE_NAME LIKE 'users%'
               OR TABLE_NAME LIKE 'email_%'
               OR TABLE_NAME LIKE 'dingalings%'
               OR TABLE_NAME LIKE 'comment_test%'
               OR TABLE_NAME LIKE 'no_constraints%'
        """)

        result = connection.execute(query)
        tables_to_drop = [row[0] for row in result]

        if not tables_to_drop:
            return  # No cleanup needed

        print(f"Found {len(tables_to_drop)} test tables to clean up: {tables_to_drop}")

        # Step 1: Drop all FK constraints first to avoid dependency issues
        # We need to handle FK constraints in both directions:
        # 1. FK constraints FROM this table (this table references others)
        # 2. FK constraints TO this table (other tables reference this table)
        
        for table_name in tables_to_drop:
            try:
                # Query 1: FK constraints FROM this table (fkey_table_name = table_name)
                fk_query_from = text("""
                    SELECT FK_NAME, FKTABLE_NAME
                    FROM dbo.fSQLForeignKeys(NULL, NULL, :table_name)
                    WHERE FK_NAME IS NOT NULL
                """)
                fk_result_from = connection.execute(fk_query_from, {"table_name": table_name})

                for fk_row in fk_result_from:
                    fk_name, fk_table = fk_row[0], fk_row[1]
                    try:
                        drop_fk_query = text(f'ALTER TABLE "{fk_table}" DROP CONSTRAINT "{fk_name}"')
                        connection.execute(drop_fk_query)
                        print(f"Dropped FK constraint: {fk_name} from {fk_table}")
                    except Exception as fk_e:
                        print(f"Warning: Could not drop FK {fk_name} from {fk_table}: {fk_e}")
                        continue

                # Query 2: FK constraints TO this table (pkey_table_name = table_name)
                fk_query_to = text("""
                    SELECT FK_NAME, FKTABLE_NAME
                    FROM dbo.fSQLForeignKeys(NULL, :table_name, NULL)
                    WHERE FK_NAME IS NOT NULL
                """)
                fk_result_to = connection.execute(fk_query_to, {"table_name": table_name})

                for fk_row in fk_result_to:
                    fk_name, fk_table = fk_row[0], fk_row[1]
                    try:
                        drop_fk_query = text(f'ALTER TABLE "{fk_table}" DROP CONSTRAINT "{fk_name}"')
                        connection.execute(drop_fk_query)
                        print(f"Dropped FK constraint: {fk_name} from {fk_table} (referencing {table_name})")
                    except Exception as fk_e:
                        print(f"Warning: Could not drop FK {fk_name} from {fk_table}: {fk_e}")
                        continue

            except Exception as e:
                print(f"Warning: Could not query FK constraints for {table_name}: {e}")
                continue

        # Step 2: Now drop all tables (should succeed since FKs are gone)
        for table_name in tables_to_drop:
            try:
                drop_query = text(f'DROP TABLE "{table_name}"')
                connection.execute(drop_query)
                print(f"Cleaned up test table: {table_name}")
            except Exception as e:
                # Continue if table doesn't exist
                if "does not exist" not in str(e).lower():
                    print(f"Warning: Could not drop table {table_name}: {e}")
                continue

        # CRITICAL FIX: Ensure cleanup is committed and visible
        try:
            connection.commit()
            print("Cleanup committed successfully")
            
            # Force a connection refresh to ensure cleanup is visible
            connection.rollback()  # Rollback any pending changes
            connection.commit()    # Commit the cleanup again
            
            # Small delay to ensure cleanup is fully processed
            import time
            time.sleep(0.1)
            
            # Verify cleanup worked
            verify_query = text("""
                SELECT TABLE_NAME
                FROM dbo.fSQLTables(NULL, NULL, NULL)
                WHERE TABLE_NAME IN :table_names
            """)
            remaining_tables = connection.execute(verify_query, {"table_names": tuple(tables_to_drop)})
            remaining = [row[0] for row in remaining_tables]
            if remaining:
                print(f"Warning: Tables still exist after cleanup: {remaining}")
            else:
                print("Cleanup verification: All tables successfully removed")
                
        except Exception as e:
            print(f"Warning: Cleanup commit failed: {e}")
            # Try to rollback and continue
            try:
                connection.rollback()
            except:
                pass

    except Exception as e:
        print(f"Warning: Table cleanup failed: {e}")
        # Don't fail tests due to cleanup issues
        pass


@temp_table_keyword_args.for_db("zen")
def _zen_temp_table_keyword_args(cfg, eng):
    """Return keyword arguments for temporary table creation in Zen.

    Zen supports temporary tables with specific prefixes:
    - Local temporary tables: Use # prefix (e.g., #temp_table)
    - Global temporary tables: Use ## prefix (e.g., ##temp_table)

    For testing purposes, we use local temporary tables.
    """
    # Clean up existing test tables before running tests
    try:
        with eng.connect() as conn:
            cleanup_existing_test_tables(conn)
    except Exception as e:
        print(f"Warning: Pre-test cleanup failed: {e}")

    # Zen uses # prefix for local temporary tables
    # The table name will be automatically prefixed by the testing framework
    return {}  # No special prefixes needed - Zen handles temp tables differently


# Alternative approach if the above doesn't work - using prefixes
@temp_table_keyword_args.for_db("zen+pyodbc")
def _zen_pyodbc_temp_table_keyword_args(cfg, eng):
    """Specific support for zen+pyodbc driver"""
    # Clean up existing test tables before running tests
    try:
        with eng.connect() as conn:
            cleanup_existing_test_tables(conn)
    except Exception as e:
        print(f"Warning: Pre-test cleanup failed: {e}")

    return {}