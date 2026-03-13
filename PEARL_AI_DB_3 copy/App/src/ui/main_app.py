import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import streamlit as st
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
import uuid
import hashlib

from App.src.core.database.data_access import DataAccess
from App.src.core.database.pearl_qlite.pearl_qlite import PearlClient
from App.src.core.security.vault import Vault
from App.src.agent_pearl import agent_pearl

from App.src.ui.streamlit_cache_utils import (
    get_all_distinct_pearl_ids_from_all_tables_cached,
    get_all_pearl_id_groups_cached,
    get_pearl_ids_in_group_cached,
    get_all_pearl_ids_in_active_group_cached,
    get_pearl_client_cached,
    get_data_access_cached,
    get_agent_pearl_cached
)
from App.src.ui.pages.csv_import import render_csv_import_page
from App.src.ui.db_management_utils import export_user_data_to_new_db, verify_exported_db
from App.config.sql_categories import SQL_CATEGORIES

# --- Absolute Path Setup ---
# Define the absolute path to the databases directory
db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core', 'database', 'databases'))
# Define the absolute path to the default database
default_db_path = os.path.join(db_dir, "pearl_database.db")


# Initialize session state variables if they don't exist
if"pearl_id" not in st.session_state:
    st.session_state.pearl_id = None
if"active_group_id" not in st.session_state:
    st.session_state.active_group_id = None
if"vault_unlocked" not in st.session_state:
    st.session_state.vault_unlocked = False
if"vault_manager" not in st.session_state:
    st.session_state.vault_manager = None
if"db_path" not in st.session_state:
    st.session_state.db_path = default_db_path # Ensure db_path is always initialized to an absolute path

if"agent_pearl" not in st.session_state:
    st.session_state.agent_pearl = None
if"pearl_id_modified" not in st.session_state:
    st.session_state.pearl_id_modified = False
if"vault_read_only" not in st.session_state:
    st.session_state.vault_read_only = False
if"unlock_method_selection" not in st.session_state:
    st.session_state.unlock_method_selection = "Individual Passwords"
if"displayed_master_pearl_id" not in st.session_state:
    st.session_state.displayed_master_pearl_id = None
if"display_master_pearl_id_info" not in st.session_state:
    st.session_state.display_master_pearl_id_info = False
if"displayed_master_pearl_seed" not in st.session_state:
    st.session_state.displayed_master_pearl_seed = None
if"display_master_pearl_seed_info" not in st.session_state:
    st.session_state.display_master_pearl_seed_info = False


if"active_group_context_selector_uuid" not in st.session_state:
    st.session_state.active_group_context_selector_uuid = str(uuid.uuid4())

if"sql_dir" not in st.session_state:
    st.session_state.sql_dir = None



def render_database_selection_ui(db_dir: str):
    """
    Renders the UI for selecting an existing database or creating a new one.
    """
    st.subheader("Database Selection")

    os.makedirs(db_dir, exist_ok=True) # Ensure the directory exists

    db_files = sorted([f for f in os.listdir(db_dir) if f.endswith(('.db', '.sqlite'))])

    current_db_path = st.session_state.get("db_path", "pearl_database.db")
    current_db_name = os.path.basename(current_db_path)

    # Option to select an existing database
    st.write("### Select Existing Database")
    if db_files:
        # Add current_db_name to the options if it's not already there and is a valid file
        if current_db_name not in db_files and os.path.exists(current_db_path):
            db_files.insert(0, current_db_name)

        selected_db_name = st.selectbox(
            "Choose a database file:",
            options=db_files,
            index=db_files.index(current_db_name) if current_db_name in db_files else 0,
            key="db_selector"
        )

        if selected_db_name != current_db_name:
            st.session_state.db_path = os.path.join(db_dir, selected_db_name)
            st.success(f"Database set to: {selected_db_name}")
            st.rerun()
    else:
        st.info("No existing database files found. Please create a new one.")

    st.markdown("---")

    # Option to upload an existing database is now handled in main() before this function is called

    # Option to create a new database
    st.write("### Create New Database")
    with st.form("create_new_db_form"):
        new_db_name_input = st.text_input("Enter name for new database (e.g., 'my_new_db.db'):", key="new_db_name_input")
        create_db_button = st.form_submit_button("Create Database")

        if create_db_button:
            if new_db_name_input:
                if not (new_db_name_input.endswith(".db") or new_db_name_input.endswith(".sqlite")):\
                    new_db_name_input += ".db"

                new_db_full_path = os.path.join(db_dir, new_db_name_input)
                if os.path.exists(new_db_full_path):
                    st.error(f"A database named '{new_db_name_input}' already exists. Please choose a different name.")
                else:
                    try:
                        # Create an empty database file by connecting to it
                        conn = sqlite3.connect(new_db_full_path)
                        conn.close()
                        st.success(f"Database '{new_db_name_input}' created successfully!")
                        st.session_state.db_path = new_db_full_path
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating database: {e}")
            else:
                st.error("Database name cannot be empty.")

def get_data_access(db_path: str) -> DataAccess:
    """
    Returns a DataAccess instance, ensuring the database is initialized.
    """
    # Ensure the database is initialized before getting cached instances
    # Check if pearl_ids table exists, if not, initialize the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pearl_ids';")
    table_exists = cursor.fetchone()
    conn.close()

    # Database initialization is now handled by PearlClient internally.

    # sql_dir is now managed by PearlClient

    # Use cached PearlClient and DataAccess
    pearl_client = get_pearl_client_cached(db_path)
    dal = get_data_access_cached(db_path, pearl_client.sql_dir)
    st.session_state.sql_dir = pearl_client.sql_dir

    # Store pearl_client and data_access in session_state for backward compatibility
    # with existing code that might directly access st.session_state.pearl_client or st.session_state.data_access
    st.session_state.pearl_client = pearl_client
    st.session_state.data_access = dal

    agent_pearl_vault_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core', 'security', 'vault.vault'))
    st.session_state.agent_pearl = get_agent_pearl_cached(db_name=db_path, vault_path=agent_pearl_vault_path)

    return dal

def render_vault_management_ui(dal: DataAccess):
    """
    Renders the UI for vault management, including unlocking, locking, and credential updates.
    """
    st.subheader("Vault Management")

    vault_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core', 'security', 'vault.vault'))
    vault_exists = os.path.exists(vault_file_path)

    # Create New Vault Section - Always visible in Vault Management
    with st.expander("Create New Vault"):
        st.info("Create a new vault file. This will overwrite an existing vault if one is present.")
        with st.form("create_vault_form"):
            st.write("Enter details for the new vault:")
            new_vault_door_password = st.text_input("Vault Door Password", type="password", key="new_vault_door_password")
            new_identity_password = st.text_input("Identity Password", type="password", key="new_identity_password")
            new_metadata_password = st.text_input("Metadata Password", type="password", key="new_metadata_password")
            new_seed = st.text_input("Seed (e.g., tenant:acme:project:harbor)", key="new_seed")
            create_button = st.form_submit_button("Create Vault")

            if create_button:
                if new_vault_door_password and new_identity_password and new_metadata_password and new_seed:
                    try:
                        st.session_state.agent_pearl.create_vault(
                            vault_door_password=new_vault_door_password,
                            identity_password=new_identity_password,
                            metadata_password=new_metadata_password,
                            seed=new_seed,
                            overwrite=True # Allow overwriting for simplicity in this UI
                        )
                        st.success("Vault created successfully!")
                        # Construct the master_pearl_id_seed from the inputs
                        constructed_master_seed = (
                            f"vault_door_password:{new_vault_door_password};"
                            f"identity_password:{new_identity_password};"
                            f"metadata_password:{new_metadata_password}"
                        )

                        # Automatically unlock the vault with the newly created seed
                        try:
                            result = st.session_state.agent_pearl.unlock_vault_with_master_key_seed(constructed_master_seed)
                            if result["status"] == "success":
                                st.session_state.vault_unlocked = True
                                st.success("Vault automatically unlocked after creation.")
                                get_all_distinct_pearl_ids_from_all_tables_cached.clear() # Clear cache after successful unlock
                                st.rerun()
                                # Display the constructed master unlock string to the user AFTER rerun
                                st.info(f"Your Vault Unlock String (save this!): `{constructed_master_seed}`")
                            else:
                                st.error(f"Failed to automatically unlock vault after creation: {result['message']}")
                        except Exception as e:
                            st.error(f"An unexpected error occurred during automatic vault unlock after creation: {e}")
                    except Exception as e:
                        st.error(f"An unexpected error occurred during vault creation: {e}")
                else:
                    st.error("All password and seed fields are required to create a vault.")

    st.markdown("---") # Separator for clarity

    if st.session_state.vault_unlocked:
        st.success("Vault is unlocked.")
        if st.button("Lock Vault"):
            st.session_state.vault_unlocked = False
            st.session_state.vault_manager = None
            st.session_state.vault_read_only = False # Reset read-only status on lock
            st.success("Vault locked.")
            st.rerun()

        # Create Limited Access Entry Section (only if unlocked and not read-only)
        if not st.session_state.get("vault_read_only", False):
            with st.expander("Create Limited Access Entry"):
                st.info("Create a new limited access entry for this unlocked vault.")
                with st.form("create_limited_access_form"):
                    limited_access_id = st.text_input("Limited Access ID", key="new_limited_access_id")
                    limited_access_password = st.text_input("Limited Access Password", type="password", key="new_limited_access_password")

                    # The vault passwords are required to create a limited access entry
                    # as the AgentPearl.create_limited_access_entry method requires them.
                    # These are the passwords that were used to unlock the vault.
                    # For now, we'll ask the user to re-enter them.
                    st.write("Re-enter the vault Master PEARL ID Seed to create the limited access entry:")
                    master_pearl_id_seed_for_la = st.text_input("Master PEARL ID Seed (for current vault)", type="password", key="create_la_master_pearl_id_seed")

                    create_la_button = st.form_submit_button("Create Limited Access Entry")

                    if create_la_button:
                        if limited_access_id and limited_access_password and master_pearl_id_seed_for_la:
                            try:
                                result = st.session_state.agent_pearl.create_limited_access_entry(
                                    limited_access_id=limited_access_id,
                                    limited_access_password=limited_access_password,
                                    master_pearl_id_seed=master_pearl_id_seed_for_la
                                )
                                if result["status"] == "success":
                                    st.success(result["message"])
                                else:
                                    st.error(result["message"])
                            except Exception as e:
                                st.error(f"An unexpected error occurred: {e}")
                        else:
                            st.error("All fields are required to create a limited access entry.")

        st.markdown("---")

        if st.session_state.get("display_master_pearl_id_info", False):
            st.info(f"Your Vault's Unique Identifier (Master PEARL ID): `{st.session_state.displayed_master_pearl_id}`")
            st.session_state.display_master_pearl_id_info = False

        if st.session_state.get("display_master_pearl_seed_info", False):
            st.info(f"Your Master PEARL ID Seed (save this!): `{st.session_state.displayed_master_pearl_seed}`")
            st.session_state.display_master_pearl_seed_info = False

        # Update Vault Credentials Section (only if unlocked and not read-only)
        if not st.session_state.get("vault_read_only", False):
            with st.expander("Update Vault Credentials"):
                st.info("Vault is currently unlocked. You can update its credentials below.")
                with st.form(f"update_vault_form_{st.session_state.db_path}"):
                    st.write("Enter new details to update the vault file. This will overwrite the existing vault.")
                    update_vault_door_password = st.text_input("New Vault Door Password", type="password", key="update_vault_door_password")
                    update_identity_password = st.text_input("New Identity Password", type="password", key="update_identity_password")
                    update_metadata_password = st.text_input("New Metadata Password", type="password", key="update_metadata_password")
                    update_seed = st.text_input("New Seed (e.g., tenant:acme:project:harbor)", key="update_seed")
                    update_vault_button = st.form_submit_button("Update Vault")

                    if update_vault_button:
                        if update_vault_door_password and update_identity_password and update_metadata_password and update_seed:
                            try:
                                st.session_state.agent_pearl.create_vault(
                                    vault_door_password=update_vault_door_password,
                                    identity_password=update_identity_password,
                                    metadata_password=update_metadata_password,
                                    seed=update_seed,
                                    overwrite=True  # Overwrite the existing vault
                                )
                                st.success("Vault credentials updated successfully!")
                                # Construct the master_pearl_id_seed from the inputs
                                constructed_master_seed = (
                                    f"vault_door_password:{update_vault_door_password};"
                                    f"identity_password:{update_identity_password};"
                                    f"metadata_password:{update_metadata_password}"
                                )

                                # Automatically unlock the vault with the newly created seed
                                try:
                                    result = st.session_state.agent_pearl.unlock_vault_with_master_key_seed(constructed_master_seed)
                                    if result["status"] == "success":
                                        st.session_state.vault_unlocked = True
                                        st.success("Vault automatically unlocked after update.")
                                        get_all_distinct_pearl_ids_from_all_tables_cached.clear() # Clear cache after successful unlock
                                        st.rerun()
                                        # Display the constructed master unlock string to the user AFTER rerun
                                        st.info(f"Your New Vault Unlock String (save this!): `{constructed_master_seed}`")
                                    else:
                                        st.error(f"Failed to automatically unlock vault after update: {result['message']}")
                                except Exception as e:
                                    st.error(f"An unexpected error occurred during automatic vault unlock after update: {e}")
                            except Exception as e:
                                st.error(f"An unexpected error occurred during vault update: {e}")
                        else:
                            st.error("All password and seed fields are required to update a vault.")

        st.markdown("---")

        # Delete Vault Section (only if unlocked and not read-only)
        if not st.session_state.get("vault_read_only", False):
            with st.expander("Delete Vault File"):
                st.warning("This action will permanently delete the vault file. This cannot be undone.")
                if st.button("Delete Vault", key="delete_vault_button"):
                    if os.path.exists(vault_file_path):
                        try:
                            os.remove(vault_file_path)
                            st.success("Vault file deleted successfully.")
                            st.session_state.vault_unlocked = False
                            st.session_state.vault_manager = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting vault file: {e}")
                    else:
                        st.info("No vault file found to delete.")

        st.markdown("---")

    else: # Vault is locked
        st.info("Vault is locked. Please unlock to access sensitive data.")

        if vault_exists:
            # Unlock Existing Vault Section
            with st.expander("Unlock Vault"):
                st.info("A vault file exists. Please unlock it to proceed.")

                # Unlock method selection
                unlock_method = st.radio(
                    "Select Unlock Method:",
                    ("Individual Passwords", "Master Key Seed", "Limited Access Credentials"),
                    key="unlock_method_selection"
                )


                if unlock_method == "Individual Passwords":
                    with st.form("unlock_vault_passwords_form"):
                        st.write("Enter the passwords for the vault:")
                        vault_door_password = st.text_input("Vault Door Password", type="password", key="unlock_vault_door_password")
                        identity_password = st.text_input("Identity Password", type="password", key="unlock_identity_password")
                        metadata_password = st.text_input("Metadata Password", type="password", key="unlock_metadata_password")
                        unlock_button = st.form_submit_button("Unlock Vault")

                        if unlock_button:
                            if vault_door_password and identity_password and metadata_password:
                                try:
                                    result = st.session_state.agent_pearl.load_vault(
                                        vault_door_password=vault_door_password,
                                        identity_password=identity_password,
                                        metadata_password=metadata_password
                                    )
                                    if"unlocked successfully" in result:
                                        st.session_state.vault_unlocked = True
                                        st.session_state.vault_read_only = False # load_vault implies full access
                                        master_pearl_id = st.session_state.agent_pearl.get_master_pearl_id()
                                        st.session_state.pearl_id = master_pearl_id # Set active PEARL ID
                                        st.session_state.data_access.set_pearl_id(st.session_state.pearl_id)
                                        st.success("Vault unlocked successfully!") # Use a static success message

                                        # Construct the master_key_seed from the inputs for display
                                        constructed_master_seed = (
                                            f"vault_door_password:{vault_door_password};"
                                            f"identity_password:{identity_password};"
                                            f"metadata_password:{metadata_password}"
                                        )
                                        st.info(f"Your Vault Unlock String (Master Key Seed for Individual Passwords): `{constructed_master_seed}`")

                                        st.session_state.displayed_master_pearl_id = master_pearl_id
                                        st.session_state.display_master_pearl_id_info = True
                                        st.session_state.displayed_master_pearl_seed = constructed_master_seed
                                        st.session_state.display_master_pearl_seed_info = True
                                        st.rerun()
                                    else:
                                        st.error(f"Vault unlock failed: {result}") # Display the error string
                                except Exception as e:
                                    st.error(f"An unexpected error occurred during vault unlock: {e}")
                            else:
                                st.error("All password fields are required to unlock the vault.")

                elif unlock_method == "Master Key Seed":
                    with st.form("unlock_vault_seed_form"):
                        st.write("Enter the Master Key Seed:")
                        master_key_seed = st.text_input("Master Key Seed", type="password", key="unlock_master_key_seed")
                        unlock_seed_button = st.form_submit_button("Unlock Vault with Seed")

                        if unlock_seed_button:
                            if master_key_seed:
                                try:
                                    result = st.session_state.agent_pearl.unlock_vault_with_master_key_seed(master_key_seed)
                                    if result["status"] == "success":
                                        st.session_state.vault_unlocked = True
                                        st.session_state.vault_read_only = result.get("read_only", False)
                                        master_pearl_id = st.session_state.agent_pearl.get_master_pearl_id()
                                        st.session_state.pearl_id = master_pearl_id # Set active PEARL ID
                                        st.session_state.data_access.set_pearl_id(st.session_state.pearl_id)
                                        st.success(result["message"])
                                        get_all_distinct_pearl_ids_from_all_tables_cached.clear() # Clear cache after successful unlock
                                        st.session_state.displayed_master_pearl_id = master_pearl_id
                                        st.session_state.display_master_pearl_id_info = True
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to unlock vault with seed: {result['message']}")
                                except Exception as e:
                                    st.error(f"An unexpected error occurred during vault unlock with seed: {e}")
                            else:
                                st.error("Master Key Seed is required to unlock the vault.")

                elif unlock_method == "Limited Access Credentials":
                    with st.form("unlock_vault_limited_access_form"):
                        st.write("Enter your Limited Access ID and Password:")
                        limited_access_id = st.text_input("Limited Access ID", key="unlock_limited_access_id")
                        limited_access_password = st.text_input("Limited Access Password", type="password", key="unlock_limited_access_password")
                        unlock_la_button = st.form_submit_button("Unlock Vault with Limited Access")

                        if unlock_la_button:
                            if limited_access_id and limited_access_password:
                                try:
                                    result = st.session_state.agent_pearl.unlock_vault_with_limited_access_credentials(
                                        limited_access_id=limited_access_id,
                                        limited_access_password=limited_access_password
                                    )
                                    if result["status"] == "success":
                                        st.session_state.vault_unlocked = True
                                        st.session_state.vault_read_only = result.get("read_only", True) # Limited access should always be read-only
                                        st.session_state.pearl_id = result.get("pearl_id") # Set active PEARL ID if returned
                                        if st.session_state.pearl_id:
                                            st.session_state.data_access.set_pearl_id(st.session_state.pearl_id)
                                            st.session_state.displayed_master_pearl_id = st.session_state.pearl_id
                                            st.session_state.display_master_pearl_id_info = True
                                        st.success(result["message"])
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to unlock vault with limited access: {result['message']}")
                                except Exception as e:
                                    st.error(f"An unexpected error occurred during limited access vault unlock: {e}")
                            else:
                                st.error("Limited Access ID and Password are required to unlock the vault.")


from App.src.ui.pages.common import render_common_page
from App.src.ui.pages.home import render_home_page
from App.src.ui.pages.job_costing import render_job_costing_page
from App.src.ui.pages.contacts import render_contacts_page
from App.src.ui.pages.accounting import render_accounting_page
from App.src.ui.pages.reports import render_reports_page
from App.src.ui.pages.contacts import render_contacts_page
from App.src.ui.pages.query_builder_page import render_query_builder_page

def full_session_reset(clear_db_path: bool = False):
    """
    Performs a hard reset of the Streamlit session state and all related caches.
    If clear_db_path is True, st.session_state.db_path will be cleared.
    """
    keys_to_delete = list(st.session_state.keys())
    if not clear_db_path and "db_path" in keys_to_delete:
        keys_to_delete.remove("db_path")
    for key in keys_to_delete:
        del st.session_state[key]
    # Aggressively clear all relevant caches as a final measure
    get_data_access_cached.clear()
    get_pearl_client_cached.clear()
    get_all_distinct_pearl_ids_from_all_tables_cached.clear()
    get_agent_pearl_cached.clear()

def handle_database_change():
    """
    Renders the database selection UI and handles changes.
    If a change is detected (upload, selection, creation), it resets the session and reruns.
    This function must be called at the very top of the main app logic.
    """
    st.sidebar.subheader("Database Selection")
    db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core', 'database', 'databases'))
    os.makedirs(db_dir, exist_ok=True)

    st.sidebar.warning(f"handle_database_change start - st.session_state.db_path: `{st.session_state.get('db_path')}`")

    # --- Handle Upload --- #
    uploaded_db = st.sidebar.file_uploader("Upload a .db or .sqlite file", type=["db", "sqlite"], key="db_uploader")
    if uploaded_db is not None:
        save_path = os.path.join(db_dir, uploaded_db.name)
        st.sidebar.info(f"Upload detected. Target path: `{save_path}`")
        if st.session_state.get("db_path") != save_path:
            st.sidebar.info("" "New file detected. Processing upload and reset...")
            with open(save_path, "wb") as f:
                f.write(uploaded_db.getbuffer())

            new_db_path = save_path
            st.sidebar.info(f"Before full_session_reset - st.session_state.db_path: `{st.session_state.get('db_path')}`")
            full_session_reset(clear_db_path=False)
            st.session_state.db_path = new_db_path
            st.sidebar.success(f"After full_session_reset and set - st.session_state.db_path: `{st.session_state.get('db_path')}`")
            st.success(f"Database '{uploaded_db.name}' uploaded. Please unlock the vault.")
            st.rerun()

    # --- Handle Selection and Creation --- #
    db_files = sorted([f for f in os.listdir(db_dir) if f.endswith(('.db', '.sqlite'))])
    current_db_path = st.session_state.get("db_path", default_db_path) # Use default_db_path here
    current_db_name = os.path.basename(current_db_path)

    st.sidebar.info(f"handle_database_change - current_db_path for selection: `{current_db_path}`")

    if db_files:
        # Add current_db_name to the options if it's not already there and is a valid file
        if current_db_name not in db_files and os.path.exists(current_db_path):
            db_files.insert(0, current_db_name)

        selected_db_name = st.sidebar.selectbox(
            "Choose a database file:",
            options=db_files,
            index=db_files.index(current_db_name) if current_db_name in db_files else 0,
            key="db_selector"
        )

        if selected_db_name != current_db_name:
            new_db_path = os.path.join(db_dir, selected_db_name)
            st.sidebar.info(f"Before full_session_reset (selection) - st.session_state.db_path: `{st.session_state.get('db_path')}`")
            full_session_reset(clear_db_path=False)
            st.session_state.db_path = new_db_path
            st.sidebar.success(f"After full_session_reset and set (selection) - st.session_state.db_path: `{st.session_state.get('db_path')}`")
            st.success(f"Database switched to '{selected_db_name}'. Please unlock the vault.")
            st.rerun()
    else:
        st.sidebar.info("No databases found. Please create one.")

    with st.sidebar.form("create_new_db_form"):
        new_db_name_input = st.text_input("Or create a new database:")
        create_db_button = st.form_submit_button("Create")
        if create_db_button and new_db_name_input:
            if not (new_db_name_input.endswith(".db") or new_db_name_input.endswith(".sqlite")):
                new_db_name_input += ".db"
            new_db_full_path = os.path.join(db_dir, new_db_name_input)
            if not os.path.exists(new_db_full_path):
                conn = sqlite3.connect(new_db_full_path)
                conn.close()
                new_db_path = new_db_full_path
                st.sidebar.info(f"Before full_session_reset (creation) - st.session_state.db_path: `{st.session_state.get('db_path')}`")
                full_session_reset(clear_db_path=False)
                st.session_state.db_path = new_db_path
                st.sidebar.success(f"After full_session_reset and set (creation) - st.session_state.db_path: `{st.session_state.get('db_path')}`")
                st.success(f"Database '{new_db_name_input}' created. Please create and unlock a vault.")
                st.rerun()
            else:
                st.error("Database already exists.")

    return st.session_state.db_path # Return the current active db_path


# Main application logic
def main():
    st.set_page_config(layout="wide")
    st.title("PEARL AI Database Interface")

    # --- PROTOCOL DEBUGGING ---
    st.sidebar.warning(f"Main start - st.session_state.db_path: `{st.session_state.get('db_path')}`")
    # --- END DEBUGGING ---

    # This function now handles all DB state changes and will rerun the app if a change occurs.
    # It must be the first thing to run.
    current_db_path = handle_database_change()

    # If the app continues past this point, the DB state is stable for this run.
    st.sidebar.info(f"Main() - Before get_data_access, current_db_path: `{current_db_path}`") # New debug line
    dal = get_data_access(current_db_path)
    st.session_state.sql_dir = st.session_state.pearl_client.sql_dir

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page_selection = st.sidebar.radio("Go to", [
        "Home",
        "Vault Management",
        "Job Cost Tracking",
        "CSV Import",
        "Contact Management",
        "Accounting",
        "Reports",
        "Query Builder"
    ])

    st.sidebar.markdown("---")
    st.sidebar.subheader("Active PEARL ID")

    # Display current PEARL ID if set
    if st.session_state.pearl_id:
        st.sidebar.success(f"Current PEARL ID: {st.session_state.pearl_id}")
    else:
        st.sidebar.warning("No PEARL ID set. Please unlock a vault or select one below.")

    # Allow selecting from existing PEARL IDs
    all_pearl_ids = get_all_distinct_pearl_ids_from_all_tables_cached(st.session_state.db_path, st.session_state.sql_dir)

    # Add a 'None' option if no PEARL ID is currently selected or if there are no existing IDs
    display_pearl_ids = ["None (Unlock Vault to Set)"] + sorted(list(all_pearl_ids))

    try:
        current_pearl_id_index = display_pearl_ids.index(st.session_state.pearl_id) if st.session_state.pearl_id in display_pearl_ids else 0
    except ValueError:
        current_pearl_id_index = 0 # Fallback if pearl_id is not in the list (e.g., from a deleted vault)

    selected_pearl_id_from_sidebar = st.sidebar.selectbox(
        "Select Active PEARL ID (Overrides Vault if selected)",
        options=display_pearl_ids,
        index=current_pearl_id_index,
        key="sidebar_pearl_id_selector"
    )

    # Handle selection change
    if selected_pearl_id_from_sidebar and selected_pearl_id_from_sidebar != "None (Unlock Vault to Set)":
        if st.session_state.pearl_id != selected_pearl_id_from_sidebar:
            st.session_state.pearl_id = selected_pearl_id_from_sidebar
            st.session_state.data_access.set_pearl_id(st.session_state.pearl_id)
            st.session_state.pearl_id_modified = True # Indicate that pearl_id was manually selected
            st.sidebar.success(f"Active PEARL ID set to: {st.session_state.pearl_id}")
            st.rerun()
    elif st.session_state.pearl_id is not None and selected_pearl_id_from_sidebar == "None (Unlock Vault to Set)":
        # If user explicitly selected 'None' and a PEARL ID was previously set
        st.session_state.pearl_id = None
        st.session_state.data_access.set_pearl_id(None)
        st.session_state.pearl_id_modified = True
        st.sidebar.warning("Active PEARL ID has been cleared.")
        st.rerun()

    st.sidebar.markdown("---") # Separator after PEARL ID section

    # Initialize session state for the export/delete workflow
    if 'download_generated' not in st.session_state:
        st.session_state.download_generated = False
    if 'backup_verified' not in st.session_state:
        st.session_state.backup_verified = False

    # Database Management Section
    st.sidebar.subheader("Database Management")
    with st.sidebar.expander("Export & Delete Your Data"):
        st.info("Step 1: Generate and download a backup of your data.")
        if st.button("Generate & Download Database"):
            if st.session_state.pearl_id:
                try:
                    original_db_name = os.path.basename(st.session_state.db_path).replace(".db", "").replace(".sqlite", "")
                    export_db_name = f"{original_db_name}_export_{st.session_state.pearl_id}.db"
                    export_db_full_path = os.path.join(os.path.dirname(st.session_state.db_path), export_db_name)

                    export_user_data_to_new_db(st.session_state.pearl_id, st.session_state.db_path, export_db_full_path)

                    with open(export_db_full_path, "rb") as fp:
                        st.download_button(
                            label="Download Your Database",
                            data=fp,
                            file_name=export_db_name,
                            mime="application/x-sqlite3"
                        )

                    # Clean up the temporary file
                    if os.path.exists(export_db_full_path):
                        os.remove(export_db_full_path)

                    st.success("Database generated successfully! Please download it and proceed to Step 2.")
                    st.session_state.download_generated = True
                    st.session_state.backup_verified = False # Reset verification status

                except Exception as e:
                    st.error(f"Error during database export: {e}")
            else:
                st.warning("Please set an active PEARL ID to export data.")

        if st.session_state.download_generated:
            st.markdown("---")
            st.info("Step 2: Upload the downloaded database to verify your backup.")
            uploaded_file = st.file_uploader("Upload your .db backup file", type=["db", "sqlite3"])

            if uploaded_file is not None:
                if verify_exported_db(uploaded_file):
                    st.success("Backup verified successfully! You can now proceed to delete your data.")
                    st.session_state.backup_verified = True
                else:
                    st.error("The uploaded file is not a valid backup. Please try downloading again.")
                    st.session_state.backup_verified = False

        if st.session_state.backup_verified:
            st.markdown("---")
            st.info("Step 3: Delete your data from the system.")
            st.warning("This action will permanently delete all data associated with your active PEARL ID from the database. This cannot be undone.")
            confirmation_text = st.text_input("Type 'DELETE MY DATA' to confirm:")
            if st.button("Delete Your Data"):
                if confirmation_text == "DELETE MY DATA":
                    if st.session_state.pearl_id:
                        try:
                            dal.delete_all_user_data(st.session_state.pearl_id)
                            st.success("All data for your PEARL ID has been deleted. The application will now reset.")
                            st.session_state.pearl_id = None # Explicitly clear pearl_id
                            full_session_reset(clear_db_path=True)
                            get_all_distinct_pearl_ids_from_all_tables_cached.clear() # Clear cache for pearl IDs
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting data: {e}")
                    else:
                        st.warning("Please set an active PEARL ID to delete data.")
                else:
                    st.error("Confirmation text does not match. Data not deleted.")



    if page_selection == "Home":
        render_home_page(dal)
    elif page_selection == "Vault Management":
        render_vault_management_ui(dal)
    elif page_selection == "Job Cost Tracking":
        render_job_costing_page(dal)
    elif page_selection == "CSV Import":
        render_csv_import_page()
    elif page_selection == "Contact Management":
        render_contacts_page(dal)
    elif page_selection == "Accounting":
        render_accounting_page(dal)
    elif page_selection == "Reports":
        render_reports_page(dal)
    elif page_selection == "Query Builder":
        render_query_builder_page(dal, st.session_state.sql_dir)

if __name__ == "__main__":
    main()
