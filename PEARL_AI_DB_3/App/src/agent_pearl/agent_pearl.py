import os
import logging
from ..core.database.pearl_qlite.pearl_qlite import PearlClient
from typing import Optional
from ..core.security.vault import Vault, VaultDecryptionError
from ..core.security.limited_access_key_store import LimitedAccessKeyStore
from ..core.seedtools.seedtools import seed_to_pearl_id, pearl_id_to_vector
from ai_text_to_sql import TextToSQL # type: ignore
from ai_text_to_sql.data_connectors import SQLiteConnector
from ai_text_to_sql.llm_connectors import OpenAIConnector
import uuid # Import uuid for generating limited access seeds
# from ..contract_executor import ContractExecutor # Uncomment when ContractExecutor is ready

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentPearl:
    """Orchestration agent for PEARL_AI_DB operations."""
    def __init__(self, db_name: str = "core/database/databases/project_mgmt_acct.db", vault_path: str = "core/security/vault.vault", pearl_client: Optional[PearlClient] = None):
        if pearl_client:
            self.pearl_client = pearl_client
        else:
            self.pearl_client = PearlClient(default_db=db_name)
        logger.debug(f"AgentPearl initialized with pearl_client: {self.pearl_client}")
        self.vault = Vault(vault_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), vault_path))
        self.limited_access_key_store: Optional[LimitedAccessKeyStore] = None
        self._limited_access_store_master_pearl_id: Optional[str] = None
        self._limited_access_store_seed: Optional[str] = None
        # self.contract_executor = ContractExecutor() # Uncomment when ContractExecutor is ready
        self.text_to_sql_converter = self._initialize_text_to_sql()

    def create_entity(self, entity_type: str, attributes: Optional[dict] = None, pearl_id: str = None, seed: str = None) -> str:
        """Creates a new entity and returns its PEARL_ID."""
        created_pearl_id = self.pearl_client.create_pearl_id(entity_type, attributes, pearl_id=pearl_id, seed=seed)
        print(f"Created {entity_type} with PEARL_ID: {created_pearl_id}")
        return created_pearl_id

    def record_transaction(self, pearl_id: str, item: str, cost: float, payment: str, sku: str = None):
        """
        Records a new transaction associated with a PEARL ID.
        """
        self.pearl_client.add_transaction(pearl_id, item, cost, payment, sku)
        print(f"Recorded transaction for PEARL ID {pearl_id}: {item} - {cost}")

    def get_transactions_for_pearl_id(self, pearl_id: str) -> list[dict]:
        """
        Retrieves all transactions associated with a given PEARL ID.
        """
        return self.pearl_client.get_transactions_by_pearl_id(pearl_id)

    def update_job_status(self, pearl_id: str, status: str):
        """
        Updates the status of a job (PEARL ID).

        Args:
            pearl_id (str): The PEARL ID of the job to update.
            status (str): The new status for the job (e.g., 'active', 'finished', 'deleted').
        """
        self.pearl_client.update_pearl_id_status(pearl_id, status)
        print(f"Updated status for PEARL ID {pearl_id} to {status}.")

    def get_pearl_id_status(self, pearl_id: str) -> str | None:
        """
        Retrieves the status of a job (PEARL ID).

        Args:
            pearl_id (str): The PEARL ID of the job to retrieve the status for.

        Returns:
            str | None: The status of the job, or None if not found.
        """
        return self.pearl_client.get_pearl_id_status(pearl_id)

    def get_entity(self, pearl_id: str) -> dict:
        """Retrieves an entity by its PEARL_ID."""
        return self.pearl_client.get_pearl_id(pearl_id)

    def execute_contract(self, contract_name: str, payload: dict):
        """Executes a contract via the ContractExecutor."""
        # if self.contract_executor:
        #     return self.contract_executor.execute(contract_name, payload)
        # else:
        print(f"ContractExecutor not initialized. Cannot execute contract: {contract_name}")
        return {"status": "error", "message": "ContractExecutor not available"}

    def _initialize_text_to_sql(self) -> TextToSQL:
        """
        Initializes the TextToSQL converter.
        """
        db_path = self.pearl_client.active_db
        if db_path == ":memory:":
            sqlite_connector = SQLiteConnector(database=":memory:")
        else:
            # For file-based databases, ensure the full path is used
            sqlite_connector = SQLiteConnector(database=db_path)
        openai_connector = OpenAIConnector(api_key=os.environ.get("OPENAI_API_KEY"))
        return TextToSQL(sqlite_connector, openai_connector)

    def run_query(self, query: str, params: tuple = ()):
        """Runs a direct SQL query against the active database."""
        results, column_names = self.pearl_client.execute_query(query, params)
        return results, column_names

    def query_database_nl(self, question: str) -> str:
        """
        Interprets natural language questions about the database and returns relevant information.
        Uses ai-text-to-sql for advanced NLQ, falling back to predefined commands if needed.
        """
        question_lower = question.lower()
        response_lines = []

        try:
            # Attempt to convert natural language to SQL using ai-text-to-sql
            sql_query = self.text_to_sql_converter.convert(question)
            if sql_query:
                print(f"Generated SQL: {sql_query}")
                results = self.pearl_client.execute_query(sql_query)
                if results:
                    # Attempt to get column names for header
                    conn = self.pearl_client._get_connection()
                    cursor = conn.cursor()
                    cursor.execute(sql_query) # Re-execute to get cursor description
                    if cursor.description:
                        column_names = [description[0] for description in cursor.description]
                        response_lines.append(", ".join(column_names))
                    for row in results:
                        response_lines.append(str(row))
                    conn.close()
                else:
                    response_lines.append("No data found for the generated query.")
                return "\n".join(response_lines)
            else:
                response_lines.append("ai-text-to-sql could not generate a SQL query. Falling back to predefined commands.")

            # Fallback to existing logic if ai-text-to-sql fails or returns no query
            if "list tables" in question_lower or "show tables" in question_lower:
                tables = self.pearl_client.get_all_table_names()
                if tables:
                    response_lines.append("Available tables:")
                    for table in tables:
                        response_lines.append(f"- {table}")
                else:
                    response_lines.append("No tables found in the database.")
            elif "list pearl ids" in question_lower or "show pearl ids" in question_lower:
                pearl_ids = self.get_all_pearl_ids()
                if pearl_ids:
                    response_lines.append("All PEARL IDs:")
                    for pearl_id_data in pearl_ids:
                        response_lines.append(f"ID: {pearl_id_data['id']}, Type: {pearl_id_data['entity_type']}, Attributes: {pearl_id_data['attributes']}, Vector: ({pearl_id_data['x']:.4f}, {pearl_id_data['y']:.4f}, {pearl_id_data['z']:.4f})")
                else:
                    response_lines.append("No PEARL IDs found.")
            elif "describe table" in question_lower or "schema for" in question_lower:
                table_name = None
                for keyword in ["describe table ", "schema for "]:
                    if keyword in question_lower:
                        parts = question_lower.split(keyword)
                        if len(parts) > 1:
                            table_name = parts[1].strip().split(' ')[0] # Get the first word after the keyword
                            break

                if table_name:
                    schema = self.pearl_client.get_table_columns(table_name)
                    if schema:
                        response_lines.append(f"Schema for table '{table_name}':")
                        for col_name in schema:
                            response_lines.append(f"- {col_name}")
                    else:
                        response_lines.append(f"Table '{table_name}' not found or no schema available.")
                else:
                    response_lines.append("Please specify a table name (e.g., 'describe table products').")
            elif "show me" in question_lower or "select from" in question_lower:
                table_name = None
                # Prioritize more specific keywords
                for keyword in ["show me data from ", "show me from ", "select from ", "show me "]:
                    if keyword in question_lower:
                        parts = question_lower.split(keyword)
                        if len(parts) > 1:
                            table_name = parts[1].strip().split(' ')[0] # Get the first word after the keyword
                            break

                if table_name:
                    # For now, just a simple select all with limit
                    results = self.pearl_client.execute_query(f"SELECT * FROM {table_name} LIMIT 5;")
                    if results:
                        response_lines.append(f"Sample data from '{table_name}':")
                        # Attempt to get column names for header
                        cursor = self.pearl_client._get_connection().cursor()
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 0;") # Get cursor description without fetching data
                        if cursor.description:
                            column_names = [description[0] for description in cursor.description]
                            response_lines.append(", ".join(column_names))
                        for row in results:
                            response_lines.append(str(row))
                    else:
                        response_lines.append(f"No data found in table '{table_name}'.")
                else:
                    response_lines.append("Please specify a table name (e.g., 'show me data from products').")
            else:
                response_lines.append("I can help with:")
                response_lines.append("1. 'list tables'")
                response_lines.append("2. 'describe table <name>'")
                response_lines.append("3. 'show me data from <name>'")
        except Exception as e:
            response_lines.append(f"An error occurred: {e}")
            response_lines.append("Please ensure the table name is correct and try again.")

        return "\n".join(response_lines)

    def get_all_pearl_ids(self) -> list[dict]:
        """
        Retrieves all PEARL IDs and their associated entity_type and attributes.

        Returns:
            list[dict]: A list of dictionaries, each representing a PEARL ID with its id, entity_type, and attributes.
        """
        return self.pearl_client.get_all_pearl_ids()

    def export_query_results(self, query: str, file_path: str, format: str) -> str:
        """
        Executes a SQL query and exports the results to a specified file in the given format.

        Args:
            query (str): The SQL query to execute.
            file_path (str): The path to the output file.
            format (str): The export format ('json', 'csv', 'txt').

        Returns:
            str: A message indicating the success or failure of the export.
        """
        try:
            with self.pearl_client._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
                column_headers = [description[0] for description in cursor.description]

            self.pearl_client.export_query_results(column_headers, results, file_path, format)
            return f"Query results successfully exported to {file_path} in {format} format."
        except Exception as e:
            return f"Error exporting query results: {e}"

    def add_crdt_log_entry(self, entry_type: str, entity_id: str, data: str):
        """
        Adds an entry to the CRDT log.
        """
        # Assuming pearl_client.add_crdt_log_entry expects entry_type and data separately for structured logging
        log_entry_content = f"Type: {entry_type}, Data: {data}"
        self.pearl_client.add_crdt_log_entry(entity_id, log_entry_content)

    def get_crdt_log(self) -> list[dict]:
        """
        Retrieves all entries from the CRDT log.
        """
        return self.pearl_client.get_crdt_log_entries()

    def increment_crdt_counter(self, counter_name: str, site_id: str, value: int = 1):
        """
        Increments a CRDT counter.
        """
        self.pearl_client.increment_crdt_counter(counter_name, site_id, value)

    def get_crdt_counter_value(self, counter_name: str) -> int:
        """
        Retrieves the current value of a CRDT counter.
        """
        return self.pearl_client.get_crdt_counter_value(counter_name)

    def create_vault(self, vault_door_password: str, identity_password: str, seed: str, metadata_password: str, metadata: Optional[dict] = None, overwrite: bool = False) -> str:
        """
        Creates a new encrypted vault file.
        """
        try:
            self.vault.create_new_vault(vault_door_password, identity_password, seed, metadata_password, metadata, overwrite=overwrite)
            # After creating the vault, initialize the limited access key store
            master_pearl_id = self.get_master_pearl_id()
            # Ensure the master_pearl_id is recorded in the pearl_ids table
            if not self.pearl_client.get_pearl_id(master_pearl_id):
                self.pearl_client.create_pearl_id(
                    entity_type="master_vault_id",
                    attributes={"source": "vault_creation"},
                    pearl_id=master_pearl_id,
                    seed=None # The pearl_id is already fully formed
                )
                logger.debug(f"Attempted to create pearl_id for vault_creation: {master_pearl_id}")
            self._initialize_limited_access_key_store(master_pearl_id)
            return "Vault created successfully."
        except FileExistsError as e:
            return str(e)

    def load_vault(self, vault_door_password: str, identity_password: str, metadata_password: str):
        """
        Loads and decrypts an existing vault file.
        """
        try:
            self.vault.load_vault(vault_door_password, identity_password, metadata_password)
            return "Vault unlocked successfully."
        except (FileNotFoundError, ValueError) as e:
            return str(e)

    def unlock_vault_with_master_key_seed(self, master_key_seed: str) -> dict:
        """
        Unlocks the vault using a master key seed.
        This method is intended for full access after a master key has been generated.

        Args:
            master_key_seed (str): The master key seed (concatenation of vault_door, identity, and metadata seeds).

        Returns:
            dict: A dictionary indicating the status of the unlock attempt.
        """
        try:
            parts = master_key_seed.split(';')
            vault_door_password = None
            identity_password = None
            metadata_password = None

            for part in parts:
                part = part.strip()
                if part.startswith("vault_door_password:"):
                    vault_door_password = part.split(":")[1]
                elif part.startswith("identity_password:"):
                    identity_password = part.split(":")[1]
                elif part.startswith("metadata_password:"):
                    metadata_password = part.split(":")[1]

            if not (vault_door_password and identity_password and metadata_password):
                raise ValueError("Invalid master PEARL ID seed format.")

            self.vault.load_vault(vault_door_password, identity_password, metadata_password)
            master_pearl_id = self.get_master_pearl_id()
            # Ensure the master_pearl_id is recorded in the pearl_ids table
            pearl_id_exists = self.pearl_client.get_pearl_id(master_pearl_id)
            logger.debug(f"Checking if Master PEARL ID {master_pearl_id} exists in DB: {pearl_id_exists}")
            if not pearl_id_exists:
                logger.debug(f"Calling create_pearl_id with pearl_id: {master_pearl_id}")
                self.pearl_client.create_pearl_id(
                    entity_type="master_vault_id",
                    attributes={"source": "vault_unlock_master_seed"},
                    pearl_id=master_pearl_id,
                    seed=None # The pearl_id is already fully formed
                )
                logger.debug(f"Attempted to create pearl_id for vault_unlock_master_seed: {master_pearl_id}")

            self._initialize_limited_access_key_store(master_pearl_id)
            return {"status": "success", "message": "Vault unlocked successfully with Master PEARL ID Seed.", "read_only": False}
        except (FileNotFoundError, ValueError, VaultDecryptionError) as e:
            return {"status": "error", "message": str(e), "read_only": True}
        except Exception as e:
            return {"status": "error", "message": f"An unexpected error occurred during master key seed unlock: {e}", "read_only": True}

    def unlock_vault_with_limited_access_credentials(self, limited_access_id: str, limited_access_password: str) -> dict:
        """
        Unlocks the vault using limited access credentials.
        This method attempts to retrieve the master key components from the limited access key store
        and then uses them to unlock the main vault.
        """
        if self.limited_access_key_store is None:
            return {"status": "error", "message": "Limited Access Key Store is not loaded. Cannot unlock with limited access.", "read_only": True}

        try:
            entry = self.limited_access_key_store.get_entry(limited_access_id, limited_access_password)
            if not entry:
                return {"status": "error", "message": "Invalid limited access ID or password.", "read_only": True}

            vault_door_password = entry.get("vault_door_password")
            identity_password = entry.get("identity_password")
            metadata_password = entry.get("metadata_password")

            if not (vault_door_password and identity_password and metadata_password):
                return {"status": "error", "message": "Limited access entry corrupted or incomplete.", "read_only": True}

            self.vault.load_vault(vault_door_password, identity_password, metadata_password)
            master_pearl_id = self.get_master_pearl_id()

            # Ensure the master_pearl_id is recorded in the pearl_ids table
            if not self.pearl_client.get_pearl_id(master_pearl_id):
                self.pearl_client.create_pearl_id(
                    entity_type="master_vault_id",
                    attributes={"source": "vault_unlock_limited_access"},
                    pearl_id=master_pearl_id,
                    seed=None # The pearl_id is already fully formed
                )
                logger.debug(f"Attempted to create pearl_id for vault_unlock_limited_access: {master_pearl_id}")

            self._initialize_limited_access_key_store(master_pearl_id)
            return {"status": "success", "message": "Vault unlocked successfully with limited access credentials.", "read_only": False}

        except (FileNotFoundError, ValueError, VaultDecryptionError) as e:
            return {"status": "error", "message": str(e), "read_only": True}
        except Exception as e:
            return {"status": "error", "message": f"An unexpected error occurred during limited access unlock: {e}", "read_only": True}

    def lock_vault(self):
        """
        Locks the vault, clearing sensitive data from memory.
        """
        self.vault.lock_vault()
        return "Vault locked."

    def get_vault_seed(self) -> str:
        """
        Retrieves the decrypted seed from the vault.
        """
        try:
            return self.vault.get_seed()
        except ValueError as e:
            return str(e)

    def get_master_pearl_id(self) -> str:
        """
        Retrieves the master PEARL ID from the vault.
        """
        try:
            return self.vault.get_master_pearl_id()
        except ValueError as e:
            return str(e)

    def _initialize_limited_access_key_store(self, master_pearl_id: str):
        """
        Initializes the LimitedAccessKeyStore.
        """
        if self.limited_access_key_store is None:
            self.limited_access_key_store = LimitedAccessKeyStore(
                store_file_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), "core/security/limited_access.vault")
            )
        # Set the master PEARL ID and seed for the limited access key store
        self._limited_access_store_master_pearl_id = master_pearl_id
        self._limited_access_store_seed = self.vault.get_seed()
        # Attempt to load the store, if it exists
        try:
            self.limited_access_key_store.load_store(
                self._limited_access_store_master_pearl_id,
                self._limited_access_store_seed
            )
            print("Limited Access Key Store loaded successfully.")
        except FileNotFoundError:
            print("Limited Access Key Store file not found. A new one will be created on first entry.")
        except Exception as e:
            print(f"Error loading Limited Access Key Store: {e}")

    def get_vault_metadata(self) -> dict:
        """
        Retrieves the decrypted metadata from the vault.
        """
        try:
            return self.vault.get_metadata()
        except ValueError as e:
            return str(e)

    def create_limited_access_entry(self, limited_access_id: str, limited_access_password: str, master_pearl_id_seed: str) -> dict:
        """
        Creates a limited access entry in the limited access key store.
        
        Args:
            limited_access_id: The ID for the limited access entry
            limited_access_password: The password for the limited access entry
            master_pearl_id_seed: The master PEARL ID seed (from the vault)
        
        Returns:
            dict: Status and message
        """
        try:
            # Get the vault credentials from the currently unlocked vault
            vault_door_password = self.vault.vault_door_password
            identity_password = self.vault.identity_password
            metadata_password = self.vault.metadata_password
            
            if not vault_door_password or not identity_password or not metadata_password:
                return {"status": "error", "message": "Vault is not fully unlocked. Cannot create limited access entry."}
            
            # Initialize the limited access key store if needed
            if self.limited_access_key_store is None:
                self._initialize_limited_access_key_store(self.vault.get_master_pearl_id())
            
            # Add the entry to the limited access key store
            self.limited_access_key_store.add_entry(
                limited_access_id=limited_access_id,
                limited_access_password=limited_access_password,
                vault_door_password=vault_door_password,
                identity_password=identity_password,
                metadata_password=metadata_password
            )
            
            # Save the store
            self.limited_access_key_store.save_store()
            
            return {"status": "success", "message": f"Limited access entry '{limited_access_id}' created successfully."}
            
        except Exception as e:
            logger.error(f"Error creating limited access entry: {e}")
            return {"status": "error", "message": f"Failed to create limited access entry: {str(e)}"}
