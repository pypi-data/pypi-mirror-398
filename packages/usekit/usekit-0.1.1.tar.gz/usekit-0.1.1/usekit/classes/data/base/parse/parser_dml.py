# Path: (./Mydrive/././)classes/common/parse/
# File: dml.py
# ----------------------------------------------------------------------------------------------- #
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- #

import sqlparse

class dmlDecodeError(Exception):
    """Raised when SQL parsing fails."""
    pass

def load(f):
    """
    Parse the SQL file and return a dictionary with the list of statements.
    """
    try:
        content = f.read()
        statements = [str(stmt).strip() for stmt in sqlparse.parse(content) if str(stmt).strip()]
        return {"statements": statements}
    except Exception as e:
        raise dmlDecodeError(f"Failed to parse SQL: {e}")

def dump(data, f, **kwargs):
    """
    Write a list of SQL statements to the file, each ending with a semicolon.
    """
    statements = data.get("statements", []) if isinstance(data, dict) else []
    for stmt in statements:
        f.write(stmt.strip() + ";\n")