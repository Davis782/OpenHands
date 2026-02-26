#!/usr/bin/env python3
# PEARL_Admin.py
# Menu-driven administrative console for the PEARL_Platform ecosystem.

import json
import os
import sys
from App.src.core.seedtools.seedtools import generate_seed, seed_to_pearl_id

import argparse
import builtins
from textwrap import dedent

from App.src.agent.semantic import PearlClient

from App.src.agent_pearl.agent_pearl import AgentPearl
from App.src.admin_tools.csv_importer import import_or_update_table_from_csv
from App.src.cli.cli_utils import clear, pause, _test_context, mock_input, menu_vault_management, menu_select_database

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
print("PEARL_Admin.py is starting...", file=sys.stderr)

def initialize_database_clients(db_name: str):
    """
    Initializes and returns PearlClient and AgentPearl instances for a given database.
    """
    client = PearlClient(db_name)
    agent_pearl = AgentPearl(db_name)
    return client, agent_pearl

# -------------------------------------------------------------------
# Utility Functions (mock_input and pause)
# -------------------------------------------------------------------



def mock_input(prompt=""):
    if test_inputs_queue:
        value = test_inputs_queue.pop(0)
        # Enhanced debug output with queue status
        print(f"[MOCK_INPUT] Prompt: '{prompt.strip()}' | Returned: '{value}' | Remaining inputs: {len(test_inputs_queue)}", file=sys.stderr)
        return value
    else:
        # Debug output for real user input
        print(f"[MOCK_INPUT] Using real input for prompt: '{prompt.strip()}'", file=sys.stderr)
        return original_input(prompt)

# -------------------------------------------------------------------
# Main Menu
# -------------------------------------------------------------------
def view_agent_state(agent_pearl, test_mode: bool = False):
    """
    Allows the user to view the state of an agent by its PEARL_ID.
    """
    clear(test_mode=test_mode)
    print("View Agent State")
    print("----------------")
    pearl_id = input("Enter PEARL_ID of the agent to view (e.g., '00000000-0000-4000-8000-000000000000'): ").strip()
    if not pearl_id:
        print("PEARL_ID cannot be empty.")
        pause()
        return

    try:
        agent_state = agent_pearl.get_entity(pearl_id)
        if agent_state:
            print(f"\nState for Agent PEARL_ID: {pearl_id}")
            print(json.dumps(agent_state, indent=2))
        else:
            print(f"No agent found with PEARL_ID: {pearl_id}")
    except Exception as e:
        print(f"Error retrieving agent state: {e}")
    pause()

def list_all_pearl_ids(agent_pearl, test_mode: bool = False):
    """
    Displays a list of all PEARL IDs and their associated entity types and attributes.
    """
    clear(test_mode=test_mode)
    print("List All PEARL IDs")
    print("------------------")
    try:
        pearl_ids = agent_pearl.get_all_pearl_ids()
        if pearl_ids:
            for pearl_id_data in pearl_ids:
                print(f"  ID: {pearl_id_data['id']}, Type: {pearl_id_data['entity_type']}, Attributes: {pearl_id_data['attributes']}")
        else:
            print("No PEARL IDs found.")
    except Exception as e:
        print(f"Error retrieving PEARL IDs: {e}")
    pause()

def list_all_tables(agent_pearl, test_mode: bool = False):
    """
    Displays a list of all tables in the database.
    """
    clear(test_mode=test_mode)
    print("List All Tables")
    print("---------------")
    try:
        tables = agent_pearl.pearl_client.get_all_table_names()
        if tables:
            for table in tables:
                print(f"- {table}")
        else:
            print("No tables found in the database.")
    except Exception as e:
        print(f"Error retrieving tables: {e}")
    pause()

def export_query_results_menu(agent_pearl, test_mode: bool = False):
    """
    Menu for exporting query results to various formats.
    """
    clear(test_mode=test_mode)
    print("Export Query Results")
    print("--------------------")
    print("1. Default Export: All PEARL IDs (SELECT id, entity_type, attributes FROM pearl_ids;)")
    print("2. Custom SQL Query")
    export_type_choice = input("Select export type (1 or 2, e.g., '1'): ").strip()

    if export_type_choice == "1":
        sql_query = "SELECT id, entity_type, attributes FROM pearl_ids;"
        file_name = input("Enter filename for export (e.g., 'pearl_ids.csv'): ").strip()
        if not file_name:
            print("Filename cannot be empty. Export cancelled.")
            pause()
            return
        try:
            agent_pearl.pearl_client.export_query_to_csv(sql_query, file_name)
            print(f"Default PEARL ID data exported to {file_name}")
        except Exception as e:
            print(f"Error exporting default PEARL IDs: {e}")
        pause()
    elif export_type_choice == "2":
        sql_query = input("Enter custom SQL query: ").strip()
        file_name = input("Enter filename for export (e.g., 'custom_query.csv'): ").strip()
        if not file_name:
            print("Filename cannot be empty. Export cancelled.")
            pause()
            return
        try:
            agent_pearl.pearl_client.export_query_to_csv(sql_query, file_name)
            print(f"Custom query results exported to {file_name}")
        except Exception as e:
            print(f"Error exporting custom query results: {e}")
        pause()
    else:
        print("Invalid choice. Export cancelled.")
        pause()

def import_csv_menu(agent_pearl, test_mode: bool = False):
    """
    Menu for importing data from a CSV file into a database table.
    """
    clear(test_mode=test_mode)
    print("Import CSV to Table")
    print("-------------------")
    csv_file_path = input("Enter the path to the CSV file (e.g., 'data.csv'): ").strip()
    table_name = input("Enter the target table name (e.g., 'agents'): ").strip()
    if not csv_file_path or not table_name:
        print("CSV file path and table name cannot be empty. Import cancelled.")
        pause()
        return

    try:
        import_or_update_table_from_csv(agent_pearl.pearl_client, csv_file_path, table_name)
        print(f"Data from {csv_file_path} imported/updated in table {table_name}.")
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file_path}")
    except Exception as e:
        print(f"Error importing CSV: {e}")
    pause()

def interpret_pearl_id_menu(agent_pearl, test_mode: bool = False):
    """
    Menu for interpreting a PEARL ID.
    """
    clear(test_mode=test_mode)
    print("Interpret PEARL ID")
    print("------------------")
    pearl_id = input("Enter PEARL ID to interpret (e.g., '00000000-0000-4000-8000-000000000000'): ").strip()
    if not pearl_id:
        print("PEARL ID cannot be empty.")
        pause()
        return

    try:
        result = agent_pearl.interpret_pearl_id(pearl_id)
        print("\nInterpretation Result:")
        if result["status"] == "success":
            print(f"PEARL ID: {result['pearl_id']}")
            if result.get("derived_from_vault_seed"):
                print(f"Derived from current vault's seed: {result['vault_seed']}")
                print(f"3D Vector: (x={result['vector']['x']:.4f}, y={result['vector']['y']:.4f}, z={result['vector']['z']:.4f})")
            else:
                print(result["message"])
                if result.get("entity_data"):
                    print(json.dumps(result["entity_data"], indent=2))
        else:
            print(f"Error: {result['message']}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    pause()

def _generate_pearl_id_from_seed_string_flow(agent_pearl, test_mode: bool = False):
    """
    Handles the flow for generating a PEARL ID from a user-provided seed string.
    """
    clear(test_mode=test_mode)
    print("Generate PEARL ID from Seed String")
    print("----------------------------------")
    seed_string = input("Enter seed string (e.g., 'user:john.doe:department:sales'): ").strip()
    if not seed_string:
        print("Seed string cannot be empty. Generation cancelled.")
        pause()
        return

    try:
        pearl_id = seed_to_pearl_id(seed_string)
        print(f"\nGenerated PEARL ID: {pearl_id}")

        store_seed = input("Store this seed string in the vault's identity compartment? (y/N): ").strip().lower()
        if store_seed == 'y':
            identity_password = input("Enter Identity password to store seed: ")
            if not identity_password:
                print("Identity password cannot be empty. Seed string not stored.")
            else:
                agent_pearl.vault.store_seed(seed_string, identity_password)
                print("Seed string stored in vault's identity compartment.")
        else:
            print("Seed string not stored in vault.")

    except Exception as e:
        print(f"Error generating PEARL ID: {e}")
    pause()

def _generate_random_seed_string_flow(agent_pearl, test_mode: bool = False):
    """
    Handles the flow for generating a random seed string.
    """
    clear(test_mode=test_mode)
    print("Generate Random Seed String")
    print("---------------------------")
    try:
        random_seed = generate_seed()
        print(f"\nGenerated Random Seed String: {random_seed}")
    except Exception as e:
        print(f"Error generating random seed string: {e}")
    pause()

def menu_admin_tools(agent_pearl, test_mode: bool = False):
    """
    Displays a sub-menu for Agent-PEARL Debug Tools and handles user input.
    """
    while True:
        clear(test_mode=test_mode)
        print(dedent("""
        Agent-PEARL Debug Tools
        -----------------------
        1. View Agent State
        2. List All PEARL IDs
        3. List All Tables
        4. Export Query Results
        5. Import CSV to Table
        6. Interpret PEARL ID
        7. Generate PEARL ID from Seed String
        8. Generate Random Seed String
        9. Back
        """))

        choice = input("> ").strip()

        if choice == "1":
            view_agent_state(agent_pearl, test_mode=test_mode)
        elif choice == "2":
            list_all_pearl_ids(agent_pearl, test_mode=test_mode)
        elif choice == "3":
            list_all_tables(agent_pearl, test_mode=test_mode)
        elif choice == "4":
            export_query_results_menu(agent_pearl, test_mode=test_mode)
        elif choice == "5":
            import_csv_menu(agent_pearl, test_mode=test_mode)
        elif choice == "6":
            interpret_pearl_id_menu(agent_pearl, test_mode=test_mode)
        elif choice == "7":
            _generate_pearl_id_from_seed_string_flow(agent_pearl, test_mode=test_mode)
        elif choice == "8":
            _generate_random_seed_string_flow(agent_pearl, test_mode=test_mode)
        elif choice == "9":
            break
        else:
            print("Invalid choice. Please try again.")
            pause()

def main_menu(args, test_mode: bool = False):
    client, agent_pearl = None, None
    current_db = None

    while True:
        clear()
        print(dedent(f"""
        PEARL Admin Console
        -------------------
        Current DB: {current_db if current_db else "Not Selected"}
        Vault Status: {"Loaded" if agent_pearl and not agent_pearl.vault.is_locked() else "Locked/Not Loaded"}
        
        1. Database Management
        2. Vault Management
        3. Agent-PEARL Debug Tools
        4. Exit
        """))

        choice = input("> ").strip()

        if args.main_choice and not test_inputs_queue: # For single-shot test execution
            choice = args.main_choice
            args.main_choice = None # Consume the choice

        if choice == "1":
            current_db = menu_select_database(test_mode=args.test)
            if current_db:
                client, agent_pearl = initialize_database_clients(current_db)
        elif choice == "2":
            menu_vault_management(agent_pearl, test_mode=args.test)
        elif choice == "3":
            if agent_pearl:
                menu_admin_tools(agent_pearl, test_mode=args.test)
            else:
                print("Please select a database first (Option 1).")
                pause()
        elif choice == "4":
            print("Exiting PEARL Admin Console.")
            break
        else:
            print("Invalid choice. Please try again.")
            pause()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PEARL Admin Console")
    parser.add_argument("--main_choice", type=str, help="Main menu choice")
    parser.add_argument("--agent_choice", type=str, help="Agent-PEARL Debug Tools menu choice")
    parser.add_argument("--nlq_query", type=str, help="Natural Language Query for Agent-PEARL")
    parser.add_argument("--test", action="store_true", help="Enable test mode")
    args = parser.parse_args()

    # Global variable to store test inputs
    test_inputs_queue: list[str] = []
    original_input = input

    if args.test:
        test_file_path = os.environ.get("PEARL_TEST_INPUTS_FILE")
        if test_file_path and os.path.exists(test_file_path):
            with open(test_file_path, 'r') as f:
                test_inputs_queue.extend([line.strip() for line in f.readlines()])
            builtins.input = mock_input

            # Store original stdout and stderr
            original_stdout = sys.stdout
            original_stderr = sys.stderr

            # Redirect stdout and stderr to a file for test mode
            sys.stdout = open("test_run_output.txt", "w")
            sys.stderr = sys.stdout # Redirect stderr to the same file
        else:
            print(f"Error: Test mode enabled but PEARL_TEST_INPUTS_FILE environment variable not set or file not found: {test_file_path}", file=sys.stderr)
            sys.exit(1)

    try:
        main_menu(args, test_mode=args.test)
    finally:
        if args.test:
            # Restore original stdout and stderr
            sys.stdout.close()
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            print("Test mode output redirected to test_run_output.txt", file=sys.stderr)
