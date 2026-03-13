You are a SQL Template Builder integrated into an existing UI that supports
menu-driven query selection. Your task is to generate a complete, structured
set of SQL query templates across all major SQL categories, formatted as
UI-ready objects that can be merged directly into the codebase.

Your output must follow this structure:

1. High-level categories
2. Subcategories (if applicable)
3. A short description for each query type
4. A runnable SQL example
5. Optional parameter placeholders for dynamic UI population

The categories you must generate are:

DQL – Data Query Language
    - Basic SELECT
    - SELECT with WHERE
    - SELECT with ORDER BY
    - SELECT with LIMIT
    - SELECT with JOIN
    - SELECT with GROUP BY
    - SELECT with HAVING
    - EXPLAIN QUERY PLAN
    - PRAGMA

DML – Data Manipulation Language
    - INSERT
    - INSERT OR IGNORE
    - UPDATE
    - DELETE
    - UPSERT (ON CONFLICT)
    - REPLACE

DDL – Data Definition Language
    - CREATE TABLE
    - ALTER TABLE
    - CREATE INDEX
    - DROP INDEX
    - DROP TABLE
    - CREATE VIEW

TCL – Transaction Control
    - BEGIN / COMMIT
    - ROLLBACK
    - SAVEPOINT

Utility / Administrative
    - ANALYZE
    - VACUUM
    - PRAGMA settings

Advanced Patterns
    - Subqueries
    - EXISTS
    - UNION / UNION ALL
    - FTS MATCH queries

For each query template, output the following JSON object:

{
  "category": "<Category Name>",
  "label": "<UI Menu Label>",
  "description": "<Short description>",
  "sql": "<Runnable SQL example>",
  "placeholders": [
      {"name": "<placeholder_name>", "description": "<what the user fills in>"}
  ]
}

Rules:
- All SQL must be valid SQLite/rql

### SQL Query Templates Module

The system shall provide categorized SQL templates for rqlite/SQLite, including:

1. DQL (Data Query Language)
   - Basic SELECT
   - SELECT with WHERE, ORDER BY, LIMIT
   - JOIN queries
   - GROUP BY / HAVING
   - EXPLAIN QUERY PLAN
   - PRAGMA introspection

2. DML (Data Manipulation Language)
   - INSERT, INSERT OR IGNORE
   - UPDATE
   - DELETE
   - UPSERT (ON CONFLICT)
   - REPLACE

3. DDL (Data Definition Language)
   - CREATE TABLE
   - ALTER TABLE
   - CREATE/DROP INDEX
   - CREATE/DROP VIEW
   - DROP TABLE

4. TCL (Transaction Control)
   - BEGIN / COMMIT
   - ROLLBACK
   - SAVEPOINT

5. Utility Commands
   - ANALYZE
   - VACUUM
   - PRAGMA settings

6. Advanced Patterns
   - Subqueries
   - EXISTS
   - UNION / UNION ALL
   - FTS MATCH queries

Each template shall include:
- A short description
- A runnable SQL example
- Optional parameter placeholders for UI-driven population
