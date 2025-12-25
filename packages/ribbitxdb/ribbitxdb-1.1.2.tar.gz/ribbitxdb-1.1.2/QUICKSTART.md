# RibbitXDB - Quick Start Guide

## Installation

```bash
# Install from source
cd d:\ribbitx
pip install -e .

# Or for PyPI (after publishing)
pip install ribbitxdb
```

## Basic Usage

```python
import ribbitxdb

# Connect to database
conn = ribbitxdb.connect('myapp.rbx')
cursor = conn.cursor()

# Create table
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE
    )
''')

# Insert data
cursor.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')")
cursor.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com')")
conn.commit()

# Query
cursor.execute("SELECT * FROM users")
for row in cursor.fetchall():
    print(row)

# Update
cursor.execute("UPDATE users SET email = 'newemail@example.com' WHERE id = 1")
conn.commit()

# Delete
cursor.execute("DELETE FROM users WHERE id = 2")
conn.commit()

# Close
conn.close()
```

## Features

- **BLAKE2 Hashing**: Every row automatically hashed for integrity
- **LZMA Compression**: Database files automatically compressed
- **B-tree Indexing**: Fast lookups with primary keys
- **Transactions**: Full ACID support with commit/rollback
- **SQLite3 Compatible**: Familiar API

## Publishing to PyPI

```bash
# Build distribution
python setup.py sdist bdist_wheel

# Upload to PyPI
pip install twine
twine upload dist/*
```

## Next Steps

1. Run tests: `python test_simple.py`
2. View examples: `python examples.py`
3. Read full docs: See README.md
