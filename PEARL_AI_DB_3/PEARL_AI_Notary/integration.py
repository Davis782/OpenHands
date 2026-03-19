"""
PEARL AI Notary - Integration Module
====================================

This module provides integration utilities to add the PEARL AI Notary
feature to the PEARL AI DB application.

USAGE:
------
In your main_app.py, add the following:

    # Import the notary integration
    from PEARL_AI_Notary.integration import get_notary_navigation_options, init_notary_system
    
    # Initialize notary system (call this before creating the DataAccess)
    notary_dal = init_notary_system(db_path)
    
    # Add notary to navigation options (modify your page_selection)
    notary_pages = get_notary_navigation_options()
    # Then add "Notary Dashboard" to your navigation list

"""

import os
from pathlib import Path
from typing import List, Dict, Any
from PEARL_AI_Notary.src.core import NotaryDataAccess


# SQL schema files to execute on initialization
SCHEMA_FILES = [
    '01_notaries.sql',
    '02_signers.sql',
    '03_documents.sql',
    '04_notary_sessions.sql',
    '05_state_rules.sql',
    '06_audit_logs.sql'
]


def get_notary_navigation_options() -> List[str]:
    """
    Returns the list of navigation page names for the notary system.
    
    Returns:
        List of page names for notary pages
    """
    return ['Notary Dashboard', 'Create Session', 'Manage Sessions', 'Audit Logs', 'State Rules']


def init_notary_system(db_path: str, sql_dir: str = None) -> NotaryDataAccess:
    """
    Initialize the notary system database schema.
    
    Args:
        db_path: Path to the SQLite database
        sql_dir: Path to the SQL schema files (defaults to module's sql folder)
    
    Returns:
        NotaryDataAccess instance for database operations
    """
    # Determine the SQL directory
    if sql_dir is None:
        # Get the directory of this integration module
        module_dir = Path(__file__).parent.parent
        sql_dir = str(module_dir / 'PEARL_AI_Notary' / 'sql')
    
    # Create database schema if needed
    _ensure_notary_schema(db_path, sql_dir)
    
    # Return the data access layer
    return NotaryDataAccess(db_path)


def _ensure_notary_schema(db_path: str, sql_dir: str):
    """
    Ensure the notary system tables exist by executing schema files.
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Execute each schema file using executescript for multi-line statements
        for schema_file in SCHEMA_FILES:
            schema_path = os.path.join(sql_dir, schema_file)
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                    conn.executescript(schema_sql)
        
        conn.commit()
        
        # Seed default state rules
        _seed_default_state_rules(conn)
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def _seed_default_state_rules(conn):
    """Seed default state rules if they don't exist"""
    import sqlite3
    
    cursor = conn.execute("SELECT COUNT(*) FROM state_rules")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Insert default state rules
        default_rules = [
            ('VA', 'Virginia', 1, 1, '["US", "International"]', 'NIST-IAL2', 5, 'VA_RON_2026'),
            ('TX', 'Texas', 1, 1, '["US"]', 'NIST-IAL2', 5, 'TX_RON_2026'),
            ('FL', 'Florida', 1, 1, '["US", "International"]', 'NIST-IAL2', 5, 'FL_RON_2026'),
            ('NY', 'New York', 1, 1, '["US"]', 'NIST-IAL2', 5, 'NY_RON_2026'),
            ('CA', 'California', 0, 1, '[]', 'NIST-IAL2', 5, 'CA_RON_2026'),
        ]
        
        conn.executemany("""
            INSERT INTO state_rules 
            (state_code, state_name, ron_allowed, notary_location_required,
             signer_location_allowed, id_verification, retention_years, certificate_template)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, default_rules)
        
        conn.commit()


def get_notary_pages() -> Dict[str, Any]:
    """
    Returns a dictionary mapping page names to render functions.
    
    This is useful for dynamic page rendering based on selection.
    
    Returns:
        Dictionary with page names as keys and render functions as values
    """
    from PEARL_AI_Notary.src.ui.pages import (
        render_notary_dashboard_page,
        render_create_session_page,
        render_manage_sessions_page,
        render_audit_logs_page,
        render_state_rules_page
    )
    
    return {
        'Notary Dashboard': render_notary_dashboard_page,
        'Create Session': render_create_session_page,
        'Manage Sessions': render_manage_sessions_page,
        'Audit Logs': render_audit_logs_page,
        'State Rules': render_state_rules_page
    }


# Default export
__all__ = [
    'init_notary_system',
    'get_notary_navigation_options', 
    'get_notary_pages',
    'NotaryDataAccess'
]
