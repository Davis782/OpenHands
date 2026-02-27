import csv
import os
import logging
from typing import List, Dict
from ..core.database.pearl_qlite.pearl_qlite import PearlClient
from ..core.seedtools.seedtools import seed_to_pearl_id

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _infer_column_types_from_csv(file_path: str, csv_headers: List[str]) -> Dict[str, str]:
    """
    Infers SQL column types (TEXT, INTEGER, REAL) from CSV data.
    It reads the first few rows to make a best guess.

    Args:
        file_path (str): The path to the CSV file.
        csv_headers (List[str]): The headers from the CSV file.

    Returns:
        Dict[str, str]: A dictionary mapping column names to inferred SQL types.
    """
    column_types = {header: "TEXT" for header in csv_headers} # Default to TEXT

    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # Skip header row

        # Read a few rows to infer types
        sample_rows = []
        for _ in range(10): # Sample up to 10 rows
            try:
                row = next(reader)
                if row:
                    sample_rows.append(row)
            except StopIteration:
                break

        for i, header in enumerate(csv_headers):
            is_integer = True
            is_real = True
            
            for row in sample_rows:
                if i < len(row):
                    value = row[i].strip()
                    if not value: # Empty string, can be anything
                        continue
                    
                    # Check for INTEGER
                    try:
                        int(value)
                    except ValueError:
                        is_integer = False
                    
                    # Check for REAL
                    try:
                        float(value)
                    except ValueError:
                        is_real = False
            
            if is_integer and any(row[i].strip() for row in sample_rows if i < len(row)):
                column_types[header] = "INTEGER"
            elif is_real and any(row[i].strip() for row in sample_rows if i < len(row)):
                column_types[header] = "REAL"
            # Else, it remains TEXT (default)
    
    return column_types

def import_or_update_table_from_csv(file_path: str, client: PearlClient, table_name: str):
    """
    Imports or updates data from a CSV or TXT file into a specified table.
    It attempts to use INSERT OR REPLACE to handle both new records and updates.
    If the table does not exist, it attempts to create it based on CSV headers
    and inferred column types.

    Args:
        file_path (str): The path to the CSV or TXT file.
        client (PearlClient): An instance of the PearlClient for database interaction.
        table_name (str): The name of the table to import data into.
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return

    logging.info(f"Starting import/update from {file_path} into table '{table_name}'")

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            # Read header from CSV
            try:
                csv_headers = [h.strip() for h in next(reader)]
                if not csv_headers:
                    logging.error("CSV file is empty or contains no headers.")
                    return
            except StopIteration:
                logging.error("CSV file is empty or contains no headers.")
                return

            # Infer types from CSV headers immediately
            inferred_types = _infer_column_types_from_csv(file_path, csv_headers)

            # Check if table exists
            db_columns = client.get_table_columns(table_name)
            
            add_pearl_id_column = False
            add_autoincrement_id_column = False # New flag
            
            if not db_columns:
                logging.info(f"Table '{table_name}' not found. Attempting to create it.")
                
                if table_name == 'transactions':
                    add_pearl_id_column = True
                    logging.info("Automatically adding 'pearl_id' column for 'transactions' table.")
                else:
                    user_choice = input(f"Table '{table_name}' does not exist. Do you want to add a 'pearl_id' column to it? (y/n): ").lower()
                    if user_choice == 'y':
                        add_pearl_id_column = True
                        logging.info(f"User chose to add 'pearl_id' column to '{table_name}'.")
                    else:
                        add_autoincrement_id_column = True # User chose not to add pearl_id, so add autoincrement id
                        logging.info(f"User chose NOT to add 'pearl_id' column to '{table_name}'. Adding 'id INTEGER PRIMARY KEY AUTOINCREMENT' instead.")

                column_definitions = []
                has_pearl_id_in_csv = 'pearl_id' in [h.lower() for h in csv_headers]
                has_id_in_csv = 'id' in [h.lower() for h in csv_headers]

                for header in csv_headers:
                    sql_type = inferred_types.get(header, "TEXT")
                    definition = f"{header} {sql_type}"
                    column_definitions.append(definition)
                
                # Apply primary key logic after initial column definitions
                if add_pearl_id_column:
                    if has_pearl_id_in_csv:
                        # Find and modify the existing pearl_id definition
                        for i, def_str in enumerate(column_definitions):
                            if def_str.lower().startswith('pearl_id '):
                                column_definitions[i] = f"{def_str} PRIMARY KEY"
                                break
                    else:
                        column_definitions.append("pearl_id TEXT PRIMARY KEY")
                elif add_autoincrement_id_column:
                    if has_id_in_csv:
                        # Find and modify the existing id definition
                        for i, def_str in enumerate(column_definitions):
                            if def_str.lower().startswith('id '):
                                if inferred_types.get('id', 'TEXT') == 'INTEGER':
                                    column_definitions[i] = f"{def_str} PRIMARY KEY AUTOINCREMENT"
                                else:
                                    logging.warning(f"Column 'id' exists in CSV but is not INTEGER. Cannot apply AUTOINCREMENT. Using 'id {inferred_types.get('id', 'TEXT')} PRIMARY KEY'.")
                                    column_definitions[i] = f"{def_str} PRIMARY KEY"
                                break
                    else:
                        column_definitions.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
                
                create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_definitions)});"
                logging.info(f"Executing CREATE TABLE: {create_table_sql}")
                try:
                    client.execute_ddl(create_table_sql)
                    logging.info(f"Table '{table_name}' created successfully.")
                    # Re-fetch db_columns after creation
                    db_columns = client.get_table_columns(table_name)
                except Exception as e:
                    logging.error(f"Error creating table '{table_name}': {e}")
                    return
            
            if not db_columns: # If table creation failed or still no columns
                logging.error(f"Could not determine columns for table '{table_name}'. Aborting import.")
                return

            # We'll only consider columns that exist in both the CSV and the database
            common_columns = [col for col in csv_headers if col in db_columns]
            if not common_columns:
                logging.error(f"No common columns found between CSV headers ({csv_headers}) and table '{table_name}' columns ({db_columns}). Aborting import.")
                return

            # Prepare the INSERT OR REPLACE statement
            # This assumes that the table has a PRIMARY KEY or UNIQUE constraint
            # to identify rows for replacement.
            placeholders = ', '.join(['?' for _ in common_columns])
            columns_str = ', '.join(common_columns)
            
            # Special handling for 'pearl_id' column if it's not in CSV but needed
            # This now considers the 'add_pearl_id_column' flag for non-transactions tables
            insert_pearl_id_dynamically = False
            if 'pearl_id' in db_columns and 'pearl_id' not in common_columns and add_pearl_id_column:
                insert_pearl_id_dynamically = True
                # Add pearl_id to columns for insertion
                columns_str = 'pearl_id, ' + columns_str
                placeholders = '?, ' + placeholders
            elif 'pearl_id' in db_columns and 'pearl_id' not in common_columns and not add_pearl_id_column and not add_autoincrement_id_column:
                 logging.warning(f"Table '{table_name}' has 'pearl_id' column but it's not in CSV and user chose not to add it dynamically. "
                                 "Skipping dynamic PEARL ID generation for this table.")

            sql = f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders});"

            # Reset file pointer to read data rows after header
            f.seek(0)
            next(reader) # Skip header again

            for i, row_data in enumerate(reader):
                if not row_data or all(not cell.strip() for cell in row_data):
                    logging.info(f"Skipping blank line at row {i+2}.")
                    continue

                row_dict = dict(zip(csv_headers, [d.strip() for d in row_data]))
                
                params = []
                if insert_pearl_id_dynamically:
                    # Generate PEARL ID from all available row data for transactions or user-chosen tables
                    seed_string = ','.join(f"{k}:{v}" for k,v in row_dict.items())
                    params.append(seed_to_pearl_id(seed_string))

                for col in common_columns:
                    value = row_dict.get(col)
                    # Attempt type conversion if necessary (basic for now)
                    if value is not None:
                        try:
                            # Basic type conversion for common types
                            if inferred_types.get(col) == 'INTEGER':
                                params.append(int(value))
                            elif inferred_types.get(col) == 'REAL':
                                params.append(float(value))
                            else:
                                params.append(value)
                        except ValueError:
                            logging.warning(f"Type conversion failed for column '{col}' with value '{value}' in row {i+2}. "
                                            "Using original string value.")
                            params.append(value)
                    else:
                        params.append(None) # Append None for missing values

                if len(params) != len(common_columns) + (1 if insert_pearl_id_dynamically else 0):
                    logging.warning(f"Skipping row {i+2} due to parameter count mismatch. Expected "
                                    f"{len(common_columns) + (1 if insert_pearl_id_dynamically else 0)}, got {len(params)}. Row data: {row_dict}")
                    continue

                try:
                    client.execute_query(sql, tuple(params))
                    logging.info(f"Processed row {i+2} for table '{table_name}'.")
                except Exception as e:
                    logging.error(f"Error processing row {i+2} for table '{table_name}': {e}. Row data: {row_dict}")

    except Exception as e:
        logging.error(f"An unexpected error occurred during file processing: {e}")

    logging.info(f"Import/update process finished for table '{table_name}'.")

def generate_csv_template(client: PearlClient, table_name: str, output_path: str):
    """
    Generates an empty CSV file with headers based on the specified table's columns.

    Args:
        client (PearlClient): An instance of the PearlClient for database interaction.
        table_name (str): The name of the table to generate the template for.
        output_path (str): The full path where the CSV template file should be saved.
    """
    try:
        table_columns = client.get_table_columns(table_name)
        if not table_columns:
            logging.warning(f"No columns found for table '{table_name}'. Cannot generate template.")
            return False

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(table_columns)
        logging.info(f"CSV template for table '{table_name}' generated successfully at '{output_path}'.")
        return True
    except Exception as e:
        logging.error(f"Error generating CSV template for '{table_name}': {e}")
        return False


if __name__ == '__main__':
    # Example usage (for testing purposes)
    # This part will not run when imported as a module
    print("This is a module for importing data. Run PEARL_Admin.py to use it.")
    # Example:
    # from PEARL_AI_DB.pearl_qlite.pearl_qlite import PearlClient
    # client = PearlClient()
    #
    # # Create a dummy CSV file for testing transactions
    # with open("test_transactions.csv", "w", newline='') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(['item', 'cost', 'payment', 'sku'])
    #     writer.writerow(['Laptop', '1200.50', 'Credit', 'SKU1001'])
    #     writer.writerow(['Mouse', '25', 'Cash', 'SKU1002'])
    #     writer.writerow(['Keyboard', '75.99', 'Debit', 'SKU1003'])
    #
    # import_or_update_table_from_csv("test_transactions.csv", client, "transactions")
    #
    # # Create a dummy CSV file for testing pearl_ids (assuming pearl_ids table has 'id', 'entity_type', 'attributes')
    # # Note: 'id' here would be the PEARL ID itself, which should be generated or provided.
    # # For simplicity, let's assume 'id' is provided in CSV for pearl_ids table.
    # with open("test_pearl_ids.csv", "w", newline='') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(['id', 'entity_type', 'attributes'])
    #     writer.writerow([pearl_id("user1"), 'user', '{"name": "Alice"}'])
    #     writer.writerow([pearl_id("productA"), 'product', '{"name": "Product A", "price": 99.99}'])
    #
    # # import_or_update_table_from_csv("test_pearl_ids.csv", client, "pearl_ids")
    #
    # # Verify by listing all transactions
    # print("\nVerifying imported transactions:")
    # results = client.execute_query("SELECT pearl_id, item, cost, payment, sku FROM transactions;")
    # for row in results:
    #     print(row)

