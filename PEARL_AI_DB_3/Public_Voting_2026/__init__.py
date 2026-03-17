"""
Public Voting 2026
==================

A secure anonymous public voting system module for PEARL AI DB.

This module implements a voting system based on the PRD_Voting_Pearl_ID.md
specification, providing:
- Election management
- Voter registration and eligibility
- Anonymous vote casting
- Vote verification
- Results calculation and display
- Audit logging

Quick Start:
-----------
from Public_Voting_2026 import init_voting_system, get_voting_pages

# Initialize the voting system
voting_dal = init_voting_system("path/to/your/database.db")

# Get available voting pages
pages = get_voting_pages()

# Render a page
pages['Cast Vote'](voting_dal)
"""

from .src.core import VotingDataAccess
from .integration import (
    init_voting_system,
    get_voting_navigation_options,
    get_voting_pages
)

__version__ = "1.0.0"

__all__ = [
    'VotingDataAccess',
    'init_voting_system', 
    'get_voting_navigation_options',
    'get_voting_pages'
]
