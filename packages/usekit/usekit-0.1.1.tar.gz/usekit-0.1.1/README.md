# usekit

A lightweight, mobile-first Python toolkit for **Memory-Oriented Software Architecture (MOSA)**.

**Code is not function, but memory.**

```python
from usekit import u

u.wjb({"hello": "world"}, "config")     # write json to base
data = u.rjb("config")                  # read json from base
u.ujb({"version": "1.0"})               # update json
```

**3-letter interface**: Verb + Object + Location  
Minimal typing. Semantic paths. Mobile-optimized.

---

## Quick Start

### Installation

```bash
pip install usekit
```

### 30-Second Demo

```python
import usekit
from usekit import use, u, s

print("usekit:", usekit.__version__)

# Basic DATA operations
u.wjb({"hello": "MOSA"}, "config")      # write json base
data = u.rjb("config")                  # read json from base
u.ujb({"version": "1.0"})               # update json

# Safe operations (returns None on error)
data = s.rjb("missing")                 # safe read
```

---

## Status

- **Version**: 0.1.1  
- **Stage**: Alpha (API may change)
- **Focus**: Stable DATA/NAVI core, EXEC layer expanding

**Links**:
- PyPI: https://pypi.org/project/usekit  
- TestPyPI: https://test.pypi.org/project/usekit  

---

## Core Concept

### 3-Letter Interface

**Pattern**: `u.[action][format][location]`

```
u.rjb()  →  read json base
u.wys()  →  write yaml sub
u.ujt()  →  update json tmp
```

### Actions

**DATA I/O**: `r`ead, `w`rite, `u`pdate, `d`elete, `e`xists  
**NAVI**: `p`ath, `f`ind, `l`ist, `g`et, `s`et  
**EXEC**: e`x`ec, `i`mport, reru`n`, `q`uit

### Formats

**Basic**: `j`son, `y`aml, `t`xt, `m`d, `c`sv  
**Advanced**: `s`ql, `d`dl, `p`yp (Python), `a`ny

### Locations

`b`ase, `s`ub, `n`ow, `t`mp, `d`ir, `p`re, `c`ache

---

## Usage Examples

### File Operations

```python
from usekit import u

# JSON operations
data = u.rjb("config")                  # read
u.wjb({"key": "value"}, "output")       # write
u.ujb({"new": "data"}, "config")        # update
u.djb("old")                            # delete
exists = u.ejb("config")                # check exists

# Different locations
u.rjs("config")                         # read json sub
u.wyt({"temp": "data"}, "cache")        # write yaml tmp
u.rtb("readme")                         # read text base
```

### Pattern Matching

```python
# Find files with wildcards
users = u.fjb("user_*")                 # find user_*.json
for item in users:
    print(item["file"], item["data"])

# List all files
json_files = u.ljb()                    # list all json in base

# Recursive search
logs = u.fjb("log_*", walk=True)        # search subdirectories
```

### KeyData (Nested Access)

```python
# Data: {"user": {"profile": {"email": "a@b.com"}}}

# Read nested value
email = u.rjb("config", keydata="user/profile/email")

# Update nested value
u.ujb("config", keydata="user/profile/email", data="new@example.com")

# Array access
name = u.rjb("data", keydata="items[0]/name")

# Get field from multiple files
emails = u.rjb("user_*", keydata="email")
```

### Python Module Operations

```python
from usekit import use

# 1) Write a Python file
data = """
def add(a, b):
    return a + b

def multiply(x, y, z=1):
    return x * y * z

def greet(name, title="Mr.", greeting="Hello"):
    return f"{greeting}, {title} {name}!"
"""
use.write.pyp.base(data, nm="test_import")

# 2) Import functions (no path needed)
use.imp.pyp.base("test_import:add, multiply")

print(add(10, 20))                      # 30
print(multiply(10, 2, 3))               # 60

# 3) Execute function directly
use.exec.pyp.base(
    "test_import:greet",
    "Alice",
    title="Dr."
)
```

### SQL Operations

```python
# Execute SQL
results = u.esb("SELECT * FROM users")

# With parameters
u.esb(
    "SELECT * FROM users WHERE age > :age",
    params={"age": 18}
)

# Read SQL file
query = u.rsb("queries/select_users")
```

### Safe Mode

```python
from usekit import s

# Returns None instead of exceptions
data = s.rjb("missing")                 # returns None if error
config = s.rjb("config") or {}
```

---

## Google Colab

```python
# Mount Google Drive
from google.colab import drive
drive.mount("/content/drive")

# Use usekit
from usekit import u

data = u.rjd("config", dir_path="/content/drive/MyDrive/project")
u.wjd(results, "output", dir_path="/content/drive/MyDrive/project")
```

### Semantic Paths

```python
# Configure in .env
# PATH_BASE=/content/project
# PATH_DATA=/content/drive/MyDrive/datasets

# Use @ paths
data = u.rjb("@base/config")            # reads from PATH_BASE
model = u.rjb("@data/training")         # reads from PATH_DATA
```

---

## Configuration

### Environment File

usekit auto-generates `.env`:

```bash
# Core paths
PATH_BASE=/content/project
PATH_SUB=/content/project/data
PATH_NOW=/content
PATH_TMP=/tmp
PATH_DIR=/content/drive/MyDrive
PATH_PRE=/content/presets
PATH_CACHE=/tmp/cache

# Database (optional)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb
```

### Parameter Aliases

```python
# Full form (IDE-friendly)
u.rjb(name="config", keydata="user/email", default=None)

# Short form (mobile-optimized)
u.rjb(nm="config", kd="user/email", df=None)

# Direct path (most common)
u.rjb("config")
```

**Alias Rules**: 4+ chars → 2-letter alias  
`name`→`nm`, `keydata`→`kd`, `default`→`df`, `dir_path`→`dp`

---

## Philosophy: MOSA

**Memory-Oriented Software Architecture**

1. **Code is Memory**: Focus on data meaning, not file location
2. **Semantic Over Physical**: Use meaningful names, not paths
3. **Mobile-First**: Optimized for constrained environments
4. **Rule of 5**: Keep cognitive chunks ≤ 5 elements
5. **SmallBig Design**: 90% simple, 10% powerful

### Token Economy

usekit saves ~65% tokens vs natural language:

```
Natural: "Read the JSON file named config from the base directory"
usekit:  u.rjb("config")

Tokens: ~12 → ~3
```

Ideal for LLM-assisted development.

---

## Requirements

- Python 3.7+
- PyYAML
- python-dotenv

**Optional**: pandas, beautifulsoup4, sqlalchemy

---

## Roadmap

**Current v0.1.1 (Alpha)**
- Stable DATA/NAVI layers
- Expanding EXEC layer
- 30+ format support

**v0.2.0**: Complete EXEC, enhanced SQL  
**v0.3.0**: KeyMemory format, KQL language  
**v1.0.0**: Stable API, full docs

---

## Help System

```python
from usekit import u

u.help()                                # overview
u.help("quick")                         # quick start
u.help("examples")                      # usage examples
u.help("pattern")                       # pattern matching
u.help("keydata")                       # nested access
```

---

## License

MIT License

---

## Links

- PyPI: https://pypi.org/project/usekit
- TestPyPI: https://test.pypi.org/project/usekit
- GitHub: Coming soon
- Documentation: Coming soon

---

**Created by THE Little Prince, in harmony with ROP and FOP**

*usekit - Code is memory, not function*
