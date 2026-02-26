import os
import sqlite3
import pandas as pd

# Adjust the path to import from the correct location
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'App')))

from src.core.database.data_access import DataAccess
from src.core.database.pearl_qlite.pearl_qlite import PearlClient
from App.config.sql_categories import SQL_CATEGORIES

def initialize_database(db_path: str):
    """
    Initializes the SQLite database by creating tables based on SQL scripts.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for category_obj in SQL_CATEGORIES:
        sql_base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'App', 'sql'))
        
        create_table_scripts = []
        other_scripts = []

        for script_name, script_path_relative in category_obj.sql_files:
            if "create_table" in script_name or "create_pearls_table" in script_name or "create_groups_table" in script_name or "create_group_members_table" in script_name:
                create_table_scripts.append((script_name, script_path_relative))
            else:
                other_scripts.append((script_name, script_path_relative))

        # Execute create table scripts first
        for script_name, script_path_relative in create_table_scripts:
            full_script_path = os.path.join(sql_base_path, script_path_relative)
            try:
                with open(full_script_path, "r") as f:
                    sql_script = f.read()
                    cursor.executescript(sql_script)
                # print(f"Successfully executed CREATE script: {script_name}")
            except Exception as e:
                print(f"Error executing CREATE script {script_name}: {e}")

        # Then execute other scripts
        for script_name, script_path_relative in other_scripts:
            full_script_path = os.path.join(sql_base_path, script_path_relative)
            try:
                with open(full_script_path, "r") as f:
                    sql_script = f.read()
                    cursor.executescript(sql_script)
                # print(f"Successfully executed OTHER script: {script_name}")
            except Exception as e:
                print(f"Error executing OTHER script {script_name}: {e}")
    conn.close()

def generate_pearl_id_csv(db_path: str, output_filename: str = "PEARL_ID_Import.csv"):
    """
    Generates a CSV file containing all distinct PEARL IDs from the database.
    """
    sql_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'App', 'sql'))

    # Ensure the database is initialized (handled by PearlClient internally)

    # Instantiate PearlClient and DataAccess
    pearl_client = PearlClient(db_path)
    dal = DataAccess(db_path, sql_dir, pearl_client)

    try:
        all_pearl_ids = dal.get_all_distinct_pearl_ids_from_all_tables()
        if not all_pearl_ids:
            print("No PEARL IDs found. Creating sample PEARL IDs...")
            # Create some sample PEARL IDs using pearl_client
            pearl_client.create_pearl_id(entity_type="Person", attributes={"name": "Alice", "age": 30}, seed="alice_seed")
            pearl_client.create_pearl_id(entity_type="Company", attributes={"name": "Acme Corp", "industry": "Tech"}, seed="acme_seed")
            pearl_client.create_pearl_id(entity_type="Project", attributes={"name": "Project X", "status": "Active"}, seed="projectx_seed")
            all_pearl_ids = dal.get_all_distinct_pearl_ids_from_all_tables() # Re-fetch after creation

        if all_pearl_ids:
            df = pd.DataFrame({"pearl_id": all_pearl_ids})
            df.to_csv(output_filename, index=False)
            print(f"Successfully generated {output_filename} with {len(all_pearl_ids)} PEARL IDs.")
        else:
            print("Still no PEARL IDs found after attempting to create samples. CSV will not be generated.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Default database path (you might need to adjust this if your DB is elsewhere)
    default_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'App', 'src', 'core', 'database', 'databases', 'pearl_database.db'))
    generate_pearl_id_csv(default_db_path)
