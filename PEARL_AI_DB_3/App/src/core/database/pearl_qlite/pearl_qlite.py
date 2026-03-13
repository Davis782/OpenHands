import os
import sqlite3
import json
import csv
import pickle
from typing import Optional, Union
from App.src.core.seedtools.seedtools import pearl_id_to_vector, seed_to_pearl_id
from App.config.sql_categories import SQL_CATEGORIES

class PearlClient:
    """SQLite-backed client for PEARLqlite-style operations."""

    def __hash__(self):
        return hash(self.active_db)

    def __eq__(self, other):
        if not isinstance(other, PearlClient):
            return NotImplemented
        return self.active_db == other.active_db

    def __init__(self, default_db: str = "project_mgmt_acct.db"):
        if default_db == ":memory:":
            self.active_db = ":memory:"
        else:
            DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "databases")
            os.makedirs(DB_DIR, exist_ok=True)
            self.active_db = os.path.join(DB_DIR, default_db)
        self.sql_dir = None # Initialize sql_dir attribute
        self._active_pearl_id = None # Initialize active PEARL ID
        self._connection = None # Store persistent connection
        # Ensure tables are created/updated when the client is initialized
        # This will be handled by _get_connection when the first connection is made.


    def set_active_pearl_id(self, pearl_id: str):
        """
        Sets the active PEARL ID for the client.
        """
        self._active_pearl_id = pearl_id

    def _get_connection(self):
        if self._connection is None:
            self._connection = sqlite3.connect(self.active_db, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row # Return rows as dict-like objects
            self._ensure_db_and_tables(self._connection) # Always ensure tables when a new connection is made
        return self._connection

    def close_connection(self):
        """
        Closes the database connection if it's open.
        """
        if self._connection:
            self._connection.close()
            self._connection = None

    def fetch_query_raw(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> list[sqlite3.Row]:
        """
        Executes a raw SELECT SQL query and fetches all results.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()

    def execute_query_raw(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> int:
        """
        Executes a raw SQL query (INSERT, UPDATE, DELETE, DDL).
        Args:
            sql (str): The SQL query string.
            params (Optional[Union[tuple, dict]]): Parameters for the query.
        Returns:
            int: The number of rows affected.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            return cursor.rowcount

    def _ensure_db_and_tables(self, conn):
        cursor = conn.cursor()

        # If using an in-memory database, skip loading SQL files from disk
        if self.active_db == ":memory:":
            print("DEBUG: In-memory database detected. Skipping SQL file loading.")
            # Manually create essential tables for CRDT tests if needed
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crdt_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    site_id TEXT NOT NULL,
                    log_entry TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crdt_counter (
                    counter_name TEXT NOT NULL,
                    site_id TEXT NOT NULL,
                    increments INTEGER DEFAULT 0,
                    decrements INTEGER DEFAULT 0,
                    PRIMARY KEY (counter_name, site_id)
                );
            """)
            conn.commit()
            return

        # Dynamically create tables based on SQL_CATEGORIES
        SQL_DIR = "C:\\Users\\Solid\\OneDrive\\Documents\\GitHub\\Trae_AI\\OpenHands\\PEARL_AI_DB_3\\App\\sql"
        print(f"DEBUG: SQL_DIR in _ensure_db_and_tables: {SQL_DIR}") # Debug print

        self.sql_dir = SQL_DIR # Assign to instance attribute

        # First, ensure pearl_ids table is created if it exists in SQL_CATEGORIES
        pearl_ids_created = False
        for category in SQL_CATEGORIES:
            for sql_file_name, relative_path in category.sql_files:
                if "create_pearls_table.sql" in relative_path:
                    file_path = os.path.join(SQL_DIR, relative_path)
                    print(f"DEBUG: Processing SQL file (pearls table): {file_path}") # Debug print
                    try:
                        with open(file_path, 'r') as f:
                            sql_script = f.read()
                        cursor.execute(sql_script)

                        pearl_ids_created = True
                    except FileNotFoundError:
                        pass # Log this silently or with a proper logging mechanism
                    except sqlite3.Error:
                        pass # Log this silently or with a proper logging mechanism
                    break # Found and executed, move to next category
            if pearl_ids_created: break

        # Then, execute other create table scripts
        for category in SQL_CATEGORIES:
            for sql_name, sql_file_path_relative in category.sql_files:
                # Only execute SQL files that start with 'create_' during schema initialization
                if os.path.basename(sql_file_path_relative).startswith("create_"):
                    full_sql_path = os.path.join(SQL_DIR, sql_file_path_relative)
                    print(f"DEBUG: Processing SQL file: {full_sql_path}") # Debug print
                    try:
                        with open(full_sql_path, 'r') as f:
                            sql_script = f.read()
                        cursor.execute(sql_script)
                        conn.commit()
                    except FileNotFoundError:
                        pass # Log this silently or with a proper logging mechanism
                    except sqlite3.OperationalError:
                        pass # Log this silently or with a proper logging mechanism
                    except Exception:
                        pass # Log this silently or with a proper logging mechanism



    def create_pearl_id(self, entity_type: str, attributes: dict = None, pearl_id: str = None, seed: str = None) -> str:
        """
        Generates a deterministic PEARL ID, calculates its 3D vector, and stores it.
        If pearl_id and seed are provided, they are used directly.

        Args:
            entity_type (str): The type of entity for which the PEARL ID is being created.
            attributes (dict, optional): Additional attributes for the PEARL ID. Defaults to None.
            pearl_id (str, optional): Pre-generated PEARL ID. If None, one will be generated.
            seed (str, optional): The seed string used to generate the PEARL ID. Required if pearl_id is provided.

        Returns:
            str: The newly created deterministic PEARL ID.
        """
        if pearl_id is None:
            if seed is None:
                # Generate a deterministic PEARL ID based on entity_type and current timestamp/randomness
                # For true determinism, a more robust seed generation strategy would be needed
                # that incorporates all relevant identity geometry components.
                seed = f"{entity_type}_{os.urandom(8).hex()}" # Using os.urandom for uniqueness for now
            pearl_id = seed_to_pearl_id(seed)

        # Calculate 3D vector coordinates
        x, y, z = pearl_id_to_vector(pearl_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO pearl_ids (id, entity_type, attributes, x, y, z) VALUES (?, ?, ?, ?, ?, ?);
                """, (pearl_id, entity_type, json.dumps(attributes) if attributes else "{}", x, y, z))
                conn.commit()
            except sqlite3.Error:
                conn.rollback()
        return pearl_id

    def add_crdt_log_entry(self, site_id: str, log_entry: str):
        """
        Adds a new entry to the CRDT log.

        Args:
            site_id (str): The identifier of the site/replica originating the log entry.
            log_entry (str): The content of the log entry.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO crdt_log (site_id, log_entry) VALUES (?, ?);
            """, (site_id, log_entry))
            # The with statement for sqlite3.Connection automatically commits on success
            # and rolls back on exception, so explicit conn.commit() is redundant here.

    def get_crdt_log_entries(self, limit: int = 10) -> list[dict]:
        """
        Retrieves the latest CRDT log entries.

        Args:
            limit (int): The maximum number of log entries to retrieve.

        Returns:
            list[dict]: A list of dictionaries, each representing a CRDT log entry.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, site_id, log_entry
                FROM crdt_log
                ORDER BY timestamp DESC
                LIMIT ?;
            """, (limit,))
            rows = cursor.fetchall()
            return [{"id": row[0], "timestamp": row[1], "site_id": row[2], "log_entry": row[3]} for row in rows]

    def increment_crdt_counter(self, counter_name: str, site_id: str, value: int = 1):
        """
        Increments a CRDT counter for a given site.

        Args:
            counter_name (str): The name of the counter.
            site_id (str): The identifier of the site/replica.
            value (int): The amount to increment by (default is 1).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO crdt_counter (counter_name, site_id, increments, decrements)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(counter_name, site_id) DO UPDATE SET increments = increments + ?;
            """, (counter_name, site_id, value, value))
            conn.commit()

    def decrement_crdt_counter(self, counter_name: str, site_id: str, value: int = 1):
        """
        Decrements a CRDT counter for a given site.

        Args:
            counter_name (str): The name of the counter.
            site_id (str): The identifier of the site/replica.
            value (int): The amount to decrement by (default is 1).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO crdt_counter (counter_name, site_id, increments, decrements)
                VALUES (?, ?, 0, ?)
                ON CONFLICT(counter_name, site_id) DO UPDATE SET decrements = decrements + ?;
            """, (counter_name, site_id, value, value))
            conn.commit()

    def get_crdt_counter_value(self, counter_name: str) -> int:
        """
        Gets the current value of a CRDT counter by summing increments and decrements across all sites.

        Args:
            counter_name (str): The name of the counter.

        Returns:
            int: The aggregated value of the counter.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(increments), SUM(decrements)
                FROM crdt_counter
                WHERE counter_name = ?;
            """, (counter_name,))
            result = cursor.fetchone()
            if result and result[0] is not None and result[1] is not None:
                return result[0] - result[1]
            return 0

    def add_transaction(self, pearl_id: str, item: str, cost: float, payment: str, sku: str = None):
        """
        Adds a new transaction to the database.

        Args:
            pearl_id (str): The PEARL ID associated with the transaction.
            item (str): The name of the item.
            cost (float): The cost of the item.
            payment (str): The payment method used.
            sku (str, optional): The SKU of the item. Defaults to None.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (pearl_id, item, cost, payment, sku) VALUES (?, ?, ?, ?, ?);
            """, (pearl_id, item, cost, payment, sku))
            conn.commit()

    def create_task(self, job_id: int, task_name: str, description: str = None, status: str = 'pending', assigned_to: str = None, due_date: str = None) -> int:
        """
        Creates a new task and associates it with a job.

        Args:
            job_id (int): The ID of the job this task belongs to.
            task_name (str): The name of the task.
            description (str, optional): A description of the task. Defaults to None.
            status (str, optional): The current status of the task (e.g., 'pending', 'in_progress', 'completed'). Defaults to 'pending'.
            assigned_to (str, optional): The person assigned to the task. Defaults to None.
            due_date (str, optional): The due date of the task. Defaults to None.

        Returns:
            int: The ID of the newly created task.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (job_id, task_name, description, status, assigned_to, due_date)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (job_id, task_name, description, status, assigned_to, due_date))
            conn.commit()
            return cursor.lastrowid

    def get_task(self, task_id: int) -> dict | None:
        """
        Retrieves a single task by its ID.

        Args:
            task_id (int): The ID of the task to retrieve.

        Returns:
            dict | None: A dictionary representing the task, or None if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, job_id, task_name, description, status, assigned_to, due_date, created_at FROM tasks WHERE id = ?;", (task_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_tasks_by_job_id(self, job_id: int) -> list[dict]:
        """
        Retrieves all tasks associated with a given job ID.

        Args:
            job_id (int): The ID of the job.

        Returns:
            list[dict]: A list of dictionaries, each representing a task.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, job_id, task_name, description, status, assigned_to, due_date, created_at FROM tasks WHERE job_id = ? ORDER BY created_at DESC;", (job_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_task(self, task_id: int, task_name: str = None, description: str = None, status: str = None, assigned_to: str = None, due_date: str = None):
        """
        Updates an existing task.

        Args:
            task_id (int): The ID of the task to update.
            task_name (str, optional): The new name of the task. Defaults to None.
            description (str, optional): The new description of the task. Defaults to None.
            status (str, optional): The new status of the task. Defaults to None.
            assigned_to (str, optional): The new person assigned to the task. Defaults to None.
            due_date (str, optional): The new due date of the task. Defaults to None.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if task_name is not None:
                updates.append("task_name = ?")
                params.append(task_name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if assigned_to is not None:
                updates.append("assigned_to = ?")
                params.append(assigned_to)
            if due_date is not None:
                updates.append("due_date = ?")
                params.append(due_date)

            if not updates:
                return # Nothing to update

            sql_query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?;"
            params.append(task_id)
            cursor.execute(sql_query, tuple(params))
            conn.commit()

    def delete_task(self, task_id: int):
        """
        Deletes a task by its ID.

        Args:
            task_id (int): The ID of the task to delete.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
            conn.commit()

    def get_pearl_id(self, pearl_id: str) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, entity_type, attributes FROM pearl_ids WHERE id = ?;
            """, (pearl_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "entity_type": row[1], "attributes": json.loads(row[2])}
            return None

    def get_transactions_by_pearl_id(self, pearl_id: str) -> list[dict]:
        """
        Retrieves all transactions associated with a given PEARL ID.

        Args:
            pearl_id (str): The PEARL ID to retrieve transactions for.

        Returns:
            list[dict]: A list of dictionaries, each representing a transaction.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, pearl_id, item, cost, payment, sku, timestamp FROM transactions WHERE pearl_id = ?;
            """, (pearl_id,))
            rows = cursor.fetchall()
            transactions = []
            for row in rows:
                transactions.append({
                    "id": row[0],
                    "pearl_id": row[1],
                    "item": row[2],
                    "cost": row[3],
                    "payment": row[4],
                    "sku": row[5],
                    "timestamp": row[6]
                })
            return transactions

    def update_pearl_id(self, pearl_id: str, entity_type: str = None, attributes: dict = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if entity_type:
                updates.append("entity_type = ?")
                params.append(entity_type)
            if attributes:
                updates.append("attributes = ?")
                params.append(json.dumps(attributes))

            if not updates:
                return # Nothing to update

            sql_query = f"UPDATE pearl_ids SET {', '.join(updates)} WHERE id = ?;"
            params.append(pearl_id)
            cursor.execute(sql_query, tuple(params))
            conn.commit()

    def delete_pearl_id(self, pearl_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pearl_ids WHERE id = ?;", (pearl_id,))
            conn.commit()

    def update_pearl_id_status(self, pearl_id: str, status: str):
        """
        Updates the status of a given PEARL ID.

        Args:
            pearl_id (str): The PEARL ID to update.
            status (str): The new status (e.g., 'active', 'finished', 'deleted').
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pearl_ids SET status = ? WHERE id = ?;
            """, (status, pearl_id))
            conn.commit()

    def get_pearl_id_status(self, pearl_id: str) -> str | None:
        """
        Retrieves the status of a given PEARL ID.

        Args:
            pearl_id (str): The PEARL ID to retrieve the status for.

        Returns:
            str | None: The status of the PEARL ID, or None if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status FROM pearl_ids WHERE id = ?;
            """, (pearl_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def execute_ddl(self, ddl_query: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(ddl_query)
            conn.commit()
            print(f"DDL executed: {ddl_query}")

    def execute_query(self, query: str, params: tuple = ()) -> tuple[list[sqlite3.Row], list[str]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

            if cursor.description: # Check if there is a result set
                results = cursor.fetchall()
                column_names = [description[0] for description in cursor.description]
                return results, column_names
            else:
                return [], [] # Return empty lists for non-SELECT queries

    def log_semantic_event(self, pearl_id: str, log_entry: str):
        """
        Logs a semantic event associated with a PEARL ID.

        Args:
            pearl_id (str): The PEARL ID to associate the log entry with.
            log_entry (str): The content of the semantic log entry.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO semantic_logs (pearl_id, log_entry) VALUES (?, ?);
            """, (pearl_id, log_entry))
            conn.commit()

    def semantic_search(self, query_text: str):
        """
        Performs a basic keyword-based semantic search on semantic logs.
        This is a placeholder for more advanced semantic similarity algorithms.

        Args:
            query_text (str): The text to search for.

        Returns:
            list: A list of matching semantic log entries.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Using LIKE for a simple keyword search
            cursor.execute("""
                SELECT id, pearl_id, timestamp, log_entry
                FROM semantic_logs
                WHERE log_entry LIKE ?;
            """, (f"%{query_text}%",))
            return cursor.fetchall()

    def get_table_columns(self, table_name: str) -> list[str]:
        """
        Retrieves the column names for a given table.

        Args:
            table_name (str): The name of the table.

        Returns:
            list[str]: A list of column names for the table.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            return [col[1] for col in columns_info]

    def get_table_column_info(self, table_name: str) -> list[tuple]:
        """
        Retrieves detailed column information for a given table.

        Args:
            table_name (str): The name of the table.

        Returns:
            list[tuple]: A list of tuples, each containing (cid, name, type, notnull, dflt_value, pk).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            return cursor.fetchall()

    def get_distinct_column_values(self, table_name: str, column_name: str, limit: int = 1000) -> list[any]:
        """
        Retrieves distinct values for a specified column in a given table.

        Args:
            table_name (str): The name of the table.
            column_name (str): The name of the column.
            limit (int): The maximum number of distinct values to retrieve.

        Returns:
            list[any]: A list of distinct values from the column.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name} LIMIT ?;", (limit,))
                values = cursor.fetchall()
                return [value[0] for value in values]
            except sqlite3.OperationalError as e:
                print(f"Error fetching distinct values for {table_name}.{column_name}: {e}")
                return []

    def get_all_table_names(self) -> list[str]:
        """
        Retrieves the names of all tables in the database.

        Returns:
            list[str]: A list of all table names.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            return [table[0] for table in tables]

    def get_table_row_count(self, table_name: str, pearl_id: str = None) -> int:
        """
        Retrieves the number of rows in a given table, optionally filtered by PEARL ID.

        Args:
            table_name (str): The name of the table.
            pearl_id (str, optional): The PEARL ID to filter by. If None, counts all rows.

        Returns:
            int: The number of rows in the table.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = f"SELECT COUNT(*) FROM {table_name}"
            params = []
            if pearl_id:
                query += " WHERE pearl_id = ?"
                params.append(pearl_id)
            cursor.execute(query, tuple(params))
            count = cursor.fetchone()[0]
            return count

    def get_folder_structure_report(self, pearl_id: str = None) -> dict:
        """
        Generates a hierarchical report of PEARL IDs, their associated tables,
        and the row count for each table, optionally filtered by a specific PEARL ID.

        Args:
            pearl_id (str, optional): If provided, the report will be filtered to this PEARL ID.
                                      Otherwise, it will include all PEARL IDs.

        Returns:
            dict: A dictionary where keys are PEARL IDs and values are dictionaries
                  containing 'entity_type', 'attributes', and 'tables'.
                  'tables' is a list of dictionaries, each with 'name' and 'row_count'.
        """
        report = {}
        all_table_names = self.get_all_table_names()

        if pearl_id:
            pearl_ids_to_report = [self.get_pearl_id(pearl_id)]
        else:
            pearl_ids_to_report = self.get_all_pearl_ids()

        for pearl_id_info in pearl_ids_to_report:
            if pearl_id_info is None: # Skip if pearl_id was not found
                continue
            current_pearl_id = pearl_id_info["id"]
            report[current_pearl_id] = {
                "entity_type": pearl_id_info["entity_type"],
                "attributes": pearl_id_info["attributes"],
                "tables": []
            }
            for table_name in all_table_names:
                try:
                    row_count = self.get_table_row_count(table_name, pearl_id=current_pearl_id)
                    report[current_pearl_id]["tables"].append({
                        "name": table_name,
                        "row_count": row_count
                    })
                except sqlite3.OperationalError:
                    report[current_pearl_id]["tables"].append({
                        "name": table_name,
                        "row_count": 0
                    })
        return report

    def get_all_pearl_ids(self) -> list[dict]:
        """
        Retrieves all PEARL IDs and their associated entity_type, attributes, and 3D coordinates.

        Returns:
            list[dict]: A list of dictionaries, each representing a PEARL ID with its id, entity_type, attributes, x, y, and z.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, entity_type, attributes, x, y, z, status FROM pearl_ids;")
            rows = cursor.fetchall()
            return [{"id": row[0], "entity_type": row[1], "attributes": json.loads(row[2]), "x": row[3], "y": row[4], "z": row[5], "status": row[6] if row[6] else 'active'} for row in rows]

    def export_query_results(self, column_headers: list[str], results: list[tuple], file_path: str, format: str):
        """
        Exports query results to a specified file in the given format.

        Args:
            column_headers (list[str]): List of column headers for the results.
            results (list[tuple]): The query results as a list of tuples.
            file_path (str): The path to the output file.
            format (str): The export format ('json', 'csv', 'txt', 'pickle').
        """
        if format == 'json':
            data = []
            for row in results:
                data.append(dict(zip(column_headers, row)))
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        elif format == 'csv':
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(column_headers)
                writer.writerows(results)
        elif format == 'txt':
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(','.join(column_headers) + '\n')
                for row in results:
                    f.write(','.join(map(str, row)) + '\n')
        elif format == 'pickle':
            with open(file_path, 'wb') as f:
                pickle.dump({"headers": column_headers, "data": results}, f)
        else:
            raise ValueError(f"Unsupported export format: {format}")

