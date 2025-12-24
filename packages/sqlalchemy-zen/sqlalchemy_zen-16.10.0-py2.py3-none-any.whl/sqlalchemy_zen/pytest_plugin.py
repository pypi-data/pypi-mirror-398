# -*- coding: utf-8 -*-
################################################################################
#
#  sqlalchemy-zen -- SQLAlchemy Dialect for Actian Zen
#  Copyright © 2025 Actian Corporation
#  See LICENSE.txt
#
################################################################################

"""
Pytest plugin for SQLAlchemy Zen dialect.
This ensures the Zen dialect is registered early in the test discovery process.
"""

import pytest
from sqlalchemy.dialects import registry
from sqlalchemy.testing import config as sa_testing_config
from sqlalchemy_zen.requirements import Requirements

def pytest_addoption(parser):
    """Add Zen-specific pytest options"""
    parser.addoption(
        "--zen-override-requirements",
        action="store_true",
        default=False,
        help="Override SQLAlchemy test requirements with Zen-specific requirements"
    )
    parser.addoption(
        "--skip-orm-tests",
        action="store_true",
        default=False,
        help="Skip ORM tests for Zen dialect (default: False - ORM tests are supported)"
    )

def pytest_load_initial_conftests(early_config, parser, args):
    """Load Zen dialect very early in the pytest process"""
    try:
        import sqlalchemy_zen.base
        from sqlalchemy.dialects import registry
        
        # Register the zen dialect (zen.pyodbc now available via entry point)
        registry.register("zen", "sqlalchemy_zen.base", "ZenDialect")
        
        # Ensure dialect is available in registry's impl dict
        from sqlalchemy_zen.base import ZenDialect
        registry.impls["zen"] = ZenDialect
        
        print("Zen dialect loaded in early pytest hook")
        
        # Also ensure the dialect is available in the URL parser
        from sqlalchemy.engine import url
        try:
            test_url = "zen:///?odbc_connect=test"
            parsed_url = url.make_url(test_url)
            # Force dialect loading by accessing it
            dialect = parsed_url.get_dialect()
            print("Zen dialect URL parsing test successful")
        except Exception as e:
            print(f"Zen dialect URL parsing test failed: {e}")
            
    except Exception as e:
        print(f"Warning: Could not load Zen dialect early: {e}")

def pytest_configure(config):
    """Register pytest markers and configure Zen dialect"""
    
    # Register custom markers
    config.addinivalue_line(
        "markers", "orm: marks tests as ORM tests (deselect with '-m \"not orm\"')"
    )
    config.addinivalue_line(
        "markers", "zen_skip: marks tests to be skipped for Zen dialect"
    )
    
    # Register the Zen dialect when pytest starts
    try:
        # Import and register the Zen dialect (zen.pyodbc now available via entry point)
        import sqlalchemy_zen.base
        registry.register("zen", "sqlalchemy_zen.base", "ZenDialect")
        print("Zen dialect registered as pytest plugin")
        
        # Also ensure the dialect is available for URL parsing
        from sqlalchemy.engine import url
        # This forces the dialect to be loaded into the URL parser
        try:
            test_url = "zen:///?odbc_connect=test"
            url.make_url(test_url)
        except:
            pass  # We don't care if this fails, we just want the dialect loaded
            
        # Force the dialect to be available in the registry
        from sqlalchemy.dialects import registry as dialect_registry
        from sqlalchemy_zen.base import ZenDialect
        if 'zen' not in dialect_registry.impls:
            dialect_registry.impls['zen'] = ZenDialect
            print("Zen dialect forced into registry")
        
        # Override requirements by default when Zen dialect is being used
        should_override_requirements = True

        # The getoption for --zen-override-requirements returns True when present, False when absent
        # We want to use Zen requirements by default, but allow disabling with a different flag
        # For now, just always use Zen requirements when the plugin is loaded

        # Check for environment variables (with safe fallback)
        try:
            if config.getini("zen_disable_requirements_override"):
                should_override_requirements = False
        except (ValueError, KeyError):
            pass
        
        if should_override_requirements:
            print("[Zen pytest_plugin] Overriding SQLAlchemy test requirements with Zen Requirements")
            zen_requirements = Requirements()
            sa_testing_config.requirements = zen_requirements
            # Also need to set testing.requires directly
            import sqlalchemy.testing as testing
            testing.requires = zen_requirements

            # CRITICAL: Also need to override the configuration that SQLAlchemy uses to load requirements
            # This prevents SQLAlchemy from overwriting our requirements later
            try:
                # Hook into the file configuration to change requirement_cls
                if hasattr(config, '_inicache'):
                    # For newer pytest versions
                    config._inicache['sqla_testing.requirement_cls'] = 'sqlalchemy_zen.requirements:Requirements'

                # Also try to modify any config parser that might be used
                import configparser
                if hasattr(config, 'inicfg') and config.inicfg:
                    config.inicfg.setdefault('sqla_testing', {})['requirement_cls'] = 'sqlalchemy_zen.requirements:Requirements'

                print("[Zen pytest_plugin] Modified configuration to use Zen requirements permanently")
            except Exception as cfg_e:
                print(f"[Zen pytest_plugin] Warning: Could not modify config permanently: {cfg_e}")

            # BACKUP PLAN: Monkey patch the _setup_requirements function to always use Zen requirements
            try:
                from sqlalchemy.testing.plugin import plugin_base
                original_setup_requirements = plugin_base._setup_requirements

                def zen_setup_requirements(argument):
                    print(f"[Zen pytest_plugin] Intercepted _setup_requirements call with argument: {argument}")
                    # Always use Zen requirements instead
                    from sqlalchemy.testing import config
                    from sqlalchemy import testing
                    zen_req = Requirements()
                    config.requirements = testing.requires = zen_req
                    print(f"[Zen pytest_plugin] Force-set requirements to Zen. foreign_key_constraint_reflection.enabled: {testing.requires.foreign_key_constraint_reflection.enabled}")

                # Replace the function
                plugin_base._setup_requirements = zen_setup_requirements
                print("[Zen pytest_plugin] Successfully monkey-patched _setup_requirements")
            except Exception as patch_e:
                print(f"[Zen pytest_plugin] Warning: Could not monkey-patch _setup_requirements: {patch_e}")

            # Verify the override worked
        else:
            print("[Zen pytest_plugin] Zen dialect registered (requirements not overridden)")
            
    except ImportError as e:
        print(f"Warning: Could not import Zen dialect: {e}")
    except Exception as e:
        print(f"Warning: Could not register Zen dialect: {e}")

def pytest_sessionstart(session):
    """Hook into session start to ensure Zen dialect is available before database setup"""
    try:
        import sqlalchemy_zen.base
        from sqlalchemy.dialects import registry
        from sqlalchemy_zen.base import ZenDialect
        
        # Ensure zen dialect is registered before any URL processing (zen.pyodbc via entry point)
        registry.register("zen", "sqlalchemy_zen.base", "ZenDialect")
        registry.impls["zen"] = ZenDialect
        
    except Exception as e:
        print(f"Warning: Error in pytest_sessionstart: {e}")

def pytest_collection_modifyitems(config, items):
    """Modify test collection for Zen dialect"""
    # Zen dialect DOES support ORM features as demonstrated by comprehensive tests
    # Only skip tests that are explicitly marked as incompatible with Zen

    # Check if we're running with Zen dialect
    is_zen_dialect = False

    print(f"[Zen pytest_plugin] Checking if Zen dialect is being used...")

    # Check various ways the Zen dialect might be configured
    try:
        # Check if zen dialect is in the database URL
        if hasattr(config, 'option') and hasattr(config.option, 'db'):
            db_value = str(config.option.db) if config.option.db else 'None'
            print(f"[Zen pytest_plugin] config.option.db: {db_value}")
            if 'zen' in db_value.lower():
                is_zen_dialect = True
                print(f"[Zen pytest_plugin] Zen detected in config.option.db")
    except Exception as e:
        print(f"[Zen pytest_plugin] Error checking config.option.db: {e}")

    try:
        # Check environment variables
        import os
        sqlalchemy_db = os.environ.get('SQLALCHEMY_DB', '')
        print(f"[Zen pytest_plugin] SQLALCHEMY_DB env var: {sqlalchemy_db}")
        if 'ZEN' in sqlalchemy_db.upper():
            is_zen_dialect = True
            print(f"[Zen pytest_plugin] Zen detected in SQLALCHEMY_DB")
    except Exception as e:
        print(f"[Zen pytest_plugin] Error checking SQLALCHEMY_DB: {e}")

    try:
        # Check if zen dialect is registered
        from sqlalchemy.dialects import registry
        registry_impls = list(registry.impls.keys()) if hasattr(registry, 'impls') else []
        print(f"[Zen pytest_plugin] Registry impls: {registry_impls}")
        if 'zen' in registry.impls:
            is_zen_dialect = True
            print(f"[Zen pytest_plugin] Zen detected in registry.impls")
    except Exception as e:
        print(f"[Zen pytest_plugin] Error checking registry: {e}")

    # Check command line arguments for Zen
    try:
        if hasattr(config, 'invocation_params') and hasattr(config.invocation_params, 'args'):
            args = config.invocation_params.args
            print(f"[Zen pytest_plugin] Command line args: {args}")
            for arg in args:
                if 'zen://' in str(arg):
                    is_zen_dialect = True
                    print(f"[Zen pytest_plugin] Zen detected in command line args: {arg}")
                    break
        else:
            print(f"[Zen pytest_plugin] No invocation_params.args found")
    except Exception as e:
        print(f"[Zen pytest_plugin] Error checking command line args: {e}")

    # Also check getoption for dburi
    try:
        dburi = config.getoption('--dburi', default=None)
        print(f"[Zen pytest_plugin] --dburi option: {dburi}")
        if dburi and 'zen://' in dburi:
            is_zen_dialect = True
            print(f"[Zen pytest_plugin] Zen detected in --dburi")
    except Exception as e:
        print(f"[Zen pytest_plugin] Error checking --dburi: {e}")

    print(f"[Zen pytest_plugin] Final is_zen_dialect: {is_zen_dialect}")

    if is_zen_dialect:
        # Skip tests that are known to be incompatible with Zen dialect limitations
        zen_skip = pytest.mark.skip(reason="Zen dialect limitation: special characters in identifiers not supported")
        bizarro_skipped = 0
        fk_reflection_skipped = 0

        for item in items:

            # CASE statements are fully supported in Zen - tests enabled
            # (Previously skipped due to incorrect assumption about type handling)

            # Bitwise operations: Basic ops (&, |, ^, ~) supported; shift ops (<<, >>) not supported
            # Skip only shift-specific tests if they exist
            if 'BitwiseTest' in item.nodeid and ('shift' in item.nodeid.lower() or 'lshift' in item.nodeid.lower() or 'rshift' in item.nodeid.lower()):
                item.add_marker(pytest.mark.skip(reason="Zen dialect limitation: bitwise shift operations (<<, >>) not supported"))
                continue

            # Skip BooleanTest due to NULL/constraint semantics differences in Zen BIT
            if 'BooleanTest' in item.nodeid:
                item.add_marker(pytest.mark.skip(reason="Zen dialect limitation: BIT/NULL semantics differ (non-nullable BIT)"))
                continue

            # Skip BizarroCharacterTest - these test special characters that Zen doesn't support
            if 'BizarroCharacterTest' in item.name or 'BizarroCharacterTest' in item.nodeid:
                print(f"[Zen pytest_plugin] Skipping BizarroCharacterTest: {item.name}")
                item.add_marker(zen_skip)
                bizarro_skipped += 1
                continue

            # Skip tests that require foreign_key_constraint_reflection
            if hasattr(item, 'pytestmark'):
                for mark in item.pytestmark:
                    if hasattr(mark, 'name') and 'foreign_key_constraint_reflection' in str(mark):
                        item.add_marker(pytest.mark.skip(reason="Zen dialect limitation: foreign key constraint reflection not fully supported"))
                        fk_reflection_skipped += 1
                        break

        if bizarro_skipped > 0:
            print(f"[Zen pytest_plugin] Skipped {bizarro_skipped} BizarroCharacterTest tests (special character limitations)")
        if fk_reflection_skipped > 0:
            print(f"[Zen pytest_plugin] Skipped {fk_reflection_skipped} foreign key reflection tests")

        # Check if ORM tests should be skipped (default: False - allow ORM tests)
        skip_orm_tests = config.getoption("--skip-orm-tests", default=False)

        if skip_orm_tests:
            skip_orm = pytest.mark.skip(reason="ORM features not supported in Zen dialect")
            orm_skipped = 0

            for item in items:
                # Skip tests in ORM directories
                if any(orm_path in str(item.fspath) for orm_path in ['/orm/', '\\orm\\']):
                    item.add_marker(skip_orm)
                    orm_skipped += 1

                # Skip tests with ORM-related names
                elif any(orm_keyword in item.name.lower() for orm_keyword in [
                    'orm', 'session', 'mapper', 'relationship', 'inheritance',
                    'polymorphic', 'attribute', 'inspect'
                ]):
                    item.add_marker(skip_orm)
                    orm_skipped += 1

            if orm_skipped > 0:
                print(f"[Zen pytest_plugin] Skipped {orm_skipped} ORM tests for Zen dialect")
        else:
            print(f"[Zen pytest_plugin] Allowing ORM tests for Zen dialect (use --skip-orm-tests to disable)") 