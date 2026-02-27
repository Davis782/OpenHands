
import sqlite3
import os
from App.src.core.database.data_access import DataAccess

def export_user_data_to_new_db(pearl_id: str, main_db_path: str, export_db_full_path: str):
    """
    Exports all data for a given PEARL_ID from the main database to a new database file.

    Args:
        pearl_id (str): The PEARL_ID of the user whose data is to be exported.
        main_db_path (str): The path to the main database file.
        export_db_full_path (str): The full path where the new database file will be created.
    """
    if os.path.exists(export_db_full_path):
        os.remove(export_db_full_path)

    main_conn = sqlite3.connect(main_db_path)
    main_cursor = main_conn.cursor()

    export_conn = sqlite3.connect(export_db_full_path)
    export_cursor = export_conn.cursor()

    try:
        # Get a list of all tables in the main database
        main_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = main_cursor.fetchall()

        for table_name_tuple in tables:
            table_name = table_name_tuple[0]
            if table_name.startswith('sqlite_'):
                continue  # Skip internal SQLite tables

            # Get the CREATE TABLE statement
            main_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            create_table_sql = main_cursor.fetchone()[0]
            export_cursor.execute(create_table_sql)

            # Check if the table has a 'pearl_id' column
            main_cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [info[1] for info in main_cursor.fetchall()]

            if 'pearl_id' in columns:
                # Copy data for the specific pearl_id
                main_cursor.execute(f"SELECT * FROM {table_name} WHERE pearl_id=?", (pearl_id,))
                rows = main_cursor.fetchall()

                if rows:
                    # Get column names to build the INSERT statement
                    main_cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
                    col_names = [description[0] for description in main_cursor.description]
                    placeholders = ', '.join(['?'] * len(col_names))
                    
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(col_names)}) VALUES ({placeholders})"
                    export_cursor.executemany(insert_sql, rows)
            else:
                # For tables without a pearl_id (like schema_version), you might want to copy all data
                # or handle them based on specific rules. For now, we'll copy all.
                main_cursor.execute(f"SELECT * FROM {table_name}")
                rows = main_cursor.fetchall()
                if rows:
                    main_cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
                    col_names = [description[0] for description in main_cursor.description]
                    placeholders = ', '.join(['?'] * len(col_names))
                    
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(col_names)}) VALUES ({placeholders})"
                    export_cursor.executemany(insert_sql, rows)


        export_conn.commit()

    finally:
        main_conn.close()
        export_conn.close()

def verify_exported_db(uploaded_file) -> bool:
    """
    Verifies if an uploaded database file is a valid SQLite database and contains tables.

    Args:
        uploaded_file: The file-like object from st.file_uploader.

    Returns:
        bool: True if the database is valid, False otherwise.
    """
    if uploaded_file is None:
        return False

    temp_dir = "temp_verification_files"
    os.makedirs(temp_dir, exist_ok=True)
    temp_db_path = os.path.join(temp_dir, uploaded_file.name)

    try:
        # Write the uploaded file to a temporary path
        with open(temp_db_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Try to connect and check for tables
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()

        # A valid export should have at least one table
        return len(tables) > 0

    except sqlite3.DatabaseError:
        # This will catch corrupted or non-SQLite files
        return False
    except Exception as e:
        print(f"An unexpected error occurred during DB verification: {e}")
        return False
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        # Clean up the temporary directory if it's empty
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)

