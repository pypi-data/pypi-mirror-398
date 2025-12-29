# PY DBMS — A Modern, Secure MySQL CLI Client

**Stable Release — v2.5.0**

PY DBMS is a modern, developer-focused command-line client for MySQL, built with Python.  
It provides a clean terminal UI, readable query output, and powerful helper commands—without sacrificing safety or simplicity.

Designed for developers who live in the terminal but want a more structured, reliable experience than the default MySQL CLI.

---

## Key Features

### Terminal UX
- Rich-based terminal interface with structured panels and tables
- Clean, readable formatting for query results
- Typewriter-style text rendering for status messages
- ASCII startup banner and session dashboard

### Query Execution
- Multi-line SQL query support
- Accurate execution feedback (success, warnings, errors)
- Execution time reporting for SELECT queries
- Separate handling for SELECT vs DML / DDL operations

### Configuration & Control
- Persistent JSON-based configuration system (`config.json`)
- Session-level configuration for runtime behavior changes
- Inline query flags (e.g. `--expand`) for per-query output overrides
- Interactive configuration inspection and modification via meta-commands

### Security
- Masked password input
- Safe defaults for local development
- No credential persistence

---

## Installation

### Prerequisites
- Python **3.10+** (recommended)
- A running MySQL Server

### Install via pip
```bash
pip install py-dbms-cli  
```

### Usage

**1. Run from your terminal**
```bash
pydbms  
```

**2. When prompted, enter credentials to establish connection with MySQL**
You will be prompted for:
  - Host
  - Username
  - Password (masked)

**3. Begin querying**

Enter SQL commands as you normally would.  
Multi-line queries are supported and executed once terminated with ;.  

---

## Meta Commands

PY DBMS includes several helper commands for interactive usage:

| Command | Description |
|------|-----------|
| `.help` | Show all helper commands |
| `.databases` | List all databases |
| `.tables` | List tables in the current database |
| `.schema <table>` | Show CREATE TABLE definition |
| `.clear` | Clear the terminal screen |
| `.version` | Show build and version information |
| `.config` | Show persistent configuration |
| `.config set <section>.<key> <value>` | Update a config value |
| `.config reset <section>.<key>` | Reset a config value |
| `.session-config` | Show session-level configuration |
| `.session-config set <key> <value>` | Update session-only settings |
| `.session-config reset <key>` | Reset a session setting |
| `.exit` | Exit the CLI |

---

## Roadmap

Planned future improvements include:

- Exporting query results to CSV and JSON
- Extended output formatting options
- Support for additional database engines
- Improved extensibility for plugins and integrations

---

## Author

Anish Sethi  
B.Tech Computer Science & Engineering  
Delhi Technological University (Class of 2029)  

---

## License

This project is licensed under the BSD 3-Clause License.  
Visit the [BSD 3-Clause License page](https://opensource.org/license/bsd-3-clause) for more information.
