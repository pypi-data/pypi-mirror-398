**STABLE RELEASE**
### v2.1.5

PY DBMS — A Modern, Secure, All-in-One DBMS CLI Client

PY DBMS is a lightweight, secure, and modern command-line database client built using Python.
It provides a clean user experience, readable output formatting, and convenient helper commands while connecting to MySQL.

This tool is designed for developers who prefer the terminal but want a more enhanced experience than the default MySQL CLI.

Features
Visual & UI

Rich-based terminal interface for clean, formatted output

Typewriter-style text rendering

ASCII banner and structured dashboard

Tabular display for query results

Password masking during login

Functional

Multi-line SQL query support

Built-in meta commands (.help, .tables, .schema, .version, etc.)

Execution time for SELECT queries

Graceful error handling (no session crashes)

Security

Secure password input using masked characters

Localhost defaults for safe development usage

Installation

Prerequisites

Python (3.10 or newer recommended)

A running MySQL Server

Install using pip:

pip install py-dbms-cli


All required dependencies are installed automatically.

Usage

1. Start the CLI
pydbms

2. Enter MySQL login credentials

You will be prompted for:

Host

Username

Password (masked using *)

3. Begin querying

Enter SQL commands as you normally would. The client supports multi-line queries and executes them once terminated with a ;.

Query Support

Standard SQL queries

Multi-line input

Separate behaviors for SELECT vs UPDATE/INSERT

MySQL-style syntax

Meta Commands

The tool includes additional helper commands:

Command	Description
.help	                Show all helper commands
.databases	            List all databases
.tables	                List tables in the current database
.schema <table>	        Show CREATE TABLE definition
.clear	                Clear the screen
.version	            Show build/version info
.config                 Show config settings for pydbms
.config set <>.<> <>    Set config to a value
.config reset <>.<>     Reset config to a default
.exit	                Exit the CLI

Roadmap

Future planned features include:

User profile support with encrypted JSON storage

Support for additional database engines (Oracle, MongoDB, etc.)

Consistent UI formatting across engines

Exportable session history

Customizable UI themes

Author

Anish Sethi
B.Tech Computer Science & Engineering
Delhi Technological University (Class of 2029)

License

This project is licensed under the BSD 3-Clause License.