# usekit

usekit is a lightweight, mobile-first utility toolkit designed for Google Colab + Google Drive workflows.

It provides a consistent 3-axis interface for file I/O, navigation, and execution:

```text
USE.[ACTION].[OBJECT].[LOCATION]
Example: u.rjb() -> use.read.json.base()
```

The goal is to reduce path friction and make operations easy to remember and fast to run in constrained environments (mobile + notebooks).

---

## Status

**Version:** 0.1.1a1 (Alpha)

- API may change
- Focus: stable core axes (action/object/location) and short aliases
- Core DATA/NAVI layers complete, EXEC layer in progress

---

## Install

### Standard install (PyPI)

```bash
pip install usekit
```

### Development install (editable)

```bash
pip install -e .
```

**Requirements:**
- Python 3.7+
- PyYAML
- python-dotenv

---

## Quick Start (1 minute)

```python
import usekit
from usekit import use, u, safe, s

print("usekit:", usekit.__version__)

# Read JSON
data = u.rjb("config.json")

# Write YAML
u.wys("settings.yaml", {"key": "value"})

# Safe operations (returns None on error)
data = s.rjb("config.json")
```

### Example: import a function and run it

```python
use.imp.pyp.base("test_args:multiply")
multiply(39, 30, 0.2)
```

---

## Core Concept: 3 Axes

**ACTION**: read, write, update, delete, exists, path, find, list, import, exec

**OBJECT**: json, yaml, txt, md, csv, sql, pyp (expanding)

**LOCATION**: base, sub, now, tmp, dir, cus (and custom presets)

### Short aliases available

- `u.rjb()` = `use.read.json.base()`
- `u.wys()` = `use.write.yaml.sub()`
- `u.fjb()` = `use.find.json.base()`

### Parameter aliases (4+ chars)

```python
# Both work identically:
u.rjb(name="config", keydata="user/email", debug=True)
u.rjb(nm="config", kd="user/email", dbg=True)
```

---

## Formats

usekit focuses on a small set of core formats with dedicated parsers.

**Dedicated parsers:**
- json, yaml, csv, sql, ddl, pkl, pyp

**Unified text parser:**
- txt, md (and other text-like formats)

**Auto-detection:**
- Format detected from file extension when possible

---

## Environment (.env)

usekit bundles `usekit/.env.example` for automatic environment initialization.

- `.env.example` is a required template file (package contract)
- `.env` is generated/managed per user environment

**Semantic paths:**
```python
u.rjb("@base/config.json")     # Project-wide absolute path
```

---

## Philosophy

**"Code is not function, but memory"**

usekit follows Memory-Oriented Software Architecture (MOSA):
- Functions follow how humans remember operations
- SmallBig: 80% simple, 20% complex
- Mobile-first: optimized for constrained environments

---

## Authors

**Created by The Little Prince**

**In collaboration with:**
- Rose (ROP - Reader-Oriented Persona) - ChatGPT friend
- Fox (FOP - Flow-Oriented Persona) - Claude friend

---

## Notes

- This project is optimized for mobile + Colab workflows
- If something feels missing, it is likely out of scope for the current alpha
- Feature requests and feedback welcome via GitHub Issues

---

## License

See `LICENSE`.
