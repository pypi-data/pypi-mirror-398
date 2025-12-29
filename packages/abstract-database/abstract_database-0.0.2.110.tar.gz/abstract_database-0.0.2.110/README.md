---

# abstract\_database · v0.0.2.101

A lightweight, modular database toolkit for Python that centralizes **connection management**, **environment-driven configuration**, **table discovery**, **query/search helpers**, and **result export**—with batteries included for Pandas/Excel and your `abstract_*` ecosystem.

* **Author:** putkoff ([partners@abstractendeavors.com](mailto:partners@abstractendeavors.com))
* **License:** MIT
* **Python:** 3.6+ (tested with 3.11)
* **Status:** Alpha

---

## Why this exists

You’ve got multiple apps and services that need to talk to Postgres (and occasionally RabbitMQ), each with their own DB name/type, credential sets, and table templates. This package gives you:

* A **singleton** `connectionManager` with env-driven config
* A thin **DatabaseManager** facade for common ops
* A set of **post functions** (free functions) for quick scripting
* Utilities to **generate table templates** from JSON samples
* Helpers to **serialize/flatten** results and **export** to Excel

It’s intentionally minimal on heavy ORMs so it can slot into existing code quickly—especially alongside the `abstract_*` modules.

---

## Features

* **Env-driven connections**
  `DBNAME_DBTYPE_USER`, `…_PASSWORD`, `…_HOST`, `…_PORT`, `…_DBNAME` → auto-assembled into a full URL.

* **Single entry-point manager**
  `connectionManager` (Singleton) + convenience functions in `postFunctions.py` to avoid boilerplate.

* **Template generation from JSON**
  `get_templates.py` analyzes JSON files to infer `valueKeys` and `unique_keys` you can use for schema planning.

* **Quick querying utilities**
  Helpers for “first row as dict”, multi-field search, simple SQL execution, and table list/bootstrap patterns.

* **Pandas interop**
  `save_to_excel()` and “query → Excel” paths for quick offline inspection.

* **Composable managers**
  Organized by responsibility under `src/abstract_database/managers/...` (connection, database, session, table, etc.).

---

## Installation

```bash
# recommended: in your project's venv/conda env
pip install -U abstract_database
# or, from your repo root
pip install -e .
```

**Dependencies** (auto-installed): `sqlalchemy`, `abstract_pandas`, `pandas`, `abstract_utilities`
(Postgres: `psycopg2` is imported internally; ensure your system libs are ready or use `psycopg2-binary` if appropriate.)

---

## Quick start

### 1) Environment variables

The package derives credentials from **name + type + key**:

```
{DBNAME}_{DBTYPE}_{KEY}
```

All segments are **uppercased**. Required keys:

* `USER`
* `PASSWORD`
* `HOST`
* `PORT`
* `DBNAME`

**Example (.env):**

```dotenv
# Example for: dbName="abstract", dbType="database"
ABSTRACT_DATABASE_USER=postgres
ABSTRACT_DATABASE_PASSWORD=supersecret
ABSTRACT_DATABASE_HOST=127.0.0.1
ABSTRACT_DATABASE_PORT=5432
ABSTRACT_DATABASE_DBNAME=abstract

# Optional: path to a JSON config file of table templates/rules, used by DatabaseManager
ABSTRACT_DATABASE_CONFIGPATH=/var/www/configs/abstract_database_tables.json
```

> The library discovers your `.env` via your existing `abstract_security` / `abstract_utilities` helpers (e.g., `get_env_value`, `get_env_path`).

### 2) Connect and run a simple query

You can use the class directly:

```python
from abstract_database.managers.connectionManager.utils.postFunctions import connect_db

with connect_db() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT now();")
        print(cur.fetchone())
```

…or grab a cursor that returns dict-like rows:

```python
from abstract_database.managers.connectionManager.utils.postFunctions import get_cur_conn

cur, conn = get_cur_conn(use_dict_cursor=True)
try:
    cur.execute("SELECT 1 AS ok;")
    print(cur.fetchone())  # {'ok': 1}
finally:
    cur.close()
    conn.close()
```

### 3) Use `DatabaseManager` for helper flows

```python
from abstract_database.managers.databaseManager.postFunctions import ensure_db_manager

db = ensure_db_manager(dbName="abstract", dbType="database")

# see table config if a JSON config file is set in ..._CONFIGPATH
tables = db.get_table_names()          # ['users', 'orders', ...] if provided
first = db.get_first_row_as_dict("users", db.connect_db())   # {'id': 1, ...}

# Peek value types for a sample row (useful for schema prompts)
types = db.analyze_variable_types(first)  # {'id': 'int', 'email': 'str', ...}

# Export any query to Excel via pandas
rows = [(1, 'alice@example.com'), (2, 'bob@example.com')]
db.save_to_excel(rows, file_path="users.xlsx")
```

### 4) Insert/fetch via `TableManager` surface

```python
from abstract_database.managers.connectionManager.utils.postFunctions import (
    fetchFromDb, insertIntoDb, get_insert
)

# insert/get helpers work through the singleton connectionManager.table_mgr
insert_stmt = get_insert("users")  # depends on your TableManager config
insertIntoDb("users", "email", {"email": "eve@example.com", "name": "Eve"})
row = fetchFromDb("users", "eve@example.com")
print(row)
```

> The `TableManager` is configured when `connectionManager` initializes; it can also be seeded with a `tables_path` JSON file listing your table definitions.

---

## CLI-style helpers (post functions)

Import these when you want minimal ceremony in scripts:

```python
from abstract_database.managers.connectionManager.utils.postFunctions import (
  create_connection, connect_db, get_db_connection, put_db_connection,
  get_insert, fetchFromDb, insertIntoDb, search_multiple_fields, get_first_row_as_dict
)

# bootstrap (singleton under the hood)
create_connection(env_path="/path/to/.env", dbType="database", dbName="abstract")
```

---

## Template generation from JSON

Generate a template file (`valueKeys`, `unique_keys`) from a folder of JSON samples:

```python
from abstract_database.get_templates import create_templates

create_templates(
    json_folder="/path/to/json/samples",
    out_json="/path/to/output/templates.json"
)
```

Internally uses `get_value_type`, `get_value_keys`, and a simple uniqueness heuristic. Great for scaffolding column plans or validating ingested payload structures.

---

## Result export to Excel

```python
from abstract_database.managers.databaseManager.postFunctions import ensure_db_manager

db = ensure_db_manager()
rows = db.search_multiple_fields(  # supply your own query execution
    database_query={"query": "SELECT id, email FROM users LIMIT 100"}
)
db.get_query_save_to_excel(
    database_query={"query": "SELECT * FROM users"},
    file_path="users_dump.xlsx"
)
```

> Under the hood this calls `safe_excel_save` from `abstract_pandas` and will `flatten_json` per row when needed.

---

## Project layout (high-level)

```

src/abstract_database/
  managers/
    connectionManager/         # env parsing + psycopg2 connection(s)
    databaseManager/           # db-facing helpers (table config, exports, etc.)
    tableManager/              # insert/fetch/search surface
    sessionManager/            # (placeholder / future session helpers)
    ...
  query_utils/                 # structured query helpers (incl. Solana data callers)
  fetch_utils/                 # generic insert/select/update/remove split
  utils/                       # config/get_tables/get_templates/etc.
```
## Directory MAp (low-level)
```
├── README.md
├── module_info/
│   └── descriptions/
│       ├── abstract_database/
│       │   ├── abstract_database_cmd/
│       │   │   └── synopsis.txt
│       │   ├── connection_manager/
│       │   │   └── synopsis.txt
│       │   ├── dbManager/
│       │   │   └── synopsis.txt
│       │   ├── dbQuery/
│       │   │   └── synopsis.txt
│       │   ├── dbSearchFunctions/
│       │   │   └── synopsis.txt
│       │   ├── db_utils/
│       │   │   ├── db_functions/
│       │   │   │   └── synopsis.txt
│       │   │   ├── get_tables/
│       │   │   │   └── synopsis.txt
│       │   │   └── utils/
│       │   │       └── synopsis.txt
│       │   ├── env_functions/
│       │   │   └── synopsis.txt
│       │   └── get_templates/
│       │       └── synopsis.txt
│       ├── complete_synopsis.txt
│       ├── module_info.json
│       ├── module_info_grok.json
│       ├── modules.txt
│       └── read_me_response.json
├── pyproject.toml
├── setup.py
├── src/
│   └── abstract_database/
│       ├── dbManager.py
│       ├── fetch_utils/
│       │   ├── fetch_utils/
│       │   │   ├── insert_utils.py
│       │   │   ├── query_utils.py
│       │   │   ├── remove_utils.py
│       │   │   ├── select_utils.py
│       │   │   └── update_utils.py
│       │   ├── imports.py
│       │   └── utils/
│       │       ├── build_utils.py
│       │       ├── result_utils.py
│       │       └── toggle_utils.py
│       ├── imports.py
│       ├── managers/
│       │   ├── baseQueryManager/
│       │   │   ├── imports/
│       │   │   │   └── imports.py
│       │   │   └── utils/
│       │   │       └── utils.py
│       │   ├── columnNamesManager/
│       │   │   ├── imports/
│       │   │   │   └── imports.py
│       │   │   └── utils/
│       │   │       ├── main.py
│       │   │       ├── postFunctions.py
│       │   │       └── utils.py
│       │   ├── connectionManager/
│       │   │   ├── imports/
│       │   │   │   ├── abstract_imports.py
│       │   │   │   ├── local_imports.py
│       │   │   │   └── psycopg_imports.py
│       │   │   └── utils/
│       │   │       ├── main.py
│       │   │       ├── postFunctions.py
│       │   │       └── utils.py
│       │   ├── databaseBrowser/
│       │   │   ├── databaseBrowser.py
│       │   │   ├── imports/
│       │   │   │   ├── alchemy_imports.py
│       │   │   │   ├── local_imports.py
│       │   │   │   └── utilities_imports.py
│       │   │   └── utils/
│       │   │       ├── db_utils.py
│       │   │       └── utils.py
│       │   ├── databaseManager/
│       │   │   ├── databaseManager.py
│       │   │   ├── imports.py
│       │   │   └── postFunctions.py
│       │   ├── dbManager/
│       │   │   ├── imports.py
│       │   │   └── utils/
│       │   │       └── utils.py
│       │   ├── envManager/
│       │   │   ├── envManager.py
│       │   │   ├── imports.py
│       │   │   ├── postFunctions.py
│       │   │   └── utils/
│       │   │       └── utils.py
│       │   ├── imports.py
│       │   ├── logs/
│       │   ├── sessionManager/
│       │   │   └── sessionManager.py
│       │   └── tableManager/
│       │       ├── imports.py
│       │       ├── tableManager.py
│       │       └── utils/
│       │           ├── main.py
│       │           ├── postFunctions.py
│       │           └── utils.py
│       ├── pyproject.toml
│       ├── query_utils/
│       │   ├── imports.py
│       │   ├── paths.py
│       │   ├── query_utils.py
│       │   └── utils/
│       │       ├── call_functions/
│       │       │   ├── call_account_data.py
│       │       │   ├── call_log_data.py
│       │       │   ├── call_meta_data.py
│       │       │   ├── call_misc.py
│       │       │   ├── call_pair_data.py
│       │       │   ├── call_transactions_data.py
│       │       │   └── queries.py
│       │       ├── filter_functions/
│       │       │   └── filter_data_functions.py
│       │       ├── imports.py
│       │       ├── manual_connect/
│       │       │   ├── imports.py
│       │       │   └── utils/
│       │       │       └── utils.py
│       │       └── query_utils/
│       │           ├── imports.py
│       │           └── utils/
│       │               ├── execute_utils.py
│       │               ├── query_utils.py
│       │               └── utils.py
│       └── utils/
│           ├── imports.py
│           └── utils/
│               ├── config_utils/
│               │   ├── imports.py
│               │   └── utils/
│               │       └── utils.py
│               ├── db_functions/
│               │   ├── imports.py
│               │   └── utils/
│               │       └── utils.py
│               ├── get_tables/
│               │   ├── imports.py
│               │   └── utils/
│               │       └── utils.py
│               ├── get_templates/
│               │   ├── imports.py
│               │   └── utils/
│               │       └── utils.py
│               ├── get_time_data/
│               │   ├── imports.py
│               │   └── utils/
│               │       └── utils.py
│               ├── image_utils/
│               │   ├── imports.py
│               │   └── utils/
│               │       └── utils.py
│               ├── imports.py
│               ├── legacy_utils/
│               │   ├── imports.py
│               │   └── utils/
│               │       └── utils.py
│               └── solana/
│                   ├── get_meta.py
│                   ├── imports.py
│                   ├── pathUtils.py
│                   └── utils.py
├── test/
│   └── test_utils.py
└── testit.py
```
---

## Configuration keys (reference)

* `get_db_env_key(dbType, dbName, key)` → `"{DBNAME}_{DBTYPE}_{KEY}".upper()`
* Supported `key`: `user`, `password`, `host`, `port`, `dbname`
* Optional: `{DBNAME}_{DBTYPE}_CONFIGPATH` → path to a JSON array of table config objects.

**Example:** `ABSTRACT_DATABASE_USER`, `ABSTRACT_DATABASE_DBNAME`, etc.

---

## Security notes

* Prefer loading secrets via `.env` files with correct permissions or via your secret manager.
* `PASSWORD` is used as-is; if it includes special characters, it will be **URL-encoded** when the connection URL is constructed.
* Avoid logging full connection URLs.

---

## Known quirks / rough edges

* `safe_load_from_json(file_path=None)` in `utils/utils.py` appears self-recursive; ensure it calls the **abstract\_utilities** reader (e.g., `safe_read_from_json`) instead of itself.
* `connectionManager.check_conn()` calls `add_insert_list` twice—this may be harmless but redundant.
* Some helpers assume Postgres (`psycopg2`); RabbitMQ URL assembly is supported by switching protocol to `amqp`, but message-queue operations are **not** provided here.
* In `DatabaseManager.search_multiple_fields`, ensure the `query` variable is passed in (`**kwargs`) and used.

---

## Bash quickstart (because scripts are life)

```bash
#!/usr/bin/env bash
# save as db_env_example.sh, then: source db_env_example.sh

export ABSTRACT_DATABASE_USER="postgres"
export ABSTRACT_DATABASE_PASSWORD="supersecret"
export ABSTRACT_DATABASE_HOST="127.0.0.1"
export ABSTRACT_DATABASE_PORT="5432"
export ABSTRACT_DATABASE_DBNAME="abstract"
export ABSTRACT_DATABASE_CONFIGPATH="$HOME/configs/abstract_tables.json"

python - <<'PY'
from abstract_database.managers.connectionManager.utils.postFunctions import connect_db
with connect_db() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT 'abstract_database ok' AS msg;")
        print(cur.fetchone())
PY
```

---

## Examples

### A) One-liner insert & fetch

```python
from abstract_database.managers.connectionManager.utils.postFunctions import insertIntoDb, fetchFromDb

insertIntoDb("users", "email", {"email": "neo@matrix.io", "name": "Neo"})
print(fetchFromDb("users", "neo@matrix.io"))
```

### B) Get config-driven hints + a sample row

```python
from abstract_database.managers.databaseManager.postFunctions import ensure_db_manager

db = ensure_db_manager(dbName="abstract", dbType="database")
print(db.get_instruction_from_tableName("users"))
```

---

## Contributing

PRs and issues welcome. Please:

1. Add/adjust unit tests under `test/`
2. Keep public APIs minimal and predictable
3. Avoid breaking env-key conventions
4. Note any cross-module coupling with other `abstract_*` packages

---

## Changelog (highlights)

* **0.0.2.101**

  * Managers reorganized under `src/abstract_database/managers/**`
  * Convenience post-functions split for `connectionManager` and `databaseManager`
  * Query/export paths clarified; improved Pandas export flow

* **0.0.2.076**

  * Initial packaging of connection, search, utils, and template generation functionality

---

## License

MIT © putkoff

---

## Alternatives & notes

* If you want stronger type-safety and models, consider layering **SQLAlchemy ORM** or **Pydantic** schemas on top of this.
* For async workflows, consider **asyncpg** or **psycopg3 (psycopg >=3)** and mirror the manager APIs.
* Migrations are out of scope here; pair with **Alembic** for schema changes.
* If you later replace any `abstract_*` helpers with standards, prefer:
  `abstract_security.get_env_value` → `os.environ.get` (plus a typed loader)
  `abstract_pandas.safe_excel_save` → `pandas.DataFrame.to_excel` with exception wrappers.

---

## Minimal code reference

```python
# dump dicts safely (small utility used in places)
import json
def dump_if_json(obj):
    return json.dumps(obj) if isinstance(obj, dict) else obj
```

---

