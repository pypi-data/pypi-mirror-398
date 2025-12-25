# Path: usekit.classes.data.base.post.sub.parser_sql_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Helper functions for SQL parser - variable binding and multi-dialect support
# Features:
#   - SQL style detection: USEKIT($), SQLite(?), Oracle(:), MSSQL(@), psycopg(%)
#   - Variable parsing: declarative string format ("$name: John | $age: 20")
#   - Type inference: auto-detect int/float/bool/None/str
#   - Dialect conversion: bidirectional conversion between SQL dialects
#   - Variable replacement: safe SQL injection prevention
# -----------------------------------------------------------------------------------------------

import re
from typing import Any, Dict, List, Optional, Tuple, Union


# ===============================================================================
# Constants
# ===============================================================================

SQL_STYLES = {
    "usekit": "$",      # $variable_name
    "sqlite": "?",      # positional ?
    "oracle": ":",      # :variable_name
    "mssql": "@",       # @variable_name
    "psycopg": "%",     # %(variable_name)s or %s
}

# Regex patterns for variable detection
PATTERN_USEKIT = re.compile(r'\$(\w+)')           # $name
PATTERN_ORACLE = re.compile(r':(\w+)')            # :name
PATTERN_MSSQL = re.compile(r'@(\w+)')             # @name
PATTERN_PSYCOPG_NAMED = re.compile(r'%\((\w+)\)s')  # %(name)s
PATTERN_SQLITE = re.compile(r'\?')                # ?


# ===============================================================================
# SQL Style Detection
# ===============================================================================

def _detect_sql_style(sql: str) -> str:
    """
    Auto-detect SQL variable placeholder style.
    
    Priority order (first match wins):
    1. psycopg: %(name)s
    2. usekit: $variable (if no @ present or @ after SELECT)
    3. oracle: :variable (if : not in time/schema context)
    4. mssql: @variable (if @ not in email context)
    5. sqlite: ? (positional)
    6. default: usekit
    
    Args:
        sql: SQL string to analyze
        
    Returns:
        Style name ('usekit', 'sqlite', 'oracle', 'mssql', 'psycopg')
    """
    
    # Remove comments and strings for accurate detection
    sql_clean = _remove_sql_noise(sql)
    
    # 1. psycopg named parameters (most specific)
    if PATTERN_PSYCOPG_NAMED.search(sql_clean):
        return 'psycopg'
    
    # 2. USEKIT style ($variable)
    if '$' in sql_clean:
        # Check if it's actually $variable pattern
        if PATTERN_USEKIT.search(sql_clean):
            return 'usekit'
    
    # 3. Oracle style (:variable)
    if ':' in sql_clean:
        # Avoid false positives from schema.table or time formats
        if PATTERN_ORACLE.search(sql_clean):
            # Check if it's not a schema qualifier
            if not re.search(r'\w+:\w+', sql_clean) or re.search(r'\s:\w+', sql_clean):
                return 'oracle'
    
    # 4. MSSQL style (@variable)
    if '@' in sql_clean:
        # Avoid false positives from email addresses
        if PATTERN_MSSQL.search(sql_clean):
            # Check if it's not an email
            if not re.search(r'\w+@\w+\.\w+', sql_clean):
                return 'mssql'
    
    # 5. SQLite style (?)
    if '?' in sql_clean:
        return 'sqlite'
    
    # Default to USEKIT
    return 'usekit'


def _remove_sql_noise(sql: str) -> str:
    """
    Remove SQL comments and string literals for cleaner detection.
    
    Args:
        sql: Original SQL string
        
    Returns:
        Cleaned SQL string
    """
    # Remove single-line comments (-- comment)
    sql = re.sub(r'--[^\n]*', '', sql)
    
    # Remove multi-line comments (/* comment */)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    
    # Remove single-quoted strings ('string')
    sql = re.sub(r"'(?:[^'\\]|\\.)*'", "''", sql)
    
    # Remove double-quoted identifiers ("identifier")
    sql = re.sub(r'"(?:[^"\\]|\\.)*"', '""', sql)
    
    return sql


# ===============================================================================
# Parameter String Parsing
# ===============================================================================

def _parse_param_string(param_str: str) -> Dict[str, Any]:
    """
    Parse declarative parameter string to dict.
    
    Supports formats:
    - Pipe-separated: "$name: John | $age: 20 | $active: True"
    - Multi-line: 
        '''
        $name: John
        $age: 20
        $active: True
        '''
    
    Args:
        param_str: Parameter string
        
    Returns:
        Dict of variable_name -> value
    """
    
    if not param_str or not isinstance(param_str, str):
        return {}
    
    result = {}
    
    # Detect format: pipe-separated vs multi-line
    if '|' in param_str:
        # Pipe-separated format
        items = param_str.split('|')
    else:
        # Multi-line format
        items = param_str.strip().split('\n')
    
    for item in items:
        item = item.strip()
        if not item or ':' not in item:
            continue
        
        # Split on first colon only
        parts = item.split(':', 1)
        if len(parts) != 2:
            continue
        
        key, value = parts
        key = key.strip().lstrip('$')  # Remove $ prefix if present
        value = value.strip()
        
        if not key:
            continue
        
        # Type inference
        result[key] = _infer_type(value)
    
    return result


def _infer_type(value: str) -> Any:
    """
    Auto-detect and convert value type.
    
    Conversion priority:
    1. None/NULL
    2. Boolean (True/False)
    3. Integer
    4. Float
    5. String (with quote removal)
    
    Args:
        value: String value to convert
        
    Returns:
        Converted value
    """
    
    value = value.strip()
    
    # None/NULL
    if value.lower() in ('none', 'null'):
        return None
    
    # Boolean
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    
    # Integer (including negative)
    if value.lstrip('-').isdigit():
        return int(value)
    
    # Float
    try:
        if '.' in value:
            return float(value)
    except ValueError:
        pass
    
    # String - remove quotes if present
    if len(value) >= 2:
        if (value[0] == value[-1]) and value[0] in ('"', "'"):
            return value[1:-1]
    
    return value


# ===============================================================================
# Dialect Conversion
# ===============================================================================

def _convert_to_usekit(sql: str, style: str) -> str:
    """
    Convert various SQL dialects to USEKIT format ($variable).
    
    Args:
        sql: Original SQL string
        style: Source style ('sqlite', 'oracle', 'mssql', 'psycopg')
        
    Returns:
        SQL in USEKIT format
    """
    
    if style == 'usekit':
        return sql
    
    elif style == 'sqlite':
        # ? → $1, $2, $3 (numbered positional)
        counter = 1
        result = []
        i = 0
        while i < len(sql):
            if sql[i] == '?':
                result.append(f'${counter}')
                counter += 1
            else:
                result.append(sql[i])
            i += 1
        return ''.join(result)
    
    elif style == 'oracle':
        # :variable → $variable
        return PATTERN_ORACLE.sub(r'$\1', sql)
    
    elif style == 'mssql':
        # @variable → $variable
        return PATTERN_MSSQL.sub(r'$\1', sql)
    
    elif style == 'psycopg':
        # %(variable)s → $variable
        return PATTERN_PSYCOPG_NAMED.sub(r'$\1', sql)
    
    return sql


def _convert_from_usekit(
    sql: str,
    param_dict: Dict[str, Any],
    target_style: str = 'sqlite'
) -> Tuple[str, Union[tuple, dict]]:
    """
    Convert USEKIT format to target SQL dialect.
    
    Args:
        sql: SQL in USEKIT format ($variable)
        param_dict: Variable values
        target_style: Target dialect ('sqlite', 'oracle', 'mssql', 'psycopg')
        
    Returns:
        (converted_sql, params_in_target_format)
    """
    
    if target_style == 'usekit':
        return sql, param_dict
    
    # Find all $variables in order
    variables = PATTERN_USEKIT.findall(sql)
    
    if target_style == 'sqlite':
        # $variable → ?
        # Build ordered tuple
        result_sql = PATTERN_USEKIT.sub('?', sql)
        param_tuple = tuple(param_dict.get(var) for var in variables)
        return result_sql, param_tuple
    
    elif target_style == 'oracle':
        # $variable → :variable
        result_sql = PATTERN_USEKIT.sub(r':\1', sql)
        return result_sql, param_dict
    
    elif target_style == 'mssql':
        # $variable → @variable
        result_sql = PATTERN_USEKIT.sub(r'@\1', sql)
        return result_sql, param_dict
    
    elif target_style == 'psycopg':
        # $variable → %(variable)s
        result_sql = PATTERN_USEKIT.sub(r'%(\1)s', sql)
        return result_sql, param_dict
    
    return sql, param_dict


# ===============================================================================
# Variable Replacement (Direct substitution - use with caution)
# ===============================================================================

def _replace_variables(
    sql: str,
    param_dict: Dict[str, Any],
    quote_strings: bool = True
) -> str:
    """
    Replace $variables with actual values in SQL string.
    
    WARNING: This creates SQL injection risk. Use only for:
    - Read-only operations
    - Trusted input
    - Display/logging purposes
    
    For actual execution, prefer parameterized queries via _convert_from_usekit.
    
    Args:
        sql: SQL with $variables
        param_dict: Variable values
        quote_strings: Auto-quote string values
        
    Returns:
        SQL with values substituted
    """
    
    def replace_match(match):
        var_name = match.group(1)
        
        if var_name not in param_dict:
            # Leave unchanged if variable not found
            return match.group(0)
        
        value = param_dict[var_name]
        
        # Convert to SQL literal
        return _to_sql_literal(value, quote_strings)
    
    return PATTERN_USEKIT.sub(replace_match, sql)


def _to_sql_literal(value: Any, quote_strings: bool = True) -> str:
    """
    Convert Python value to SQL literal string.
    
    Args:
        value: Python value
        quote_strings: Add quotes around strings
        
    Returns:
        SQL literal representation
    """
    
    if value is None:
        return 'NULL'
    
    if isinstance(value, bool):
        # SQLite uses 0/1 for boolean
        return '1' if value else '0'
    
    if isinstance(value, (int, float)):
        return str(value)
    
    if isinstance(value, str):
        if quote_strings:
            # Escape single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        return value
    
    # Fallback: convert to string
    return str(value)


# ===============================================================================
# Parameter Merging
# ===============================================================================

def _merge_params(*args, **kwargs) -> Dict[str, Any]:
    """
    Merge positional and keyword parameters into unified dict.
    
    Handles:
    - Positional param strings: "$name: John | $age: 20"
    - Keyword arguments: name="John", age=20
    - Dict unpacking: **{"name": "John", "age": 20}
    
    Priority: kwargs > positional param strings > earlier args
    
    Args:
        *args: Positional arguments (may include param strings)
        **kwargs: Keyword arguments
        
    Returns:
        Merged parameter dict
    """
    
    result = {}
    
    # Process positional args
    for arg in args:
        if isinstance(arg, str):
            # Try to parse as param string
            parsed = _parse_param_string(arg)
            if parsed:
                result.update(parsed)
        elif isinstance(arg, dict):
            # Direct dict merge
            result.update(arg)
    
    # Kwargs have highest priority
    result.update(kwargs)
    
    return result


# ===============================================================================
# Quote Handling
# ===============================================================================

def _handle_quoted_variables(sql: str) -> str:
    """
    Convert '$variable' (with quotes) to $variable (without quotes).
    
    This allows users to write:
        WHERE name = '$name'
    Instead of:
        WHERE name = $name
    
    Args:
        sql: SQL string
        
    Returns:
        SQL with quoted variables unquoted
    """
    
    # Replace '$variable' with $variable
    # Handle both single and double quotes
    sql = re.sub(r"'(\$\w+)'", r'\1', sql)
    sql = re.sub(r'"(\$\w+)"', r'\1', sql)
    
    return sql


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "SQL_STYLES",
    "_detect_sql_style",
    "_remove_sql_noise",
    "_parse_param_string",
    "_infer_type",
    "_convert_to_usekit",
    "_convert_from_usekit",
    "_replace_variables",
    "_to_sql_literal",
    "_merge_params",
    "_handle_quoted_variables",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
