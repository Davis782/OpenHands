"""
Public Voting 2026 - Integration Module
========================================

This module provides integration utilities to add the Public Voting 2026
feature to the PEARL AI DB application.

USAGE:
------
In your main_app.py, add the following:

    # Import the voting integration
    from Public_Voting_2026.integration import get_voting_navigation_options, init_voting_system
    
    # Initialize voting system (call this before creating the DataAccess)
    voting_dal = init_voting_system(db_path)
    
    # Add voting to navigation options (modify your page_selection)
    voting_pages = get_voting_navigation_options()
    # Then add "Public Voting" to your navigation list

"""

import os
from pathlib import Path
from typing import List, Dict, Any
from Public_Voting_2026.src.core import VotingDataAccess


# SQL schema files to execute on initialization
SCHEMA_FILES = [
    '01_elections.sql',
    '02_voters.sql', 
    '03_votes.sql',
    '04_results.sql'
]


def get_voting_navigation_options() -> List[str]:
    """
    Returns the list of navigation page names for the voting system.
    
    Returns:
        List of page names: ['Public Voting']
    """
    return ['Public Voting']


def init_voting_system(db_path: str, sql_dir: str = None) -> VotingDataAccess:
    """
    Initialize the voting system database schema.
    
    Args:
        db_path: Path to the SQLite database
        sql_dir: Path to the SQL schema files (defaults to module's sql folder)
    
    Returns:
        VotingDataAccess instance for database operations
    """
    # Determine the SQL directory
    if sql_dir is None:
        # Get the directory of this integration module
        module_dir = Path(__file__).parent.parent
        sql_dir = str(module_dir / 'sql')
    
    # Create database schema if needed
    _ensure_voting_schema(db_path, sql_dir)
    
    # Return the data access layer
    return VotingDataAccess(db_path)


def _ensure_voting_schema(db_path: str, sql_dir: str):
    """
    Ensure the voting system tables exist by executing schema files.
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Execute each schema file
        for schema_file in SCHEMA_FILES:
            schema_path = os.path.join(sql_dir, schema_file)
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                    # Split by semicolons to handle multiple statements
                    for statement in schema_sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            cursor.execute(statement)
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_voting_pages() -> Dict[str, Any]:
    """
    Returns a dictionary mapping page names to render functions.
    
    This is useful for dynamic page rendering based on selection.
    
    Returns:
        Dictionary with page names as keys and (function, dal) tuples as values
    """
    from Public_Voting_2026.src.ui.pages import (
        render_election_management_page,
        render_voting_page,
        render_results_page,
        render_verify_page
    )
    
    return {
        'Election Management': render_election_management_page,
        'Cast Vote': render_voting_page,
        'View Results': render_results_page,
        'Verify Vote': render_verify_page
    }


# Default export
__all__ = [
    'init_voting_system',
    'get_voting_navigation_options', 
    'get_voting_pages',
    'VotingDataAccess'
]
