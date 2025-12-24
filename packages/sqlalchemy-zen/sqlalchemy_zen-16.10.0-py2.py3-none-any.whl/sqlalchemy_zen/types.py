# -*- coding: utf-8 -*-
################################################################################
#
#  sqlalchemy-zen -- SQLAlchemy Dialect for Actian Zen
#  Copyright © 2025 Actian Corporation
#  See LICENSE.txt
#
################################################################################

from sqlalchemy import types as sa_types
from sqlalchemy.sql.compiler import GenericTypeCompiler
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.exc import CompileError
from sqlalchemy.types import TypeDecorator, Unicode, UnicodeText, Boolean, LargeBinary

# ============== BOOLEAN/BIT TYPE DEFINITIONS ==============

class ZenBit(TypeDecorator):
    """
    Zen BIT type for boolean values.
    
    Zen SQL uses BIT as its native boolean type rather than BOOLEAN.
    This type maps Python True/False to Zen's BIT type (0/1).
    """
    impl = sa_types.Integer
    __visit_name__ = 'bit'
    cache_ok = True
    inherit_cache = True
    
    def __init__(self, nullable=True, **kwargs):
        # Filter out kwargs that Integer doesn't accept
        filtered_kwargs = {}
        for key, value in kwargs.items():
            if key not in ('_create_events',):
                filtered_kwargs[key] = value
        
        # Call TypeDecorator.__init__ with no arguments to avoid Integer() argument issues
        super().__init__()
        self.nullable = nullable
    
    def load_dialect_impl(self, dialect):
        """Map to Integer for SQLAlchemy compatibility"""
        # Return a properly configured Integer instance
        return sa_types.Integer()
    
    def process_bind_param(self, value, dialect):
        """Convert Python boolean to Zen BIT (0/1)"""
        if value is None:
            return None
        # Convert various boolean-like values to 0/1
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return 1 if value else 0
        if isinstance(value, str):
            # Handle string representations
            if value.lower() in ('true', '1', 'yes', 'on'):
                return 1
            if value.lower() in ('false', '0', 'no', 'off'):
                return 0
            # Try to convert to int
            try:
                return 1 if int(value) else 0
            except (ValueError, TypeError):
                return 0
        # Default to False for unknown types
        return 0
    
    def process_result_value(self, value, dialect):
        """Convert Zen BIT (0/1) to Python boolean"""
        if value is None:
            return None
        # Convert various representations to boolean
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            # Handle string representations
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            if value.lower() in ('false', '0', 'no', 'off'):
                return False
            # Try to convert to int
            try:
                return bool(int(value))
            except (ValueError, TypeError):
                return False
        # Default to False for unknown types
        return False
    
    def copy(self, **kw):
        return type(self)(nullable=self.nullable)

# ============== TYPE DEFINITIONS ==============

class ZenTinyInt(sa_types.TypeDecorator):
    """Zen TINYINT type (1-byte integer)"""
    impl = sa_types.SmallInteger
    __visit_name__ = 'tinyint'
    cache_ok = True
    inherit_cache = True

class ZenUnsignedInt(sa_types.TypeDecorator):
    """Zen unsigned integer types with automatic promotion"""
    impl = sa_types.Integer

    def __init__(self, size_bytes):
        super().__init__()
        self.size_bytes = size_bytes
        self.__visit_name__ = f'u{"small" if size_bytes==2 else ""}int'
        self.impl_map = {
            1: sa_types.SmallInteger,
            2: sa_types.Integer,
            4: sa_types.BigInteger
        }
    
    def load_dialect_impl(self, dialect):
        # Promote unsigned types to next larger signed type
        return self.impl_map.get(self.size_bytes, sa_types.Integer)()

class ZenUBigInt(ZenUnsignedInt):
    """Zen unsigned bigint type"""
    def __init__(self):
        super().__init__(8)
        self.__visit_name__ = 'ubigint'
    
    def load_dialect_impl(self, dialect):
        # Map to BigInteger for better compatibility
        return sa_types.BigInteger()

class ZenMoney(sa_types.TypeDecorator):
    """Zen MONEY type (19,2 precision)"""
    impl = sa_types.Numeric
    __visit_name__ = 'money'
    cache_ok = True
    
    def __init__(self):
        super().__init__(precision=19, scale=2)
    
    def load_dialect_impl(self, dialect):
        return sa_types.Numeric(19, 2)

class ZenCurrency(sa_types.TypeDecorator):
    """Zen CURRENCY type (19,4 precision)"""
    impl = sa_types.Numeric
    __visit_name__ = 'currency'
    cache_ok = True
    
    def __init__(self):
        super().__init__(precision=19, scale=4)
    
    def load_dialect_impl(self, dialect):
        return sa_types.Numeric(19, 4)

class ZenLegacyNumeric(sa_types.TypeDecorator):
    """
    Zen legacy NUMERIC type with variant support (e.g., SA, SLB, SLS, STB, STS).
    """
    impl = sa_types.Numeric
    cache_ok = True

    def __init__(self, variant=None, precision=18, scale=4):
        super().__init__()
        self.variant = variant  # 'SA', 'SLB', etc.
        self.precision = precision
        self.scale = scale
        self.__visit_name__ = f'numeric{variant.lower()}' if variant else 'numeric'

    def load_dialect_impl(self, dialect):
        return sa_types.Numeric(precision=self.precision, scale=self.scale)

    def copy(self, **kw):
        return type(self)(variant=self.variant, precision=self.precision, scale=self.scale)

    @property
    def python_type(self):
        return float

    def __repr__(self):
        return (
            f"ZenLegacyNumeric(variant={self.variant!r}, precision={self.precision}, scale={self.scale})"
        )

class ZenBFloat(sa_types.TypeDecorator):
    """Zen 4-byte float (single precision)"""
    impl = sa_types.Float
    __visit_name__ = 'bfloat4'
    cache_ok = True

class ZenBFloat8(sa_types.TypeDecorator):
    """Zen 8-byte float (double precision)"""
    impl = sa_types.Double
    __visit_name__ = 'bfloat8'
    cache_ok = True

class ZenDate(sa_types.TypeDecorator):
    """Zen DATE type with null-safe processing"""
    impl = sa_types.Date
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value

    def process_result_value(self, value, dialect):
        # Defensive: treat empty string or obviously invalid as None
        if value in (None, '', '0000-00-00', '0000/00/00', '00-00-0000'):
            return None
        return value

class ZenAutoTimestamp(sa_types.TypeDecorator):
    """Zen automatic timestamp type using DEFAULT NOW()"""
    impl = sa_types.DateTime
    __visit_name__ = 'autotimestamp'
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        return sa_types.DateTime()

# ============== ZEN NATIVE IDENTITY TYPES ==============
class ZenSmallIdentity(sa_types.TypeDecorator):
    """Zen SMALLIDENTITY type (2-byte auto-increment)"""
    impl = sa_types.SmallInteger
    __visit_name__ = 'smallidentity'
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        return sa_types.SmallInteger()

class ZenIdentity(sa_types.TypeDecorator):
    """Zen IDENTITY type (4-byte auto-increment)"""
    impl = sa_types.Integer
    __visit_name__ = 'identity'
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        return sa_types.Integer()

class ZenBigIdentity(sa_types.TypeDecorator):
    """Zen BIGIDENTITY type (8-byte auto-increment)"""
    impl = sa_types.BigInteger
    __visit_name__ = 'bigidentity'
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        return sa_types.BigInteger()

class ZenUTinyInt(sa_types.TypeDecorator):
    """Zen UTINYINT type (0-255) mapped to NUMERIC(3,0) for full range preservation"""
    impl = sa_types.Numeric
    __visit_name__ = 'utinyint'
    cache_ok = True
    
    def __init__(self):
        super().__init__(precision=3, scale=0)
    
    def load_dialect_impl(self, dialect):
        return sa_types.Numeric(precision=3, scale=0)

class ZenUSmallInt(sa_types.TypeDecorator):
    """Zen USMALLINT type (0-65535) mapped to NUMERIC(5,0) for full range preservation"""
    impl = sa_types.Numeric
    __visit_name__ = 'usmallint'
    cache_ok = True
    
    def __init__(self):
        super().__init__(precision=5, scale=0)
    
    def load_dialect_impl(self, dialect):
        return sa_types.Numeric(precision=5, scale=0)

class ZenUInteger(sa_types.TypeDecorator):
    """Zen UINTEGER type (0-4,294,967,295) mapped to NUMERIC(10,0) for full range preservation"""
    impl = sa_types.Numeric
    __visit_name__ = 'uinteger'
    cache_ok = True
    
    def __init__(self):
        super().__init__(precision=10, scale=0)
    
    def load_dialect_impl(self, dialect):
        return sa_types.Numeric(precision=10, scale=0)

class ZenUBigInt(sa_types.TypeDecorator):
    """Zen UBIGINT type (0-18,446,744,073,709,551,615) mapped to NUMERIC(20,0) for full range preservation"""
    impl = sa_types.Numeric
    __visit_name__ = 'ubigint'
    cache_ok = True
    
    def __init__(self):
        super().__init__(precision=20, scale=0)
    
    def load_dialect_impl(self, dialect):
        return sa_types.Numeric(precision=20, scale=0)

# ============== TYPE REGISTRY ==============
_type_map = {
    # Boolean/Bit Types
    'BIT': ZenBit,
    'BOOLEAN': ZenBit,  # Map SQLAlchemy Boolean to ZenBit
    
    # Standard Types
    'TINYINT': ZenTinyInt,
    'SMALLINT': sa_types.SmallInteger,
    'INTEGER': sa_types.Integer,
    'BIGINT': sa_types.BigInteger,
    
    # Unsigned Types (promoted to next larger signed type)
    'UTINYINT': ZenUTinyInt,   # promote to SMALLINT
    'USMALLINT': ZenUSmallInt,       # promote to INTEGER
    'UINTEGER': ZenUInteger,     # promote to BIGINT
    'UBIGINT': ZenUBigInt,         # promote to NUMERIC
    
    # Financial Types
    'MONEY': ZenMoney,
    'CURRENCY': ZenCurrency,
    
    # Legacy Numeric
    'NUMERICSA': ZenLegacyNumeric,
    'NUMERICSLB': ZenLegacyNumeric,
    'NUMERICSLS': ZenLegacyNumeric,
    'NUMERICSTB': ZenLegacyNumeric,
    'NUMERICSTS': ZenLegacyNumeric,
    
    # Floating Point
    'BFLOAT4': ZenBFloat,
    'BFLOAT8': ZenBFloat8,
    'REAL': sa_types.Float,
    'DOUBLE': sa_types.Double,
    
    # Date/Time
    'DATE': ZenDate,
    'TIME': sa_types.Time,
    'TIMESTAMP': sa_types.TIMESTAMP,
    'DATETIME': sa_types.DateTime,
    
    # String Types
    'CHAR': sa_types.CHAR,
    'VARCHAR': sa_types.VARCHAR,
    'TEXT': sa_types.TEXT,
    'LONGVARCHAR': sa_types.TEXT,
    
    # Binary Types
    'BINARY': sa_types.BINARY,
    'VARBINARY': sa_types.VARBINARY,
    'LONG BINARY': sa_types.LargeBinary,
    
    # Auto-increment
    'SMALLIDENTITY': ZenSmallIdentity,
    'IDENTITY': ZenIdentity,
    'BIGIDENTITY': ZenBigIdentity,
    # Legacy AUTOINCREMENT mappings (for backward compatibility)
    'AUTOINCREMENT(2)': ZenSmallIdentity,
    'AUTOINCREMENT(4)': ZenIdentity,
    'AUTOINCREMENT(8)': ZenBigIdentity,
}

# ============== TYPE COMPILER ==============
class ZenTypeCompiler(GenericTypeCompiler):
    """Type compiler for Zen custom types with pattern prevention."""

    def process(self, type_, **kw):
        """Process type with pattern prevention"""
        if type_ is None:
            raise CompileError("Type is None")

        # PREVENTION: Set Zen-specific context
        zen_kw = kw.copy()
        zen_kw['zen_dialect'] = True

        try:
            result = super().process(type_, **zen_kw)

            # PREVENTION: Fix known type patterns that cause << ??? >>
            if isinstance(result, str):
                result = self._prevent_type_patterns(result)

            return result
        except Exception as e:
            # Enhanced error handling for type compilation
            raise CompileError(f"Failed to compile type {type_}: {str(e)}", None, e) from e

    def _prevent_type_patterns(self, type_str):
        """Prevent common type patterns that generate << ??? >>"""
        import re

        # Known type patterns that need prevention
        type_fixes = {
            'LONG VARCHAR': 'LONGVARCHAR',
            'LONG NVARCHAR': 'NLONGVARCHAR',
            'LONG VARBINARY': 'LONGVARBINARY',
        }

        for old_pattern, replacement in type_fixes.items():
            type_str = type_str.replace(old_pattern, replacement)

        # Prevent any remaining << ??? >> patterns in types
        type_str = re.sub(r'<<\s*\?\?\?\s*>>', '', type_str)

        return type_str
    
    def visit_numeric(self, type_, **kw):
        """Override Numeric to emit no space after comma"""
        if type_.precision is not None and type_.scale is not None:
            return f"NUMERIC({type_.precision},{type_.scale})"
        elif type_.precision is not None:
            return f"NUMERIC({type_.precision})"
        else:
            return "NUMERIC"
    
    def visit_bit(self, type_, **kw):
        """Compile ZenBit to Zen's BIT type"""
        return "BIT"
    
    def visit_tinyint(self, type_, **kw):
        return "TINYINT"

    # Unsigned Ints (emit original Zen type names for DDL)
    def visit_utinyint(self, type_, **kw):
        return "UTINYINT"
    
    def visit_usmallint(self, type_, **kw):
        return "USMALLINT"
    
    def visit_uinteger(self, type_, **kw):
        return "UINTEGER"
    
    def visit_ubigint(self, type_, **kw):
        return "UBIGINT"

    # Money
    def visit_money(self, type_, **kw):
        return "NUMERIC(19,2)"
    
    def visit_currency(self, type_, **kw):
        return "CURRENCY"

    # Legacy Numeric
    def visit_numericsa(self, type_, **kw):
        if hasattr(type_, 'precision') and hasattr(type_, 'scale'):
            return f"NUMERICSA({type_.precision},{type_.scale})"
        return "NUMERICSA"
    
    def visit_numericslb(self, type_, **kw):
        return "NUMERICSLB"
    
    def visit_numericsls(self, type_, **kw):
        return "NUMERICSLS"
    
    def visit_numericstb(self, type_, **kw):
        return "NUMERICSTB"
    
    def visit_numericsts(self, type_, **kw):
        return "NUMERICSTS"

    # Floating Point
    def visit_bfloat4(self, type_, **kw):
        return "BFLOAT4"
    
    def visit_bfloat8(self, type_, **kw):
        return "BFLOAT8"
    
    def visit_real(self, type_, **kw):
        return "REAL"
    
    def visit_double(self, type_, **kw):
        return "DOUBLE"

    # Auto-increment
    def visit_autoincrement(self, type_, **kw):
        return "AUTOINCREMENT"

    # Native Zen Identity Types
    def visit_smallidentity(self, type_, **kw):
        return "SMALLIDENTITY"
    
    def visit_identity(self, type_, **kw):
        return "IDENTITY"
    
    def visit_bigidentity(self, type_, **kw):
        return "BIGIDENTITY"

    def visit_autotimestamp(self, type_, **kw):
        return "DATETIME DEFAULT NOW()"

    def visit_text(self, type_, **kw):
        """Compile SQLAlchemy TEXT to Zen's LONGVARCHAR type"""
        return "LONGVARCHAR"

    def visit_json(self, type_, **kw):
        """Compile JSON type to Zen's LONGVARCHAR (no native JSON support)"""
        return "LONGVARCHAR"

    def visit_JSON(self, type_, **kw):
        """Compile SQLAlchemy JSON to Zen's LONGVARCHAR"""
        return "LONGVARCHAR"

    def visit_zen_binary(self, type_, **kw):
        """Compile ZenBinary to Zen's LONGVARBINARY type"""
        return "LONGVARBINARY"

    def visit_LARGEBINARY(self, type_, **kw):
        """Compile SQLAlchemy LargeBinary to Zen's LONGVARBINARY type"""
        return "LONGVARBINARY"

    def visit_nvarchar(self, type_, **kw):
        """Compile ZenNVarchar to Zen's NVARCHAR type"""
        if type_.length is not None:
            return f"NVARCHAR({type_.length})"
        return "NVARCHAR"
    
    def visit_nlongvarchar(self, type_, **kw):
        """Compile ZenNLongVarchar to Zen's NLONGVARCHAR type"""
        return "NLONGVARCHAR"
    
    def visit_zenunicode(self, type_, **kw):
        """Compile ZenUnicode to Zen's NVARCHAR type"""
        if type_.length is not None:
            return f"NVARCHAR({type_.length})"
        return "NVARCHAR"

    def visit_STRING(self, type_, **kw):
        """Override base STRING to prevent auto-COLLATE emission.

        The base SQLAlchemy type compiler automatically adds COLLATE clauses
        when processing String types. We disable this and handle COLLATE
        separately in get_column_specification to avoid duplication.
        """
        if type_.length is not None:
            return f"VARCHAR({type_.length})"
        return "VARCHAR"

    def visit_VARCHAR(self, type_, **kw):
        """Override base VARCHAR to prevent auto-COLLATE emission."""
        if type_.length is not None:
            return f"VARCHAR({type_.length})"
        return "VARCHAR"

    def visit_user_defined(self, type_, **kw):
        """Handle user-defined types with defensive type_expression access"""
        # Call the type's get_col_spec method if it exists
        if hasattr(type_, 'get_col_spec'):
            return type_.get_col_spec(**kw)
        # Fallback: try to get name from type_ object itself
        elif hasattr(type_, 'name'):
            return f"FOOB {type_.name}"
        else:
            return "FOOB"  # Final fallback string
    
    # Fallback to parent for unhandled types
    def visit_generic(self, type_, **kw):
        return super().visit_generic(type_, **kw)

# ============== COMPILER REGISTRATIONS ==============
@compiles(ZenBit, 'zen')
def compile_zen_bit(type_, compiler, **kw):
    return "BIT"

@compiles(ZenCurrency, 'zen')
def compile_zen_currency(type_, compiler, **kw):
    return "CURRENCY"

@compiles(ZenLegacyNumeric, 'zen')
def compile_zen_legacy_numeric(type_, compiler, **kw):
    if hasattr(type_, 'precision') and hasattr(type_, 'scale'):
        return f"NUMERIC({type_.precision},{type_.scale})"
    return "NUMERIC"

@compiles(ZenSmallIdentity, 'zen')
def compile_zen_smallidentity(type_, compiler, **kw):
    return "SMALLIDENTITY"

@compiles(ZenIdentity, 'zen')
def compile_zen_identity(type_, compiler, **kw):
    return "IDENTITY"

@compiles(ZenBigIdentity, 'zen')
def compile_zen_bigidentity(type_, compiler, **kw):
    return "BIGIDENTITY" 

@compiles(ZenTinyInt, 'zen')
def compile_zen_tinyint(type_, compiler, **kw):
    return "TINYINT" 

@compiles(ZenUTinyInt, 'zen')
def compile_zen_utinyint(type_, compiler, **kw):
    return "UTINYINT"

@compiles(ZenUSmallInt, 'zen')
def compile_zen_usmallint(type_, compiler, **kw):
    return "USMALLINT"

@compiles(ZenUInteger, 'zen')
def compile_zen_uinteger(type_, compiler, **kw):
    return "UINTEGER"

@compiles(ZenUBigInt, 'zen')
def compile_zen_ubigint(type_, compiler, **kw):
    return "UBIGINT"

@compiles(ZenAutoTimestamp, 'zen')
def compile_zen_autotimestamp(type_, compiler, **kw):
    return "TIMESTAMP DEFAULT NOW()" 

class ZenNVarchar(TypeDecorator):
    impl = Unicode
    __visit_name__ = 'nvarchar'
    cache_ok = True
    
    def __init__(self, length=None):
        super().__init__()
        self.length = length
    
    def load_dialect_impl(self, dialect):
        """Map to Unicode for SQLAlchemy compatibility"""
        return Unicode(self.length)
    
    def copy(self, **kw):
        return type(self)(length=self.length)

class ZenNLongVarchar(TypeDecorator):
    impl = UnicodeText
    __visit_name__ = 'nlongvarchar'
    cache_ok = True

class ZenUnicode(Unicode):
    __visit_name__ = 'zenunicode'
    def __init__(self, length=None, collation=None, **kwargs):
        super().__init__(length=length, collation=collation, **kwargs)
    def dialect_impl(self, dialect):
        # Always use NVARCHAR for Zen
        return ZenNVarchar(self.length)
    def _compiler_dispatch(self, visitor, **kw):
        # Never emit a default COLLATE, and ensure only one COLLATE is ever emitted
        # This disables parent Unicode's collation emission
        return visitor.visit_zenunicode(self, **kw)

# ============== DATE/TIME TYPE HANDLING ==============

class ZenDate(sa_types.TypeDecorator):
    """Zen Date type with proper parameter binding"""
    impl = sa_types.Date
    __visit_name__ = 'date'
    cache_ok = True
    inherit_cache = True
    
    def process_bind_param(self, value, dialect):
        """Convert Python date to Zen date format"""
        if value is None:
            return None
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)
    
    def process_result_value(self, value, dialect):
        """Convert Zen date to Python date"""
        if value is None:
            return None
        # Handle empty strings and zero dates as None
        if isinstance(value, str):
            if value.strip() == '' or value == '0000-00-00':
                return None
        if hasattr(value, 'date'):
            return value.date()
        return value

class ZenDateTime(sa_types.TypeDecorator):
    """Zen DateTime type with proper parameter binding"""
    impl = sa_types.DateTime
    __visit_name__ = 'datetime'
    cache_ok = True
    inherit_cache = True
    
    def process_bind_param(self, value, dialect):
        """Convert Python datetime to Zen datetime format"""
        if value is None:
            return None
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)
    
    def process_result_value(self, value, dialect):
        """Convert Zen datetime to Python datetime"""
        if value is None:
            return None
        return value

class ZenTime(sa_types.TypeDecorator):
    """Zen Time type with proper parameter binding"""
    impl = sa_types.Time
    __visit_name__ = 'time'
    cache_ok = True
    inherit_cache = True
    
    def process_bind_param(self, value, dialect):
        """Convert Python time to Zen time format"""
        if value is None:
            return None
        if hasattr(value, 'strftime'):
            return value.strftime('%H:%M:%S')
        return str(value)
    
    def process_result_value(self, value, dialect):
        """Convert Zen time to Python time"""
        if value is None:
            return None
        return value 

# ============== ADD UNICODE TYPES TO TYPE MAP ==============
# Add Unicode types to the type map after all classes are defined
_type_map.update({
    # Unicode Types
    'NVARCHAR': ZenNVarchar,
    'NLONGVARCHAR': ZenNLongVarchar,
    'Unicode': ZenUnicode,
    'UnicodeText': ZenNLongVarchar,
    # Date/Time Types
    'Date': ZenDate,
    'DateTime': ZenDateTime,
    'Time': ZenTime,
})

# ============== UNICODE TYPE COMPILER REGISTRATIONS ==============
@compiles(ZenNVarchar, 'zen')
def compile_zen_nvarchar(type_, compiler, **kw):
    if type_.length is not None:
        return f"NVARCHAR({type_.length})"
    return "NVARCHAR"

@compiles(ZenNLongVarchar, 'zen')
def compile_zen_nlongvarchar(type_, compiler, **kw):
    return "NLONGVARCHAR"

@compiles(ZenUnicode, 'zen')
def compile_zen_unicode(type_, compiler, **kw):
    if type_.length is not None:
        return f"NVARCHAR({type_.length})"
    return "NVARCHAR"

# ============== DATE/TIME TYPE COMPILER REGISTRATIONS ==============
@compiles(ZenDate, 'zen')
def compile_zen_date(type_, compiler, **kw):
    return "DATE"

@compiles(ZenDateTime, 'zen')
def compile_zen_datetime(type_, compiler, **kw):
    return "TIMESTAMP"

@compiles(ZenTime, 'zen')
def compile_zen_time(type_, compiler, **kw):
    return "TIME"

# ============== BINARY TYPE DEFINITIONS ==============

class ZenBinary(sa_types.LargeBinary):
    """
    Zen LONGVARBINARY type for binary data.

    Handles binary data storage in Zen database using LONGVARBINARY.
    Properly converts between Python bytes and Zen binary format.
    """
    __visit_name__ = 'zen_binary'

    def bind_processor(self, dialect):
        """Convert Python bytes to Zen binary format"""
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                # If we get a string, encode it to bytes
                return value.encode('latin-1')
            if isinstance(value, bytes):
                return value
            # For other types, try to convert to bytes
            return bytes(str(value), 'latin-1')
        return process

    def result_processor(self, dialect, coltype):
        """Convert Zen binary data back to Python bytes"""
        def process(value):
            if value is None:
                return None
            if isinstance(value, bytes):
                return value
            if isinstance(value, str):
                # Zen returns binary data as string - we need to decode it properly
                # The string contains the actual binary data, so we need to encode it as latin-1
                # to preserve the original byte values
                try:
                    return value.encode('latin-1')
                except UnicodeEncodeError:
                    # If latin-1 encoding fails, the string might contain characters outside latin-1 range
                    # This happens when Zen interprets binary data as UTF-8 text
                    # We need to convert the UTF-8 characters back to the original bytes
                    try:
                        # The string contains UTF-8 characters that represent the original binary data
                        # We need to decode these characters to get the original bytes
                        # First, encode the string as UTF-8 to get the bytes
                        utf8_bytes = value.encode('utf-8')
                        # Then, decode these bytes as latin-1 to get the original binary data
                        # This works because the UTF-8 bytes represent the original binary data
                        return utf8_bytes.decode('latin-1').encode('latin-1')
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        # As last resort, just encode as utf-8
                        return value.encode('utf-8')
            # Handle other cases
            return bytes(str(value), 'latin-1')
        return process

@compiles(ZenBinary, 'zen')
def compile_zen_binary(type_, compiler, **kw):
    return "LONGVARBINARY"

# ============== JSON TYPE DEFINITION ==============

import json as _json

class ZenJSON(TypeDecorator):
    """
    Zen JSON type stored as LONGVARCHAR.

    Since Zen doesn't have a native JSON type, this stores JSON data
    as text in LONGVARCHAR and handles serialization/deserialization
    automatically.

    Usage:
        from sqlalchemy_zen.types import ZenJSON

        class MyModel(Base):
            data = Column(ZenJSON)
            config = Column(ZenJSON(none_as_null=True))

    The type automatically:
    - Serializes Python dicts/lists to JSON strings on INSERT/UPDATE
    - Deserializes JSON strings back to Python objects on SELECT
    - Handles None values (stores as NULL or 'null' based on none_as_null)
    """
    impl = sa_types.Text  # Maps to LONGVARCHAR in Zen
    __visit_name__ = 'json'
    cache_ok = True

    def __init__(self, none_as_null=False):
        """
        Initialize ZenJSON type.

        Args:
            none_as_null: If True, Python None is stored as SQL NULL.
                         If False (default), Python None is stored as JSON 'null'.
        """
        super().__init__()
        self.none_as_null = none_as_null

    def process_bind_param(self, value, dialect):
        """Convert Python object to JSON string for storage"""
        if value is None:
            return None if self.none_as_null else 'null'
        try:
            return _json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot serialize value to JSON: {e}")

    def process_result_value(self, value, dialect):
        """Convert JSON string from database to Python object"""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            # Already deserialized (shouldn't happen, but handle it)
            return value
        try:
            return _json.loads(value)
        except (TypeError, ValueError):
            # If it's not valid JSON, return as-is
            return value

    def copy(self, **kw):
        return type(self)(none_as_null=self.none_as_null)

# Add JSON to type map
_type_map['JSON'] = ZenJSON

# Compiler registration for ZenJSON
@compiles(ZenJSON, 'zen')
def compile_zen_json(type_, compiler, **kw):
    return "LONGVARCHAR"