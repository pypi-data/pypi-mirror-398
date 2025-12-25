# Path: usekit.classes.exec.base.post.act.sql.ebp_exec_sql.py
# -----------------------------------------------------------------------------------------------
#  SQL Executor POST Layer - Hybrid Parameter Interface v3.0
#  Created by: THE Little Prince × ROP × FOP
#
#  Interface Philosophy:
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  exec_sql(sql, *args, params=None, db=None, **kwargs)
#  
#  Parameter Priority:
#  1. params (explicit dict/tuple) - highest priority, clearest
#  2. *args (positional) - simple cases
#  3. **kwargs (named) - intuitive, but watch reserved words
#  
#  Reserved kwargs: db, safe, debug, params
#  All other kwargs become SQL parameters
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional, List, Union

from usekit.classes.common.errors.helper_debug import log_and_raise


# Reserved parameter names (not SQL parameters)
RESERVED_PARAMS = {'db', 'safe', 'debug', 'params'}


@log_and_raise
def exec_sql(
    sql_or_path: Union[str, Path],
    *args,
    params: Optional[Union[dict, tuple]] = None,
    db: Optional[Any] = None,
    safe: bool = True,
    debug: bool = False,
    **kwargs
) -> List[Any]:
    """
    Execute SQL with flexible parameter passing.
    
    Interface Design:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    exec_sql(sql_or_path, *args, params=None, db=None, **kwargs)
    
    Parameter Priority:
        1. params (explicit) - highest priority
        2. *args (positional) - if no params
        3. **kwargs (named) - if no params and no args
        
    Reserved kwargs: db, safe, debug, params
    All other kwargs become SQL parameters automatically!
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    Args:
        sql_or_path: SQL text or file pattern/path
            - Inline SQL: "SELECT * FROM users WHERE id = ?"
            - File pattern: "select_user_info"
            - File path: "queries/users.sql"
            
        *args: Positional SQL parameters (for ? placeholders)
            Priority: 2nd (if no params)
            
        params: Explicit SQL parameters (dict for named, tuple for positional)
            Priority: 1st (highest)
            Use this to avoid reserved word conflicts
            
        db: Database connection (optional if DB_PATH configured)
            - Path string: "data/my.db"
            - Path object: Path("data/my.db")
            - Connection: sqlite3.Connection object
            - None: Use default from sys_const.yaml
            
        safe: Safe execution mode (reserved for future)
        
        debug: Enable debug output
        
        **kwargs: Named SQL parameters (for :name placeholders)
            Priority: 3rd (lowest, fallback)
            Reserved: db, safe, debug, params
            All other kwargs become SQL parameters
            
    Returns:
        List of results:
        - SELECT: [{'col1': val1, 'col2': val2}, ...]
        - DML: [Row(affected=N)]
        - Empty: []
        
    Examples:
        # Method 1: Direct kwargs (most intuitive for simple cases)
        >>> exec_sql("query.sql", id=124, name="test", db=conn)
        [{'id': 124, 'name': 'test', ...}]
        
        # Method 2: Explicit params (clearest, recommended for complex)
        >>> exec_sql(
        ...     "search.sql",
        ...     params={'city': 'Seoul', 'min_age': 20, 'max_age': 30},
        ...     db=conn
        ... )
        
        # Method 3: Positional args (simplest for ? placeholders)
        >>> exec_sql("query.sql", 124, "test", db=conn)
        
        # Method 4: Avoiding reserved word conflicts
        >>> exec_sql(
        ...     "query.sql",
        ...     params={'db': 'production', 'debug': True},  # SQL params
        ...     db=conn,                                      # Function param
        ...     debug=True                                    # Function param
        ... )
        
        # Method 5: Inline SQL with kwargs
        >>> exec_sql(
        ...     "SELECT * FROM users WHERE city = :city AND age > :age",
        ...     city="Seoul",
        ...     age=20,
        ...     db=conn
        ... )
        
        # Method 6: File pattern with positional args
        >>> exec_sql("select_user_info", 10, 20, db=conn)
    """
    
    if debug:
        print(f"[SQL-POST] sql_or_path: {sql_or_path}")
        print(f"[SQL-POST] args: {args}")
        print(f"[SQL-POST] params: {params}")
        print(f"[SQL-POST] kwargs: {kwargs}")
        print(f"[SQL-POST] db: {db}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Parameter Resolution (Priority Order)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if params is not None:
        # Priority 1: Explicit params (highest)
        sql_params = params
        if debug:
            print(f"[SQL-POST] Using explicit params: {sql_params}")
            
        # Check for conflicts
        if args:
            raise ValueError(
                "Cannot specify both 'params' and positional args. "
                "Use either: params={'id': 10} OR positional (10,)"
            )
        
        non_reserved_kwargs = {k: v for k, v in kwargs.items() if k not in RESERVED_PARAMS}
        if non_reserved_kwargs:
            raise ValueError(
                f"Cannot specify both 'params' and SQL kwargs. "
                f"Found SQL kwargs: {list(non_reserved_kwargs.keys())}. "
                f"Use either: params={{'id': 10}} OR id=10"
            )
            
    elif args:
        # Priority 2: Positional args
        sql_params = args
        if debug:
            print(f"[SQL-POST] Using positional args: {sql_params}")
            
        # Check for conflicts
        non_reserved_kwargs = {k: v for k, v in kwargs.items() if k not in RESERVED_PARAMS}
        if non_reserved_kwargs:
            raise ValueError(
                "Cannot mix positional args and SQL kwargs. "
                f"Found: args={args} and kwargs={list(non_reserved_kwargs.keys())}. "
                "Use either: (10, 20) OR id=10, age=20"
            )
            
    else:
        # Priority 3: Extract SQL params from kwargs (lowest priority)
        sql_params = {k: v for k, v in kwargs.items() if k not in RESERVED_PARAMS}
        
        if sql_params:
            if debug:
                print(f"[SQL-POST] Using kwargs as SQL params: {sql_params}")
        else:
            sql_params = None
            if debug:
                print(f"[SQL-POST] No SQL parameters")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SQL Loading
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Determine if inline SQL or file
    sql_text = str(sql_or_path)
    is_inline = _is_inline_sql(sql_text)
    
    if is_inline:
        # Inline SQL
        final_sql = sql_text
        if debug:
            print(f"[SQL-POST] Inline SQL detected")
            print(f"[SQL-POST] SQL preview: {final_sql[:80]}...")
    else:
        # File - load SQL
        if debug:
            print(f"[SQL-POST] File pattern detected: {sql_text}")
        
        from usekit.classes.data.base.post.parser.parser_sql import load
        
        try:
            final_sql = load(sql_text)
            if debug:
                print(f"[SQL-POST] Loaded SQL from file: {sql_text}")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"SQL file not found: '{sql_text}'\n"
                f"Tried to load as file path. "
                f"For pattern-based search, use LOAD layer (ebl_exec_sql)."
            )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Database Connection
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if db is None:
        # Try to get default DB from sys_const.yaml
        try:
            from usekit.classes.common.utils.helper_const import get_const, get_base_path
            db_root = get_const("DB_PATH.root")
            db_file = get_const("DB_PATH.db")
            db = get_base_path() / db_root / db_file
            
            if debug:
                print(f"[SQL-POST] Using default DB: {db}")
        except (KeyError, FileNotFoundError):
            raise ValueError(
                "Database connection required: pass 'db' parameter or "
                "configure DB_PATH in sys_const.yaml"
            )
    
    if debug:
        print(f"[SQL-POST] Final DB: {db}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SQL Execution
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    from usekit.classes.data.base.post.parser.parser_sql import query, execute
    
    # Detect SQL type
    sql_upper = final_sql.strip().upper()
    is_select = sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')
    
    if debug:
        sql_type = "SELECT" if is_select else "DML"
        print(f"[SQL-POST] SQL type: {sql_type}")
        if sql_params:
            print(f"[SQL-POST] Final SQL params: {sql_params}")
    
    # Execute
    if is_select:
        # SELECT query
        rows = query(
            sql=final_sql,
            db=db,
            params=sql_params,
            as_dict=True
        )
        
        if debug:
            print(f"[SQL-POST] Result: {len(rows)} rows")
            if rows:
                print(f"[SQL-POST] First row: {rows[0]}")
        
        return rows
    else:
        # INSERT/UPDATE/DELETE
        affected = execute(
            sql=final_sql,
            db=db,
            params=sql_params,
            commit=True
        )
        
        if debug:
            print(f"[SQL-POST] Affected: {affected} rows")
        
        return [Row(affected=affected)]


def _is_inline_sql(text: str) -> bool:
    """
    Detect if text is inline SQL or file pattern.
    
    Inline SQL starts with SQL keywords.
    Everything else is treated as file pattern/path.
    """
    sql_keywords = (
        'SELECT', 'INSERT', 'UPDATE', 'DELETE',
        'WITH', 'CREATE', 'DROP', 'ALTER'
    )
    
    text_upper = text.strip().upper()
    return any(text_upper.startswith(kw) for kw in sql_keywords)


# Row class for DML results
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Row:
    """
    SQL DML result with attribute/dict access.
    
    Examples:
        >>> row = Row(affected=3)
        >>> row.affected
        3
        >>> row['affected']
        3
    """
    
    def __init__(self, **kwargs):
        self._data = kwargs
    
    def __getattr__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"Row has no attribute '{name}'")
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __iter__(self):
        return iter(self._data.values())
    
    def __len__(self):
        return len(self._data)
    
    def __repr__(self):
        items = ', '.join(f"{k}={v!r}" for k, v in self._data.items())
        return f"Row({items})"
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def items(self):
        return self._data.items()
    
    def to_dict(self):
        return self._data.copy()


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "exec_sql",
    "Row",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
