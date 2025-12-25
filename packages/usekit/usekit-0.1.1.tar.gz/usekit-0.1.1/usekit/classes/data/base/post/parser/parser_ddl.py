# Path: usekit.classes.data.base.post.parser.parser_ddl.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Production-ready SQL DDL/DML parser and generator
# Pattern: Small → Big (data → name → dir → options)
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import tempfile
import os
from typing import Any, Union, Optional, Dict, List
import re

# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────

def _atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Safe write: write to temp file then atomically replace target."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), encoding=encoding
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _ensure_path(file: Union[str, Path]) -> Path:
    """Convert to Path object if needed."""
    return file if isinstance(file, Path) else Path(file)


def _wrap_if_needed(data: Any, wrap: bool) -> Any:
    """Auto-wrap simple values into dict if needed."""
    if not wrap:
        return data
    if not isinstance(data, dict):
        return {"tables": [data] if isinstance(data, list) else data}
    return data


def _escape_sql_value(value: Any) -> str:
    """Escape value for SQL insertion."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _parse_sql_type(value: Any) -> str:
    """Infer SQL type from Python value."""
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    if isinstance(value, str):
        if len(value) > 255:
            return "TEXT"
        return f"VARCHAR({max(len(value) * 2, 50)})"
    return "TEXT"


def _normalize_column_name(name: str) -> str:
    """Normalize column name for SQL."""
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name.lower()


def _extract_table_name(data: Any) -> Optional[str]:
    """Extract table name from data structure if present."""
    if isinstance(data, dict):
        # Check for common table name keys
        for key in ['table', 'table_name', 'name', '_table']:
            if key in data:
                return str(data[key])
    return None


# ───────────────────────────────────────────────────────────────
# SQL Statement Generators
# ───────────────────────────────────────────────────────────────

def _generate_create_table(
    table_name: str,
    columns: Dict[str, str],
    primary_key: Optional[str] = None,
    if_not_exists: bool = True
) -> str:
    """Generate CREATE TABLE statement."""
    exists_clause = "IF NOT EXISTS " if if_not_exists else ""
    
    col_defs = []
    for col_name, col_type in columns.items():
        col_def = f"    {col_name} {col_type}"
        if col_name == primary_key:
            col_def += " PRIMARY KEY"
        col_defs.append(col_def)
    
    columns_sql = ",\n".join(col_defs)
    
    return f"""CREATE TABLE {exists_clause}{table_name} (
{columns_sql}
);"""


def _generate_insert(
    table_name: str,
    data: Union[Dict, List[Dict]],
    batch: bool = True
) -> str:
    """Generate INSERT statement(s)."""
    if not isinstance(data, list):
        data = [data]
    
    if not data:
        return ""
    
    columns = list(data[0].keys())
    columns_sql = ", ".join(columns)
    
    if batch:
        values_list = []
        for record in data:
            values = [_escape_sql_value(record.get(col)) for col in columns]
            values_sql = ", ".join(values)
            values_list.append(f"({values_sql})")
        
        all_values = ",\n    ".join(values_list)
        return f"""INSERT INTO {table_name} ({columns_sql})
VALUES
    {all_values};"""
    else:
        statements = []
        for record in data:
            values = [_escape_sql_value(record.get(col)) for col in columns]
            values_sql = ", ".join(values)
            statements.append(
                f"INSERT INTO {table_name} ({columns_sql}) VALUES ({values_sql});"
            )
        return "\n".join(statements)


def _infer_schema_from_data(data: List[Dict]) -> Dict[str, str]:
    """Infer SQL schema from data records."""
    if not data:
        return {}
    
    schema = {}
    all_keys = set()
    for record in data:
        all_keys.update(record.keys())
    
    for key in all_keys:
        sample_value = None
        for record in data:
            if key in record and record[key] is not None:
                sample_value = record[key]
                break
        
        if sample_value is not None:
            schema[_normalize_column_name(key)] = _parse_sql_type(sample_value)
        else:
            schema[_normalize_column_name(key)] = "TEXT"
    
    return schema


# ───────────────────────────────────────────────────────────────
# Load / Loads (Parse SQL statements)
# ───────────────────────────────────────────────────────────────

def load(
    file,
    encoding: str = "utf-8",
    **kwargs
) -> Dict[str, Any]:
    """
    Read SQL from a file.
    
    Returns:
        {
            "statements": [...],  # List of SQL statements
            "raw": "...",         # Raw SQL text
            "count": n            # Statement count
        }
    """
    if isinstance(file, (str, Path)):
        path = _ensure_path(file)
        with path.open("r", encoding=encoding) as f:
            text = f.read()
    else:
        text = file.read()
    
    return loads(text, **kwargs)


def loads(text: str, **kwargs) -> Dict[str, Any]:
    """Parse SQL from string."""
    lines = []
    for line in text.splitlines():
        if '--' in line:
            line = line[:line.index('--')]
        line = line.strip()
        if line:
            lines.append(line)
    
    cleaned = ' '.join(lines)
    statements = [s.strip() for s in cleaned.split(';') if s.strip()]
    
    return {
        "statements": statements,
        "raw": text,
        "count": len(statements)
    }


# ───────────────────────────────────────────────────────────────
# Dump / Dumps (Generate SQL)
# Pattern: data → file → options
# ───────────────────────────────────────────────────────────────

def dump(
    data: Any,
    file=None,
    *,
    # Options (sorted by importance)
    mode: str = "auto",           # 'auto' | 'create' | 'insert' | 'full'
    primary_key: Optional[str] = None,
    batch_insert: bool = True,
    if_not_exists: bool = True,
    # File handling
    encoding: str = "utf-8",
    wrap: bool = False,
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    **kwargs
) -> Optional[str]:
    """
    Write SQL to file or return as string.
    
    Pattern: Small → Big
        data      (smallest - the content)
        file      (medium - where to save, optional for dumps)
        options   (largest - how to process)
    
    Usage:
        # Dumps mode (no file)
        sql_str = dump(data)
        
        # File mode
        dump(data, "users.sql")
        dump(data, "users.sql", mode="full", primary_key="id")
    
    Modes:
        'auto'   : Detect from data structure
        'create' : Generate CREATE TABLE only
        'insert' : Generate INSERT statements only
        'full'   : Generate both CREATE TABLE and INSERT
    
    Data Formats:
        # List of records (auto-infer schema)
        [{"id": 1, "name": "Alice"}, ...]
        
        # Dict with table name
        {"table": "users", "records": [...]}
        
        # Dict with explicit schema
        {"schema": {"id": "INTEGER"}, "records": [...]}
    
    Args:
        data: Data to convert to SQL (smallest unit)
        file: File path or None for dumps (medium unit)
        mode: SQL generation mode
        primary_key: Primary key column name
        batch_insert: Use multi-row INSERT
        if_not_exists: Add IF NOT EXISTS to CREATE TABLE
        encoding: File encoding
        wrap: Auto-convert to dict if needed
        overwrite: Allow overwriting existing file
        safe: Use atomic write
        append: Append to existing file
        
    Returns:
        SQL string if file is None (dumps mode), otherwise None
    """
    data = _wrap_if_needed(data, wrap)
    
    # Generate SQL
    sql = dumps(
        data,
        mode=mode,
        primary_key=primary_key,
        if_not_exists=if_not_exists,
        batch_insert=batch_insert,
        **kwargs
    )
    
    # Dumps mode - return string
    if file is None:
        return sql
    
    # File mode - write to file
    path_obj = None
    if isinstance(file, (str, Path)):
        path_obj = _ensure_path(file)
    
    # Append mode
    if append:
        if path_obj:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("a", encoding=encoding) as f:
                f.write("\n\n")
                f.write(sql)
        else:
            file.write("\n\n")
            file.write(sql)
        return None
    
    # Normal write mode
    if path_obj:
        if path_obj.exists() and not overwrite:
            raise FileExistsError(
                f"[sql.dump] Target exists and overwrite=False: {path_obj}"
            )
        
        if safe:
            _atomic_write_text(path_obj, sql, encoding=encoding)
        else:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding=encoding) as f:
                f.write(sql)
        return None
    
    # File-like object
    file.write(sql)
    return None


def dumps(
    data: Any,
    *,
    mode: str = "auto",
    primary_key: Optional[str] = None,
    if_not_exists: bool = True,
    batch_insert: bool = True,
    wrap: bool = False,
    **kwargs
) -> str:
    """
    Serialize to SQL string.
    
    Pattern: Just data → string (no file involved)
    
    Data Formats:
        # Raw SQL string (pass-through)
        "CREATE TABLE users (id INT, name TEXT);"
        
        # List of records (auto-infer schema and table name)
        [{"id": 1, "name": "Alice"}, ...]
        → Table name: "data_table"
        
        # Dict with table name
        {"table": "users", "records": [...]}
        
        # Dict with explicit schema
        {
            "table": "users",
            "schema": {"id": "INTEGER", "name": "VARCHAR(50)"},
            "records": [{"id": 1, "name": "Alice"}]
        }
    
    Args:
        data: Data to convert to SQL
        mode: SQL generation mode
        primary_key: Primary key column name
        if_not_exists: Add IF NOT EXISTS
        batch_insert: Use multi-row INSERT
        wrap: Auto-convert to dict
        
    Returns:
        SQL string
    """
    # Handle raw SQL string pass-through
    if isinstance(data, str):
        return data
    
    data = _wrap_if_needed(data, wrap)
    
    statements = []
    schema = None
    records = None
    table_name = "data_table"  # Default
    
    # Extract table name and data
    if isinstance(data, list):
        records = data
        mode = mode if mode != "auto" else "full"
    elif isinstance(data, dict):
        # Extract table name
        extracted_name = _extract_table_name(data)
        if extracted_name:
            table_name = extracted_name
        
        # Extract schema and records
        if "schema" in data:
            schema = data["schema"]
        if "records" in data:
            records = data["records"]
        
        # Auto-detect mode
        if mode == "auto":
            if schema and records:
                mode = "full"
            elif schema:
                mode = "create"
            elif records:
                mode = "full"
            else:
                mode = "create"
    else:
        raise ValueError(f"[sql.dumps] Unsupported data type: {type(data)}")
    
    # Infer schema if not provided
    if records and not schema:
        schema = _infer_schema_from_data(records)
    
    # Generate CREATE TABLE
    if mode in ("create", "full") and schema:
        create_sql = _generate_create_table(
            table_name, schema, primary_key, if_not_exists
        )
        statements.append(create_sql)
    
    # Generate INSERT statements
    if mode in ("insert", "full") and records:
        insert_sql = _generate_insert(table_name, records, batch_insert)
        statements.append(insert_sql)
    
    return "\n\n".join(statements)


# ───────────────────────────────────────────────────────────────
# Helper Functions (following Small → Big pattern)
# ───────────────────────────────────────────────────────────────

def create_table(
    schema: Dict[str, str],
    table: str = "data_table",
    *,
    primary_key: Optional[str] = None,
    if_not_exists: bool = True
) -> str:
    """
    Generate CREATE TABLE statement.
    
    Pattern: schema (small) → table name (big) → options
    
    Example:
        sql = create_table(
            {"id": "INTEGER", "name": "VARCHAR(100)"},
            "users",
            primary_key="id"
        )
    """
    return _generate_create_table(table, schema, primary_key, if_not_exists)


def insert_records(
    records: List[Dict],
    table: str = "data_table",
    *,
    batch: bool = True
) -> str:
    """
    Generate INSERT statement(s).
    
    Pattern: records (small) → table name (big) → options
    
    Example:
        sql = insert_records(
            [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            "users"
        )
    """
    return _generate_insert(table, records, batch)


# ───────────────────────────────────────────────────────────────
# Test helper
# ───────────────────────────────────────────────────────────────

def _test(base="sample.sql"):
    """Test SQL parser functionality."""
    print("=" * 60)
    print("SQL DDL/DML Parser Test - Small → Big Pattern")
    print("=" * 60)
    
    # Sample data
    users = [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "active": True},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "active": True},
        {"id": 3, "name": "Charlie", "email": "charlie@example.com", "active": False}
    ]
    
    # Test 1: Dumps mode (no file)
    print("\n[TEST 1] Dumps mode (data only):")
    sql_str = dump(users, mode="full", primary_key="id")
    print(sql_str[:200] + "...")
    
    # Test 2: File mode with table name in data
    print("\n[TEST 2] File mode with table name in data:")
    data_with_table = {
        "table": "users",
        "records": users
    }
    dump(data_with_table, base, mode="full", primary_key="id")
    print(f"[SQL] Generated full SQL: {base}")
    print(Path(base).read_text()[:200] + "...")
    
    # Test 3: Helper - CREATE TABLE (schema first)
    print("\n[TEST 3] CREATE TABLE helper (schema → table):")
    schema = {
        "id": "INTEGER",
        "name": "VARCHAR(100)",
        "email": "VARCHAR(255)",
        "active": "BOOLEAN"
    }
    create_sql = create_table(schema, "users", primary_key="id")
    print(create_sql)
    
    # Test 4: Helper - INSERT (records first)
    print("\n[TEST 4] INSERT helper (records → table):")
    insert_sql = insert_records(users[:2], "users")
    print(insert_sql)
    
    # Test 5: Parse SQL file
    print("\n[TEST 5] Parse SQL file:")
    parsed = load(base)
    print(f"[SQL] Parsed {parsed['count']} statements")
    for i, stmt in enumerate(parsed["statements"], 1):
        print(f"  Statement {i}: {stmt[:60]}...")
    
    print("\n" + "=" * 60)
    print("Pattern verified: Small → Big ✓")
    print("  data (small) → file (medium) → options (big)")
    print("=" * 60)


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------