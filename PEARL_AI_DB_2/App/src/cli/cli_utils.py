import os
import sys
import builtins
import json
from textwrap import dedent

from ..core.seedtools import seedtools
from ..core.database.pearl_qlite.pearl_qlite import PearlClient
from ..agent_pearl.agent_pearl import AgentPearl

class TestContext:
    """
    Manages the mocking of builtins.input for testing purposes.
    """
    def __init__(self):
        self.test_inputs_queue = []
        self.original_input = builtins.input
        self.test_mode = False

    def mock_input(self, prompt=""):
        if self.test_inputs_queue:
            value = self.test_inputs_queue.pop(0)
            print(f"[MOCK_INPUT] Prompt: '{prompt.strip()}' | Returned: '{value}' | Remaining inputs: {len(self.test_inputs_queue)}")
            return value
        else:
            print(f"[MOCK_INPUT] Using real input for prompt: '{prompt.strip()}'")
            return self.original_input(prompt)

    def activate_test_mode(self, inputs: list[str]):
        self.test_inputs_queue = list(inputs)
        builtins.input = self.mock_input
        self.test_mode = True

    def deactivate_test_mode(self):
        builtins.input = self.original_input
        self.test_inputs_queue = []
        self.test_mode = False

_test_context = TestContext()
mock_input = _test_context.mock_input

def pause():
    """
    Pauses the execution, waiting for user input, unless in test mode.
    """
    if _test_context.test_mode:
        print("[PAUSE SKIPPED (test mode)]", file=sys.stderr)
    else:
        builtins.input("Press ENTER to continue...")

def clear(test_mode: bool = False):
    """
    Clears the terminal screen.
    """
    if test_mode:
        print("[CLEAR_SCREEN_SIMULATED]", file=sys.stderr)
    else:
        if os.name == 'nt':
            _ = os.system('cls')
        else:
            _ = os.system('clear')

def get_user_input(prompt: str) -> str:
    """
    Gets user input, handling test mode automatically.
    """
    return input(prompt + "> ").strip()

def print_menu(title: str, options: list[str]):
    """
    Prints a formatted menu with a title and numbered options.
    """
    print(f"\n--- {title} ---")
    for i, option in enumerate(options):
        print(f"{i + 1}. {option}")
    print("------------------")

def menu_select_database(test_mode: bool = False):
    """
    Allows the user to select a database file from the 'databases' directory.
    Returns the selected database file name (e.g., "pearl.db").
    """
    db_dir = os.path.join(os.path.dirname(__file__), '..', 'core', 'database', 'databases')
    print(f"[DEBUG] db_dir: {db_dir}") # Debug print
    db_files = sorted([f for f in os.listdir(db_dir) if f.endswith('.sqlite')])
    print(f"[DEBUG] db_files: {db_files}") # Debug print

    if not db_files:
        print("No database files found in the 'databases' directory.")
        pause()
        return None

    while True:
        print("\nSelect a Database:")
        print("------------------")
        for i, db_file in enumerate(db_files):
            print(f"{i + 1}. {db_file}")
        print(f"{len(db_files) + 1}. Create New Database")
        print("------------------")
        print("Enter the number of the database, type its name, or choose to create a new one:")
        choice = input("> (e.g., '1', 'my_new_db.db', or 'Create') ").strip()

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(db_files):
                return db_files[idx]
            elif idx == len(db_files): # Create New Database option
                while True:
                    new_db_name = input("Enter the name for the new database (e.g., 'my_new_db'): ").strip()
                    if not new_db_name:
                        print("Database name cannot be empty.")
                        continue
                    if not (new_db_name.endswith(".db") or new_db_name.endswith(".sqlite")):
                        new_db_name += ".db"
                    
                    new_db_path = os.path.join(db_dir, new_db_name)
                    if os.path.exists(new_db_path):
                        print(f"A database named '{new_db_name}' already exists. Please choose a different name.")
                    else:
                        try:
                            # Create an empty database file by connecting to it
                            conn = sqlite3.connect(new_db_path)
                            conn.close()
                            print(f"Database '{new_db_name}' created successfully.")
                            pause()
                            return new_db_name
                        except Exception as e:
                            print(f"Error creating database: {e}")
                            pause()
                            return None
            else:
                print("Invalid number. Please try again.")
            pause()
        elif choice.lower() == "create": # Allow typing "create" for new database
            while True:
                new_db_name = input("Enter the name for the new database (e.g., 'my_new_db'): ").strip()
                if not new_db_name:
                    print("Database name cannot be empty.")
                    continue
                if not (new_db_name.endswith(".db") or new_db_name.endswith(".sqlite")):
                    new_db_name += ".db"
                
                new_db_path = os.path.join(db_dir, new_db_name)
                if os.path.exists(new_db_path):
                    print(f"A database named '{new_db_name}' already exists. Please choose a different name.")
                else:
                    try:
                        conn = sqlite3.connect(new_db_path)
                        conn.close()
                        print(f"Database '{new_db_name}' created successfully.")
                        pause()
                        return new_db_name
                    except Exception as e:
                        print(f"Error creating database: {e}")
                        pause()
                        return None
        elif choice in db_files:
            return choice
        else:
            print("Invalid input. Please try again.")
            pause()

def menu_vault_management(agent_pearl, test_mode: bool = False):
    """
    Manages vault operations like unlocking, locking, and creating new vaults.
    """
    active_pearl_id = None # To store the currently selected PEARL ID for transactions

    while True:
        clear(test_mode=test_mode)
        print("Vault Management")
        print("----------------")
        print("1. Unlock Vault")
        print("2. Lock Vault")
        print("3. Create New Vault")
        print("4. Back to Main Menu")
        print("----------------")
        choice = input("> ").strip()

        if choice == "1":
            _load_existing_vault_flow(agent_pearl, test_mode=test_mode)
        elif choice == "2":
            _lock_vault_flow(agent_pearl, test_mode=test_mode)
        elif choice == "3":
            _create_new_vault_flow(agent_pearl, test_mode=test_mode)
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")
        pause()

def menu_transaction_management(agent_pearl, test_mode: bool = False):
    """
    Manages job creation, selection, and transaction recording.
    """
    active_job_pearl_id = None

    while True:
        clear(test_mode=test_mode)
        print("Transaction Management")
        print("----------------------")
        print("1. Create New Job")
        print("2. Select Existing Job")
        print("3. Record Transaction (requires active job)")
        print("4. View Transactions for Active Job")
        print("5. Mark Active Job as Finished")
        print("6. Delete Active Job")
        print("7. Back to Main Menu")
        print("----------------------")
        choice = input("> ").strip()

        if choice == "1":
            active_job_pearl_id = _create_new_job_flow(agent_pearl, test_mode=test_mode)
        elif choice == "2":
            active_job_pearl_id = _select_existing_job_flow(agent_pearl, test_mode=test_mode)
        elif choice == "3":
            if active_job_pearl_id:
                _record_transaction_flow(agent_pearl, active_job_pearl_id, test_mode=test_mode)
            else:
                print("Please select or create a job first (Option 1 or 2).")
                pause()
        elif choice == "4":
            if active_job_pearl_id:
                _view_transactions_flow(agent_pearl, active_job_pearl_id, test_mode=test_mode)
            else:
                print("Please select or create a job first (Option 1 or 2).")
                pause()
        elif choice == "5":
            if active_job_pearl_id:
                _mark_job_status_flow(agent_pearl, active_job_pearl_id, "finished", test_mode=test_mode)
            else:
                print("Please select or create a job first (Option 1 or 2).")
                pause()
        elif choice == "6":
            if active_job_pearl_id:
                _mark_job_status_flow(agent_pearl, active_job_pearl_id, "deleted", test_mode=test_mode)
                active_job_pearl_id = None # Clear active job after deletion
            else:
                print("Please select or create a job first (Option 1 or 2).")
                pause()
        elif choice == "7":
            break
        else:
            print("Invalid choice. Please try again.")
        pause()

def _create_new_job_flow(agent_pearl, test_mode: bool = False) -> str | None:
    """
    Handles the flow for creating a new job and associating it with a PEARL ID.
    """
    clear(test_mode=test_mode)
    print("Create New Job")
    print("--------------")
    job_name = input("Enter a name for the new job: ").strip()
    if not job_name:
        print("Job name cannot be empty.")
        pause()
        return None

    try:
        # Create a PEARL ID for the job with entity_type 'job'
        pearl_id = agent_pearl.create_entity(entity_type="job", attributes={"name": job_name})
        print(f"Successfully created job '{job_name}' with PEARL ID: {pearl_id}")
        pause()
        return pearl_id
    except Exception as e:
        print(f"Error creating new job: {e}")
        pause()
        return None

def _select_existing_job_flow(agent_pearl, test_mode: bool = False) -> str | None:
    """
    Handles the flow for selecting an existing job, allowing filtering by status.
    """
    while True:
        clear(test_mode=test_mode)
        print("Select Existing Job")
        print("-------------------")
        print("1. View Active Jobs")
        print("2. View Finished Jobs")
        print("3. View Deleted Jobs")
        print("4. View All Jobs")
        print("5. Back to Transaction Management")
        
        status_choice = input("> ").strip()
        
        if status_choice == "5":
            return None

        selected_status = None
        if status_choice == "1":
            selected_status = "active"
        elif status_choice == "2":
            selected_status = "finished"
        elif status_choice == "3":
            selected_status = "deleted"
        elif status_choice == "4":
            selected_status = None # View all statuses
        else:
            print("Invalid choice. Please try again.")
            pause()
            continue

        try:
            all_pearl_ids = agent_pearl.get_all_pearl_ids()
            job_pearl_ids = [p for p in all_pearl_ids if p.get("entity_type") == "job"]

            if selected_status:
                filtered_jobs = [job for job in job_pearl_ids if job.get("status") == selected_status]
            else:
                filtered_jobs = job_pearl_ids

            if not filtered_jobs:
                print(f"No {selected_status if selected_status else ''} jobs found.")
                pause()
                continue

            print(f"\nAvailable {selected_status if selected_status else 'All'} Jobs:")
            for i, job in enumerate(filtered_jobs):
                job_name = job["attributes"].get("name", "N/A")
                job_status = job.get("status", "active")
                print(f"{i+1}. {job_name} (ID: {job['id']}) [Status: {job_status.capitalize()}]")

            while True:
                try:
                    choice = input("Enter the number of the job to select (or 'b' to go back to status selection): ").strip()
                    if choice.lower() == 'b':
                        break # Go back to status selection menu
                    
                    index = int(choice) - 1
                    if 0 <= index < len(filtered_jobs):
                        selected_job = filtered_jobs[index]
                        print(f"Selected job: {selected_job['attributes'].get('name', 'N/A')} (ID: {selected_job['id']}) [Status: {selected_job.get('status').capitalize()}]")
                        pause()
                        return selected_job['id']
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number or 'b'.")
        except Exception as e:
            print(f"Error retrieving jobs: {e}")
            pause()
            return None

def _record_transaction_flow(agent_pearl, active_job_pearl_id: str, test_mode: bool = False):
    """
    Handles the flow for recording a transaction for the active job.
    """
    clear(test_mode=test_mode)
    print(f"Record Transaction for Job ID: {active_job_pearl_id}")
    print("------------------------------------")

    item = input("Enter item name: ").strip()
    cost_str = input("Enter cost: ").strip()
    payment = input("Enter payment method: ").strip()
    sku = input("Enter SKU (optional): ").strip()

    if not item or not cost_str or not payment:
        print("Item, cost, and payment method are required.")
        pause()
        return

    try:
        cost = float(cost_str)
    except ValueError:
        print("Invalid cost. Please enter a numeric value.")
        pause()
        return

    try:
        # Assuming agent_pearl has a method to record transactions
        # This method needs to be implemented in agent_pearl.py
        agent_pearl.record_transaction(
            pearl_id=active_job_pearl_id,
            item=item,
            cost=cost,
            payment=payment,
            sku=sku if sku else None
        )
        print(f"Transaction recorded successfully for Job ID: {active_job_pearl_id}")
    except Exception as e:
        print(f"Error recording transaction: {e}")
    pause()



def _delete_vault_file_flow(agent_pearl, test_mode: bool = False):
    """
    Handles the flow for deleting a vault file.
    """
    clear(test_mode=test_mode)
    print("Delete Vault File")
    print("-----------------")
    confirm = input("Are you sure you want to delete the current vault file? (y/N): ").strip().lower()
    if confirm == 'y':
        vault_door_password = input("Enter Vault Door password to confirm deletion: ").strip()
        identity_password = input("Enter Identity password to confirm deletion: ").strip()
        metadata_password = input("Enter Metadata password to confirm deletion: ").strip()

        if not vault_door_password or not identity_password or not metadata_password:
            print("All three passwords are required to delete the vault. Deletion cancelled.")
            pause()
            return

        try:
            agent_pearl.delete_vault_file(vault_door_password, identity_password, metadata_password)
            print("Vault file deleted successfully.")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    else:
        print("Vault file deletion cancelled.")
    pause()

def _view_vault_metadata_flow(agent_pearl, test_mode: bool = False):
    """
    Handles the flow for viewing vault metadata.
    """
    clear(test_mode=test_mode)
    print("View Vault Metadata")
    print("-------------------")
    try:
        metadata = agent_pearl.get_vault_metadata()
        if metadata:
            print("\nVault Metadata:")
            print(json.dumps(metadata, indent=2))
        else:
            print("No metadata found or vault is locked.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    pause()

def _lock_vault_flow(agent_pearl, test_mode: bool = False):
    """
    Handles the flow for locking the current vault.
    """
    print("\nLocking current vault...")
    try:
        agent_pearl.vault.lock_vault()
        print("Vault locked successfully.")
    except Exception as e:
        print(f"Error locking vault: {e}")
    pause()

def _load_existing_vault_flow(agent_pearl, test_mode: bool = False):
    """
    Handles the flow for loading an existing vault, offering multiple unlock methods.
    """
    while True:
        clear(test_mode=test_mode)
        print("Load Existing Vault")
        print("-------------------")
        print_menu("Select Unlock Method", ["Individual Passwords", "Master Key Seed", "Limited Access Credentials", "Back to Vault Management"])
        choice = get_user_input("Enter your choice")

        result = None
        if choice == "1":
            vault_door_password = get_user_input("Enter Vault Door password")
            identity_password = get_user_input("Enter Identity password")
            metadata_password = get_user_input("Enter Metadata password")
            result = agent_pearl.load_vault(vault_door_password, identity_password, metadata_password)
        elif choice == "2":
            master_key_seed = get_user_input("Enter Master Key Seed")
            result = agent_pearl.unlock_vault_with_master_key_seed(master_key_seed)
        elif choice == "3":
            limited_access_id = get_user_input("Enter Limited Access ID")
            limited_access_password = get_user_input("Enter Limited Access Password")
            result = agent_pearl.unlock_vault_with_limited_access_credentials(limited_access_id, limited_access_password)
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")

        if result:
            print(result)
        pause()

def _create_new_vault_flow(agent_pearl, test_mode: bool = False):
    """
    Handles the flow for creating a new vault.
    """
    clear(test_mode=test_mode)
    print("Create New Vault")
    print("----------------")
    vault_door_password = input("Enter a new Vault Door password: ").strip()
    identity_password = input("Enter a new Identity password: ").strip()
    metadata_password = input("Enter a new Metadata password: ").strip()
    seed = input("Enter a seed string (e.g., 'user:john.doe:department:sales') or leave blank for random: ").strip()
    if not seed:
        seed = seedtools.generate_random_seed_string()
        print(f"Generated random seed: {seed}")

    metadata_input = input("Enter metadata as JSON (optional): ").strip()
    metadata = json.loads(metadata_input) if metadata_input else None

    overwrite_choice = input("Overwrite existing vault if it exists? (y/N): ").strip().lower()
    overwrite = (overwrite_choice == 'y')

    result = agent_pearl.create_vault(vault_door_password, identity_password, seed, metadata_password, metadata, overwrite=overwrite)
    print(result)
    pause()

def _get_and_confirm_password(prompt: str) -> str | None:
    """
    Prompts the user for a password and confirms it.

    Args:
        prompt (str): The prompt message to display to the user.

    Returns:
        str | None: The confirmed password, or None if passwords do not match.
    """
    password = input(prompt)
    confirm_password = input("Confirm password: ")
    if password == confirm_password:
        return password
    else:
        print("Passwords do not match.")
        return None

def _get_optional_metadata_input() -> dict:
    """
    Prompts the user for optional metadata as a JSON string and parses it.
    """
    metadata_input = input("Enter optional metadata as a JSON string or leave blank: ").strip()
    metadata = {}
    if metadata_input:
        try:
            metadata = json.loads(metadata_input)
        except json.JSONDecodeError:
            print("Invalid JSON metadata. Vault will be created without metadata.")
    return metadata

def _view_transactions_flow(agent_pearl, active_job_pearl_id: str, test_mode: bool = False):
    """
    Handles the flow for viewing transactions for a given PEARL ID.
    """
    clear(test_mode=test_mode)
    print(f"Transactions for Job ID: {active_job_pearl_id}")
    print("------------------------------------")

    try:
        transactions = agent_pearl.get_transactions_for_pearl_id(active_job_pearl_id)
        if transactions:
            for tx in transactions:
                print(f"  Item: {tx['item']}, Cost: {tx['cost']:.2f}, Payment: {tx['payment']}, SKU: {tx['sku'] if tx['sku'] else 'N/A'}, Date: {tx['timestamp']}")
        else:
            print(f"No transactions found for Job ID: {active_job_pearl_id}")
    except Exception as e:
        print(f"Error retrieving transactions: {e}")
    pause()

def _mark_job_status_flow(agent_pearl, pearl_id: str, new_status: str, test_mode: bool = False):
    """
    Handles the flow for marking a job with a new status (finished or deleted).
    """
    clear(test_mode=test_mode)
    print(f"Mark Job {pearl_id} as {new_status.capitalize()}")
    print("-------------------------------------")

    confirm = input(f"Are you sure you want to mark job {pearl_id} as {new_status}? (y/N): ").strip().lower()
    if confirm == 'y':
        try:
            agent_pearl.update_job_status(pearl_id, new_status)
            print(f"Job {pearl_id} successfully marked as {new_status}.")
        except Exception as e:
            print(f"Error updating job status: {e}")
    else:
        print(f"Operation cancelled. Job {pearl_id} remains {agent_pearl.get_pearl_id_status(pearl_id)}.")
    pause()