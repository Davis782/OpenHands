import os
from textwrap import dedent

from App.src.cli.cli_utils import clear, pause, _test_context, mock_input, menu_select_database, menu_vault_management, menu_transaction_management
from App.src.cli.menus.query_builder_menu import query_builder_menu


from ..core.database.pearl_qlite.pearl_qlite import PearlClient

from ..agent_pearl.agent_pearl import AgentPearl
from ..admin_tools.PEARL_Admin import menu_admin_tools
from ..admin_tools.csv_importer import generate_csv_template



__all__ = ["main_menu", "mock_input", "_test_context", "pause"]

def initialize_database_clients(db_name: str):
    """
    Initializes and returns PearlClient and AgentPearl instances for a given database.
    """
    client = PearlClient(db_name)
    agent_pearl = AgentPearl(db_name)
    return client, agent_pearl

def main_menu(test_mode: bool = False, mock_inputs: list = None):
    """
    Displays the main menu and handles user input for navigation.
    """
    if test_mode:
        _test_context.inputs = mock_inputs
        _test_context.current_input_index = 0
        global input
        input = mock_input

    db_name = "PEARL_AI_DB.sqlite" # Default database name
    client = None # Initialize client to None
    agent_pearl = None # Initialize agent_pearl to None

    while True:
        clear(test_mode=test_mode)
        print("Main Menu")
        print("---------")
        print("1. Select/Change Database")
        print("2. Vault Management")
        print("3. Admin Tools")
        print("4. Transaction Management")
        print("5. Query Builder")
        print("6. Generate CSV Template")
        print("7. Exit")
        print("---------")
        main_choice = input("> ").strip()

        if main_choice == "1":
            selected_db = menu_select_database(test_mode=test_mode)
            if selected_db:
                db_name = selected_db
                print(f"Database set to: {db_name}")
                # Re-initialize clients with the new database
                client, agent_pearl = initialize_database_clients(db_name)
            else:
                print("No database selected. Using default 'pearl.db'.")
                client, agent_pearl = initialize_database_clients(db_name) # Initialize with default if none selected
            pause()

        elif main_choice == "2":
            if agent_pearl is None:
                print("Please select or initialize a database first (Option 1).")
                pause()
            else:
                menu_vault_management(agent_pearl, test_mode=test_mode)

        elif main_choice == "3":
            if agent_pearl is None:
                print("Please select or initialize a database first (Option 1).")
                pause()
            else:
                menu_admin_tools(agent_pearl, test_mode=test_mode)

        elif main_choice == "4":
            if agent_pearl is None:
                print("Please select or initialize a database first (Option 1).")
                pause()
            else:
                menu_transaction_management(agent_pearl, test_mode=test_mode)

        elif main_choice == "5":
            if agent_pearl is None:
                print("Please select or initialize a database first (Option 1).")
                pause()
            else:
                query_builder_menu(agent_pearl)

        elif main_choice == "6": # Generate CSV Template
            if client is None:
                print("Please select or initialize a database first (Option 1).")
                pause()
            else:
                clear(test_mode=test_mode)
                print("--- Generate CSV Template ---")
                table_names = client.get_all_table_names()
                if not table_names:
                    print("No tables found in the database to generate a template from.")
                    pause()
                    continue

                print("Available tables:")
                for i, table_name in enumerate(table_names):
                    print(f"{i+1}. {table_name}")

                while True:
                    try:
                        table_choice = input("Select a table by number to generate a template for: ").strip()
                        selected_table_index = int(table_choice) - 1
                        if 0 <= selected_table_index < len(table_names):
                            selected_table = table_names[selected_table_index]
                            break
                        else:
                            print("Invalid table number. Please try again.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
                
                output_filename = input(f"Enter desired filename for the template (e.g., {selected_table}_template.csv): ").strip()
                if not output_filename:
                    output_filename = f"{selected_table}_template.csv"
                
                # Ensure the output path is absolute or relative to the current working directory
                output_path = os.path.abspath(output_filename)

                print(f"Generating template for table '{selected_table}' at '{output_path}'...")
                success = generate_csv_template(client, selected_table, output_path)
                if success:
                    print(f"CSV template successfully generated for '{selected_table}' at '{output_path}'.")
                else:
                    print(f"Failed to generate CSV template for '{selected_table}'. Check logs for details.")
                pause()

        elif main_choice == "7":
            print("Exiting PEARL AI. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
            pause()



if __name__ == "__main__":
    # Example of running in test mode with mock inputs
    # This sequence of inputs will:
    # 1. Select/Change Database (option 1)
    # 2. Select the first database in the list (assuming there is one)
    # 3. Go to Query Builder (option 5)
    # 4. Build SELECT Query (option 1)
    # 5. Select the first table (assuming there is one)
    # 6. Select all columns (option 0)
    # 7. Provide no WHERE clause (empty input)
    # 8. Confirm execution (y)
    # 9. Press Enter to continue (empty input)
    # 10. Exit Query Builder (option 6)
    # 11. Exit Main Menu (option 6)
    mock_inputs_sequence = [
        "1", # Select/Change Database
        "1", # Select the first database
        "5", # Query Builder
        "1", # Build SELECT Query
        "1", # Select the first table
        "0", # Select all columns
        "",  # No WHERE clause
        "y", # Execute query
        "",  # Press Enter to continue
        "6", # Exit Query Builder
        "6"  # Exit Main Menu
    ]
    main_menu(test_mode=True, mock_inputs=mock_inputs_sequence)




