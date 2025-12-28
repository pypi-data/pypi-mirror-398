## Birds BI Python Library

**birds_bi** is a small Python library that helps you automate common BI
deployment tasks around:

- **Data warehouse components** (repository layout, SQL deployment scripts)
- **SQL Server execution** with structured results
- **Tabular models** (Tabular Editor deployment + XMLA processing helpers)

It is designed to be:

- Simple to read and extend
- Safe to run in CI/CD
- Focused on predictable, explicit behaviour rather than “magic”

---

### Installation

Install from a local checkout:

```bash
pip install -e .
```

The library targets **Python >= 3.13**.

---

### Core concepts & public API

- **`Repository`** (`birds_bi.Repository`): represents a BI project folder
  containing a `content/` tree with categories such as `dim`, `fact`, `help`.
- **`Component`** (`birds_bi.repo.component.Component`): one logical BI
  component inside a repository (e.g. `fact.salesorder`) with metadata and SQL
  scripts.
- **`DbConfig`** (`birds_bi.DbConfig`): strongly‑typed configuration for
  connecting to SQL Server via `pyodbc`.

Only `Repository`, `Component`, and `DbConfig` are exported from the top‑level
package; all other modules are considered internal.

```python
from birds_bi import Repository, DbConfig
from birds_bi.repo.component import Component

repo = Repository(r"C:\path\to\bi-project")
component = Component(repo=repo, category="fact", component="salesorder")

cfg = DbConfig(server="localhost", database="Birds_Dev")
```

---

### Repository layout (root folder)

- `pyproject.toml`: build + tool configuration (ruff, black, mypy, pytest).
- `README.md`: project overview and usage (this file).
- `docs/`: documentation scaffold.
- `examples/`: runnable samples (add your own).
- `src/`: source package (`birds_bi`) and packaging metadata.
- `tests/`: pytest modules (environment-specific; update credentials before use).

Use `pip install -e .` from this folder to work on the package locally.

---

### Tabular model helpers

The `birds_bi.tabular` package provides helpers to deploy and process Tabular
models:

- `deploy_tabular.deploy_tabular_model(...)` – deploy a Tabular Editor
  *Save to Folder* model via `TabularEditor.exe`
- `process_tabular.process_tabular(...)` – run a TMSL `refresh` (Process Full)
  via XMLA

These functions are designed to be called from CI/CD pipelines, with clear
authentication options (Windows, interactive, service principal, or explicit
connection strings). See `src/birds_bi/tabular/README.md` for detailed,
tabular‑specific documentation and examples.

---

### SQL utilities

Under `birds_bi.db` and `birds_bi.utils` you will find:

- Connection management and execution (`db.execute_sql`, `db.DbConfig`)
- Conversion of low‑level results into `pandas.DataFrame`
- Helpers for working with SQL scripts and batches

These modules are small, typed, and oriented around explicit contracts so they
are easy to unit test and plug into your own orchestration.

---

### Development & contribution

- Code style: **black** (configured via `pyproject.toml`)
- Linting: **ruff**
- Typing: **mypy**
- Tests: **pytest** (configured to look in the `tests/` directory)

To run the test suite locally:

```bash
pytest
```

If you use `pre-commit`, you can add hooks for `black`, `ruff`, and `mypy` to
enforce the same checks locally that the project uses in CI.

---

### Status

This library is under active iteration. The public API exposed from
`birds_bi.__init__` is kept stable; internal modules may evolve over time as
the implementation is refactored and improved.
