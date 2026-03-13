import sqlite3
import os
import pandas as pd
import streamlit as st
from typing import Optional, Union
from datetime import datetime, timedelta
from .query_builder import QueryBuilder
from ..seedtools.seedtools import seed_to_pearl_id
from App.src.core.database.pearl_qlite.pearl_qlite import PearlClient
from App.config.sql_categories import SQL_CATEGORIES


# ADD THIS PART:
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataAccess:
    """
    A Data Access Layer (DAL) for interacting with the SQLite database.
    This class handles loading SQL queries from external files, managing PEARL_ID context,
    and executing parameterized queries to ensure data isolation and security.
    """

    def __hash__(self):
        return hash((self.db_path, self.sql_dir, self.pearl_client))

    def __eq__(self, other):
        if not isinstance(other, DataAccess):
            return NotImplemented
        return (self.db_path == other.db_path and
                self.sql_dir == other.sql_dir and
                self.pearl_client == other.pearl_client)

    def __init__(self, db_path: str, sql_dir: str, pearl_client: PearlClient):
        """
        Initializes the DataAccess layer.

        Args:
            db_path (str): The absolute path to the SQLite database file.
            sql_dir (str): The absolute path to the directory containing SQL files.
            pearl_client (PearlClient): An instance of the PearlClient for direct DB operations.
        """
        self.db_path = db_path
        self.sql_dir = sql_dir
        self._pearl_id = None  # Stores the active PEARL_ID for data isolation

        self._active_group_id = None # Stores the active group_id for group-based filtering
        self.pearl_client = pearl_client

    def _load_sql_query(self, query_name: str) -> str:
        """
        Loads an SQL query from the specified file.

        Args:
            query_name (str): The name of the SQL file (e.g., "jobs_get_all.sql" or "alarms/insert_alarm.sql").
                              If a category prefix is used (e.g., "alarms/"), it must be one of the defined SQL_CATEGORIES.

        Returns:
            str: The content of the SQL query.

        Raises:
            FileNotFoundError: If the SQL file does not exist.
            ValueError: If the query_name uses an undefined category prefix.
        """
        # Validate category prefix if present
        parts = query_name.split(os.sep, 1) # Split only on the first separator
        if len(parts) > 1:
            category_prefix = parts[0]
            if category_prefix not in SQL_CATEGORIES:
                raise ValueError(f"Undefined SQL category '{category_prefix}' in query name '{query_name}'. "
                                 f"Allowed categories are: {', '.join(SQL_CATEGORIES)}")

        file_path = os.path.join(self.sql_dir, query_name)
        logger.debug(f"_load_sql_query - Attempting to load SQL from: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"SQL query file not found: {file_path}")
        with open(file_path, 'r') as f:
            sql_content = f.read()
            logger.debug(f"_load_sql_query - Loaded SQL content: {sql_content[:100]}...") # Print first 100 chars
            return sql_content

    def set_pearl_id(self, pearl_id: str):
        """
        Sets the active PEARL_ID for the current session.
        All subsequent database operations will implicitly use this PEARL_ID.

        Args:
            pearl_id (str): The PEARL_ID to set.
        """
        self._pearl_id = pearl_id

    def set_active_group_id(self, group_id: Optional[str]):
        """
        Sets the active group_id for the current session.
        If a group_id is set, all subsequent database operations will be filtered
        to include only PEARL_IDs belonging to this group.

        Args:
            group_id (Optional[str]): The group_id to set, or None to clear the active group.
        """
        self._active_group_id = group_id



    def execute_query(self, query_name: str, params: Optional[dict] = None) -> int:
        """
        Executes an SQL query (INSERT, UPDATE, DELETE).
        Automatically injects PEARL_ID if available and applicable.

        Args:
            query_name (str): The name of the SQL file containing the query.
            params (dict, optional): A dictionary of parameters for the query. Defaults to None.

        Returns:
            int: The number of rows affected by the query.

        Raises:
            ValueError: If PEARL_ID is required but not set for the operation.
        """
        sql = self._load_sql_query(query_name)
        current_params = params if params is not None else {}

        if self._pearl_id:
            current_params['pearl_id'] = self._pearl_id

        # Explicitly check for pearl_id if it's expected in the SQL
        if ':pearl_id' in sql and (current_params.get('pearl_id') is None or current_params.get('pearl_id') == ''):
            raise ValueError("PEARL_ID is required for this operation but was not provided or is None/empty.")

        conn = None
        try:
            conn = self.pearl_client._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, current_params)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise RuntimeError(f"Database error during query execution: {e}")
        finally:
            pass # Connection is managed by PearlClient/fixture

    def _infer_column_types_from_dataframe(self, df: pd.DataFrame) -> dict[str, str]:
        """
        Infers SQL column types (TEXT, INTEGER, REAL) from a pandas DataFrame.
        """
        column_types = {}
        for col in df.columns:
            # Default to TEXT
            sql_type = "TEXT"
            # Check for numeric types
            if pd.api.types.is_integer_dtype(df[col]):
                sql_type = "INTEGER"
            elif pd.api.types.is_float_dtype(df[col]):
                sql_type = "REAL"
            # Add more type inference logic if needed (e.g., dates)
            column_types[col] = sql_type
        return column_types

    def import_csv_to_table(self, df: pd.DataFrame, table_name: str, import_mode: str):
        """
        Imports data from a pandas DataFrame into a specified table.
        If the table does not exist, it attempts to create it based on DataFrame columns
        and inferred column types.

        Args:
            df (pd.DataFrame): The DataFrame containing the data to import.
            table_name (str): The name of the table to import data into.
            import_mode (str): "Insert New Records" or "Update Existing Records".
        """
        if df.empty:
            st.warning("The uploaded CSV is empty. No data to import.")
            return

        db_columns = self.get_table_columns(table_name)
        df_columns = df.columns.tolist()

        # --- Table Creation Logic (if table does not exist) ---
        if not db_columns:
            st.info(f"Table '{table_name}' not found. Attempting to create it based on CSV headers.")
            column_definitions = []
            inferred_types = self._infer_column_types_from_dataframe(df)

            # Determine if pearl_id or autoincrement id should be added
            add_pearl_id_column = False
            add_autoincrement_id_column = False

            # For simplicity in Streamlit, we'll assume if 'pearl_id' is not in CSV, we add it
            # and make it PRIMARY KEY. If 'id' is not in CSV, we add 'id INTEGER PRIMARY KEY AUTOINCREMENT'.
            # This can be made more interactive with user prompts if needed.
            if 'pearl_id' not in df_columns:
                add_pearl_id_column = True
            elif 'id' not in df_columns:
                add_autoincrement_id_column = True

            for col in df_columns:
                sql_type = inferred_types.get(col, "TEXT")
                definition = f"{col} {sql_type}"
                column_definitions.append(definition)

            # Apply primary key logic
            if add_pearl_id_column:
                column_definitions.append("pearl_id TEXT PRIMARY KEY")
            elif add_autoincrement_id_column:
                column_definitions.append("id INTEGER PRIMARY KEY AUTOINCREMENT")

            create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_definitions)});"
            try:
                self._execute_raw_sql(create_table_sql) # Use _execute_raw_sql for DDL
                st.success(f"Table '{table_name}' created successfully.")
                db_columns = self.get_table_columns(table_name) # Re-fetch columns
            except Exception as e:
                st.error(f"Error creating table '{table_name}': {e}")
                return

        if not db_columns:
            st.error(f"Could not determine columns for table '{table_name}'. Aborting import.")
            return

        # --- Data Import Logic ---
        common_columns = [col for col in df_columns if col in db_columns]
        if not common_columns:
            st.error(f"No common columns found between CSV headers ({df_columns}) and table '{table_name}' columns ({db_columns}). Aborting import.")
            return

        # Prepare the INSERT OR REPLACE statement
        # This assumes that the table has a PRIMARY KEY or UNIQUE constraint
        # to identify rows for replacement.
        placeholders = ', '.join(['?' for _ in common_columns])
        columns_str = ', '.join(common_columns)

        insert_pearl_id_dynamically = False
        if 'pearl_id' in db_columns and 'pearl_id' not in common_columns:
            insert_pearl_id_dynamically = True
            columns_str = 'pearl_id, ' + columns_str
            placeholders = '?, ' + placeholders

        sql = f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders});"

        imported_rows = 0
        for index, row in df.iterrows():
            params = []
            if insert_pearl_id_dynamically:
                seed_string = ','.join(f"{col}:{row[col]}" for col in df_columns)
                params.append(seed_to_pearl_id(seed_string))

            for col in common_columns:
                value = row[col]
                # Basic type conversion (pandas often handles this, but explicit check)
                if pd.isna(value):
                    params.append(None)
                else:
                    params.append(value)

            try:
                self._execute_raw_sql(sql, tuple(params))
                imported_rows += 1
            except Exception as e:
                st.error(f"Error importing row {index + 1} into '{table_name}': {e}. Row data: {row.to_dict()}")
                # Continue to next row or break based on desired error handling

        st.success(f"Successfully imported {imported_rows} rows into table '{table_name}'.")


    def create_table(self, table_name: str, column_definitions: dict[str, str]):
        """
        Creates a new table in the database with the specified columns.

        Args:
            table_name (str): The name of the table to create.
            column_definitions (dict[str, str]): A dictionary where keys are column names
                                                  and values are their SQL data types (e.g., "TEXT", "INTEGER", "REAL").
                                                  A 'pearl_id TEXT PRIMARY KEY' column will be automatically added.
        """
        if not table_name:
            raise ValueError("Table name cannot be empty.")
        if not column_definitions:
            raise ValueError("Column definitions cannot be empty.")

        # Ensure pearl_id is always present and is the primary key
        if "pearl_id" not in column_definitions:
            column_definitions["pearl_id"] = "TEXT PRIMARY KEY"
        else:
            # If pearl_id is provided, ensure it's TEXT PRIMARY KEY
            column_definitions["pearl_id"] = "TEXT PRIMARY KEY"

        cols_sql = []
        for col_name, col_type in column_definitions.items():
            cols_sql.append(f"{col_name} {col_type}")

        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(cols_sql)});"

        try:
            self._execute_raw_sql(create_table_sql) # Use _execute_raw_sql for DDL
            st.success(f"Table '{table_name}' created successfully.")
        except sqlite3.Error as e:
            st.error(f"Error creating table '{table_name}': {e}")
            raise


    def execute_query_builder(self, query_builder: 'QueryBuilder') -> int:
        """
        Executes an SQL query constructed by a QueryBuilder object (INSERT, UPDATE, DELETE).
        Automatically injects PEARL_ID if available and applicable.

        Args:
            query_builder (QueryBuilder): An instance of QueryBuilder containing the query definition.

        Returns:
            int: The number of rows affected by the query.
        """
        if query_builder._insert_data:
            sql, params = query_builder.build_insert()
        elif query_builder._update_data:
            sql, params = query_builder.build_update()
        elif query_builder._is_delete:
            sql, params = query_builder.build_delete()
        else:
            raise ValueError("QueryBuilder must be configured for INSERT, UPDATE, or DELETE operation.")

        return self._execute_raw_sql(sql, params)

    def fetch_query_builder(self, query_builder: 'QueryBuilder') -> list[sqlite3.Row]:
        """
        Fetches all rows from a SELECT query constructed by a QueryBuilder object.
        Automatically injects PEARL_ID if available and applicable.

        Args:
            query_builder (QueryBuilder): An instance of QueryBuilder containing the query definition.

        Returns:
            list[sqlite3.Row]: A list of rows, where each row is an sqlite3.Row object.
        """
        sql, params = query_builder.build()
        return self._fetch_raw_sql(sql, params)

    def fetch_query_builder_one(self, query_builder: 'QueryBuilder') -> sqlite3.Row | None:
        """
        Fetches a single row from a SELECT query constructed by a QueryBuilder object.
        Automatically injects PEARL_ID if available and applicable.

        Args:
            query_builder (QueryBuilder): An instance of QueryBuilder containing the query definition.

        Returns:
            sqlite3.Row | None: A single row as an sqlite3.Row object, or None if no row is found.
        """
        sql, params = query_builder.build()
        return self._fetch_raw_sql_one(sql, params)

    def execute_script(self, script_name: str):
        """
        Executes an SQL script from a file, typically for DDL operations like CREATE TABLE.
        This method does not inject PEARL_ID.

        Args:
            script_name (str): The name of the SQL file containing the script (e.g., "jobs/create_jobs_table.sql").
        """
        sql = self._load_sql_query(script_name)
        conn = None
        try:
            conn = self.pearl_client._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise RuntimeError(f"Database error during script execution ({script_name}): {e}")
        finally:
            if conn:
                conn.close()

    def get_all_table_names(self) -> list[str]:
        """
        Retrieves the names of all tables in the database.

        Returns:
            list[str]: A list of all table names.
        """
        conn = None
        try:
            conn = self.pearl_client._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [row['name'] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error retrieving table names: {e}")
        finally:
            if conn:
                conn.close()

    def get_all_distinct_pearl_ids_from_all_tables(self) -> list[str]:
        """
        Retrieves all distinct PEARL IDs from all tables in the database.

        Returns:
            list[str]: A list of all distinct PEARL IDs.
        """
        all_pearl_ids = set()
        table_names = self.get_all_table_names()

        conn = None
        try:
            conn = self.pearl_client._get_connection()
            cursor = conn.cursor()
            for table_name in table_names:
                # Special handling for the 'pearl_ids' table where the ID column is named 'id'
                if table_name == 'pearl_ids':
                    cursor.execute(f"SELECT DISTINCT id FROM {table_name} WHERE id IS NOT NULL;")
                    for row in cursor.fetchall():
                        all_pearl_ids.add(row['id'])
                else:
                    # Check if the table has a 'pearl_id' column for other tables
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    if any(col['name'] == 'pearl_id' for col in columns):
                        cursor.execute(f"SELECT DISTINCT pearl_id FROM {table_name} WHERE pearl_id IS NOT NULL;")
                        for row in cursor.fetchall():
                            all_pearl_ids.add(row['pearl_id'])
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error retrieving distinct PEARL IDs: {e}")
        finally:
            if conn:
                conn.close()
        return sorted(list(all_pearl_ids))

    def create_pearl_id_group(self, group_id: str, group_name: str, description: Optional[str] = None, master_key_id: Optional[str] = None):
        """
        Creates a new PEARL ID group.

        Args:
            group_id (str): A unique identifier for the group.
            group_name (str): A human-readable name for the group.
            description (Optional[str]): An optional description for the group.
            master_key_id (Optional[str]): The PEARL ID of the master key associated with this group.
        """
        sql = "INSERT INTO pearl_id_groups (group_id, group_name, description, master_key_id) VALUES (:group_id, :group_name, :description, :master_key_id);"
        params = {
            "group_id": group_id,
            "group_name": group_name,
            "description": description,
            "master_key_id": master_key_id
        }
        self._execute_raw_sql(sql, params)

    def get_all_pearl_id_groups(self) -> list[sqlite3.Row]:
        """
        Retrieves all PEARL ID groups.

        Returns:
            list[sqlite3.Row]: A list of all PEARL ID groups.
        """
        sql = "SELECT group_id, group_name, description, master_key_id FROM pearl_id_groups;"
        rows = self._fetch_raw_sql(sql)
        return [dict(row) for row in rows]

    def create_alarm(self, job_id: int, pearl_id: str, alarm_time: str, message: str, recurrence: str, is_alarm_active: bool):
        """
        Creates a new alarm record in the database.

        Args:
            job_id (int): The ID of the job associated with the alarm.
            pearl_id (str): The PEARL ID associated with the alarm.
            alarm_time (str): The scheduled time for the alarm (YYYY-MM-DD HH:MM:SS).
            message (str): The alarm message.
            recurrence (str): The recurrence pattern of the alarm (e.g., 'once', 'daily', 'weekly').
            is_alarm_active (bool): Whether the alarm is active.
        """
        sql = """
        INSERT INTO Alarms (job_id, pearl_id, alarm_time, message, recurrence, is_active)
        VALUES (:job_id, :pearl_id, :alarm_time, :message, :recurrence, :is_active)
        """
        params = {
            "job_id": job_id,
            "pearl_id": pearl_id,
            "alarm_time": alarm_time,
            "message": message,
            "recurrence": recurrence,
            "is_active": is_alarm_active
        }
        self._execute_raw_sql(sql, params)

    def update_alarm(self, alarm_id: int, alarm_time: str, message: str, recurrence: str, is_alarm_active: bool):
        """
        Updates an existing alarm record in the database.

        Args:
            alarm_id (int): The ID of the alarm to update.
            alarm_time (str): The scheduled time for the alarm (YYYY-MM-DD HH:MM:SS).
            message (str): The alarm message.
            recurrence (str): The recurrence pattern of the alarm (e.g., 'once', 'daily', 'weekly').
            is_alarm_active (bool): Whether the alarm is active.
        """
        sql = """
        UPDATE Alarms
        SET alarm_time = :alarm_time,
            message = :message,
            recurrence = :recurrence,
            is_active = :is_active
        WHERE alarm_id = :alarm_id
        """
        params = {
            "alarm_id": alarm_id,
            "alarm_time": alarm_time,
            "message": message,
            "recurrence": recurrence,
            "is_active": is_alarm_active
        }
        self._execute_raw_sql(sql, params)

    def delete_alarm(self, alarm_id: int, pearl_id: str):
        """
        Deletes an alarm record from the database.

        Args:
            alarm_id (int): The ID of the alarm to delete.
            pearl_id (str): The PEARL ID associated with the alarm.
        """
        sql = "DELETE FROM Alarms WHERE alarm_id = :alarm_id AND pearl_id = :pearl_id"
        params = {"alarm_id": alarm_id, "pearl_id": pearl_id}
        self._execute_raw_sql(sql, params)

    def get_due_alarms(self, current_time: str) -> list[sqlite3.Row]:
        """
        Retrieves all active alarms that are due at or before the current_time,
        considering their recurrence pattern, snooze status, and dismissal status.

        Args:
            current_time (str): The current time in "YYYY-MM-DD HH:MM:SS" format.

        Returns:
            list[sqlite3.Row]: A list of due alarms.
        """
        sql = """
            SELECT *
            FROM Alarms
            WHERE is_active = 1
              AND (snooze_until IS NULL OR snooze_until <= :current_time)
              AND dismissed_at IS NULL
              AND start_date <= DATE(:current_time)
              AND (end_date IS NULL OR end_date >= DATE(:current_time))
              AND (
                    (recurrence = 'once' AND alarm_time <= :current_time)
                    OR
                    (recurrence = 'daily' AND STRFTIME('%H:%M', alarm_time) <= STRFTIME('%H:%M', :current_time))
                    OR
                    (recurrence = 'weekly' AND STRFTIME('%w', alarm_time) = STRFTIME('%w', :current_time) AND STRFTIME('%H:%M', alarm_time) <= STRFTIME('%H:%M', :current_time))
                    OR
                    (recurrence = 'monthly' AND STRFTIME('%d', alarm_time) = STRFTIME('%d', :current_time) AND STRFTIME('%H:%M', alarm_time) <= STRFTIME('%H:%M', :current_time))
              )
        """
        return self._fetch_raw_sql(sql, {"current_time": current_time})

    def add_pearl_id_to_group(self, group_id: str, pearl_id: str):
        """
        Adds a PEARL ID to a specified group.

        Args:
            group_id (str): The ID of the group.
            pearl_id (str): The PEARL ID to add.
        """
        sql = "INSERT OR IGNORE INTO group_members (group_id, pearl_id) VALUES (:group_id, :pearl_id);"
        params = {"group_id": group_id, "pearl_id": pearl_id}
        self._execute_raw_sql(sql, params)

    def remove_pearl_id_from_group(self, group_id: str, pearl_id: str):
        """
        Removes a PEARL ID from a specified group.

        Args:
            group_id (str): The ID of the group.
            pearl_id (str): The PEARL ID to remove.
        """
        sql = "DELETE FROM group_members WHERE group_id = :group_id AND pearl_id = :pearl_id;"
        params = {"group_id": group_id, "pearl_id": pearl_id}
        self._execute_raw_sql(sql, params)

    def dismiss_alarm(self, alarm_id: str):
        """
        Dismisses an alarm by setting its dismissed_at timestamp.

        Args:
            alarm_id (str): The ID of the alarm to dismiss.
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = "UPDATE Alarms SET dismissed_at = :current_time WHERE alarm_id = :alarm_id;"
        params = {"current_time": current_time, "alarm_id": alarm_id}
        self._execute_raw_sql(sql, params)

    def snooze_alarm(self, alarm_id: str, snooze_duration_minutes: int):
        """
        Snoozes an alarm by updating its snooze_until time.

        Args:
            alarm_id (str): The ID of the alarm to snooze.
            snooze_duration_minutes (int): The number of minutes to snooze the alarm.
        """
        # First, get the current alarm_time
        sql_select = "SELECT alarm_time, snooze_until FROM Alarms WHERE alarm_id = :alarm_id;"
        result = self._fetch_raw_sql_one(sql_select, {"alarm_id": alarm_id})

        if result:
            current_time = datetime.now()
            new_snooze_until = current_time + timedelta(minutes=snooze_duration_minutes)
            new_snooze_until_str = new_snooze_until.strftime("%Y-%m-%d %H:%M:%S")

            sql_update = "UPDATE Alarms SET snooze_until = :new_snooze_until WHERE alarm_id = :alarm_id;"
            params_update = {"new_snooze_until": new_snooze_until_str, "alarm_id": alarm_id}
            self._execute_raw_sql(sql_update, params_update)
        else:
            raise ValueError(f"Alarm with ID {alarm_id} not found.")

    def get_pearl_ids_in_group(self, group_id: str) -> list[str]:
        """
        Retrieves all PEARL IDs belonging to a specified group.

        Args:
            group_id (str): The ID of the group.

        Returns:
            list[str]: A list of PEARL IDs in the group.
        """
        sql = "SELECT pearl_id FROM group_members WHERE group_id = :group_id;"
        rows = self._fetch_raw_sql(sql, {"group_id": group_id})
        return [row['pearl_id'] for row in rows]



    def get_alarm_by_id(self, alarm_id: int, pearl_id: str) -> Optional[sqlite3.Row]:
        """
        Retrieves an alarm by its ID and PEARL ID.

        Args:
            alarm_id (int): The ID of the alarm.
            pearl_id (str): The PEARL ID associated with the alarm.

        Returns:
            Optional[sqlite3.Row]: The alarm row, or None if not found.
        """
        sql = self._load_sql_query("alarms/get_alarm_by_id.sql")
        params = {"alarm_id": alarm_id, "pearl_id": pearl_id}
        return self._fetch_raw_sql_one(sql, params)

    def get_all_alarms_for_job(self, job_id: int, pearl_id: str) -> list[sqlite3.Row]:
        """
        Retrieves all alarms associated with a specific job ID and PEARL ID.

        Args:
            job_id (int): The ID of the job.
            pearl_id (str): The PEARL ID associated with the alarms.

        Returns:
            list[sqlite3.Row]: A list of alarm rows.
        """
        sql = self._load_sql_query("alarms/get_all_alarms_for_job.sql")
        params = {"job_id": job_id, "pearl_id": pearl_id}
        return self._fetch_raw_sql(sql, params)

    def update_alarm(self, alarm_id: int, pearl_id: str, alarm_time: str, message: Optional[str] = None, recurrence: str = 'once', start_date: Optional[str] = None, end_date: Optional[str] = None, snooze_until: Optional[str] = None, dismissed_at: Optional[str] = None, is_active: bool = True) -> int:
        """
        Updates an existing alarm.

        Args:
            alarm_id (int): The ID of the alarm to update.
            pearl_id (str): The PEARL ID associated with the alarm.
            alarm_time (str): The new time the alarm is set for.
            message (Optional[str]): The new message for the alarm.
            recurrence (str): The new recurrence pattern for the alarm.
            start_date (Optional[str]): The start date for the alarm's recurrence.
            end_date (Optional[str]): The end date for the alarm's recurrence.
            snooze_until (Optional[str]): The time until which the alarm is snoozed.
            dismissed_at (Optional[str]): The time at which the alarm was dismissed.
            is_active (bool): The new active status for the alarm.

        Returns:
            int: The number of rows affected (should be 1 if successful).
        """
        sql = self._load_sql_query("alarms/update_alarm.sql")
        params = {
            "alarm_id": alarm_id,
            "pearl_id": pearl_id,
            "alarm_time": alarm_time,
            "message": message,
            "recurrence": recurrence,
            "start_date": start_date,
            "end_date": end_date,
            "snooze_until": snooze_until,
            "dismissed_at": dismissed_at,
            "is_active": int(is_active)
        }
        return self._execute_raw_sql(sql, params)




    def delete_alarm(self, alarm_id: int, pearl_id: str) -> int:
        """
        Deletes an alarm by its ID and PEARL ID.

        Args:
            alarm_id (int): The ID of the alarm to delete.
            pearl_id (str): The PEARL ID associated with the alarm.

        Returns:
            int: The number of rows affected (should be 1 if successful).
        """
        sql = self._load_sql_query("alarms/delete_alarm.sql")
        params = {"alarm_id": alarm_id, "pearl_id": pearl_id}
        return self._execute_raw_sql(sql, params)

    def _fetch_raw_sql(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> list[sqlite3.Row]:
        try:
            if params:
                return self.pearl_client.fetch_query_raw(sql, params)
            else:
                return self.pearl_client.fetch_query_raw(sql)
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error during raw fetch_all: {e}")

    def _execute_raw_sql(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> int:
        """
        Executes a raw SQL query (INSERT, UPDATE, DELETE, DDL) using the PearlClient.

        Args:
            sql (str): The SQL query string.
            params (Optional[Union[tuple, dict]]): Parameters for the query. Can be a tuple for
                                                    positional parameters or a dictionary for named parameters.

        Returns:
            int: The number of rows affected by the query.

        Raises:
            RuntimeError: If a database error occurs during execution.
        """
        try:
            if params:
                return self.pearl_client.execute_query_raw(sql, params)
            else:
                return self.pearl_client.execute_query_raw(sql)
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error during raw execute: {e}")

    def fetch_all(self, query_name: str, params: Optional[dict] = None) -> list[sqlite3.Row]:
        """
        Fetches all rows from a SELECT query loaded from a file.
        Automatically injects PEARL_ID if available and applicable.

        Args:
            query_name (str): The name of the SQL file containing the query.
            params (dict, optional): A dictionary of parameters for the query. Defaults to None.

        Returns:
            list[sqlite3.Row]: A list of rows, where each row is an sqlite3.Row object.

        Raises:
            ValueError: If PEARL_ID is required but not set for the operation.
        """
        sql = self._load_sql_query(query_name)
        return self._fetch_raw_sql(sql, params)

    def _fetch_raw_sql(self, sql: str, params: Optional[Union[tuple, dict]] = None) -> list[sqlite3.Row]:
        try:
            if params:
                logger.debug(f"DataAccess._fetch_raw_sql - Type of params before passing to pearl_client: {type(params)}")
                logger.debug(f"DataAccess._fetch_raw_sql - Value of params before passing to pearl_client: {params}")
                return self.pearl_client.fetch_query_raw(sql, params)
            else:
                return self.pearl_client.fetch_query_raw(sql)
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error during raw fetch_all: {e}")

    def fetch_one(self, query_name: str, params: Optional[dict] = None) -> sqlite3.Row | None:
        """
        Fetches a single row from a SELECT query loaded from a file.
        Automatically injects PEARL_ID if available and applicable.

        Args:
            query_name (str): The name of the SQL file containing the query.
            params (dict, optional): A dictionary of parameters for the query. Defaults to None.

        Returns:
            sqlite3.Row | None: A single row as an sqlite3.Row object, or None if no row is found.

        Raises:
            ValueError: If PEARL_ID is required but not set for the operation.
        """
        sql = self._load_sql_query(query_name)
        return self._fetch_raw_sql_one(sql, params)

    def _fetch_raw_sql_one(self, sql: str, params: Optional[Union[dict, tuple]] = None) -> sqlite3.Row | None:
        """
        Fetches a single row from a raw SELECT SQL query directly.
        Automatically injects PEARL_ID if available and applicable.
        This method is intended for internal use by query builders or advanced scenarios.

        Args:
            sql (str): The raw SQL string to execute.
            params (dict, optional): A dictionary of parameters for the query. Defaults to None.

        Returns:
            sqlite3.Row | None: A single row as an sqlite3.Row object, or None if no row is found.

        Raises:
            ValueError: If PEARL_ID is required but not set for the operation.
        """
        current_params = params if params is not None else {}
        modified_sql = sql

        # If an active PEARL_ID is set, add it to parameters
        if self._pearl_id:
            current_params['pearl_id'] = self._pearl_id

        # If an active group is set, filter by PEARL IDs in that group
        if self._active_group_id:
            pearl_ids_in_group = self.get_pearl_ids_in_group(self._active_group_id)
            if not pearl_ids_in_group:
                return None # No PEARL IDs in the group, so no results

            # Generate parameter names for the IN clause
            in_clause_params = {f"group_pearl_id_{i}": pid for i, pid in enumerate(pearl_ids_in_group)}
            in_clause_sql = ", ".join(f":{key}" for key in in_clause_params.keys())

            # Append the WHERE clause to the SQL query
            if "WHERE" in modified_sql.upper():
                modified_sql += f" AND pearl_id IN ({in_clause_sql})"
            else:
                modified_sql += f" WHERE pearl_id IN ({in_clause_sql})"
            current_params.update(in_clause_params)

        conn = None
        try:
            conn = self.pearl_client._get_connection()
            cursor = conn.cursor()
            cursor.execute(modified_sql, current_params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error during raw fetch_one: {e}")
        finally:
            pass # Connection is managed by PearlClient/fixture

    def get_table_columns(self, table_name: str) -> list[str]:
        """
        Retrieves the column names for a given table.

        Args:
            table_name (str): The name of the table.

        Returns:
            list[str]: A list of column names.
        """
        conn = None
        try:
            conn = self.pearl_client._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [row['name'] for row in cursor.fetchall()]
            return columns
        except sqlite3.Error as e:
            # If table does not exist, PRAGMA will return an empty result set, not an error.
            # So, this error handling is for other potential DB errors.
            raise RuntimeError(f"Database error during get_table_columns: {e}")
        finally:
            pass # Connection is managed by PearlClient/fixture

    def delete_all_user_data(self, pearl_id: str):
        """
        Deletes all data associated with a specific PEARL_ID from all relevant tables.

        Args:
            pearl_id (str): The PEARL_ID of the user whose data is to be deleted.
        """
        table_names = self.get_all_table_names()
        for table_name in table_names:
            if table_name.startswith('sqlite_'):
                continue  # Skip internal SQLite tables

            columns = self.get_table_columns(table_name)
            if 'pearl_id' in columns:
                try:
                    sql = f"DELETE FROM {table_name} WHERE pearl_id = :pearl_id"
                    params = {"pearl_id": pearl_id}
                    self._execute_raw_sql(sql, params)
                except Exception as e:
                    # Log or handle error for specific table, but continue with others
                    print(f"Error deleting data from table {table_name} for pearl_id {pearl_id}: {e}")

        # Also delete the PEARL ID itself from the pearl_ids table
        try:
            sql = "DELETE FROM pearl_ids WHERE id = :pearl_id"
            params = {"pearl_id": pearl_id}
            self._execute_raw_sql(sql, params)
        except Exception as e:
            print(f"Error deleting PEARL ID {pearl_id} from pearl_ids table: {e}")





