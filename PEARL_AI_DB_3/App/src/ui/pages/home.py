import streamlit as st
from App.src.core.database.data_access import DataAccess

def render_home_page(dal: DataAccess):
    """
    Renders the home page of the application.

    Args:
        dal (DataAccess): The DataAccess object for database operations.
    """
    st.title("Welcome to PEARL AI Database Interface!")
    st.write("Your Personal Enterprise AI Resource Library Database.")
    st.markdown("""
    This application helps you manage various aspects of your business, including:

    - **Vault Management**: Securely store and manage your credentials.
    - **Job Cost Tracking**: Track costs and tasks associated with your jobs.
    - **CSV Import**: Import data from CSV files.
    - **Contact Management**: Manage your contacts (clients, subcontractors, suppliers).
    - **Accounting**: Keep track of your financial entries.
    - **Reports**: Generate various business reports.
    - **Query Builder**: Build and execute custom database queries.
    - **Election Management**: Create and manage public elections and voting.
    - **Cast Vote**: Participate in active elections.
    - **View Results**: View election results with charts and analytics.
    - **Verify Vote**: Verify your vote using receipt codes.

    Use the sidebar navigation to explore different features.
    """)

    # Display some basic stats or a welcome message based on PEARL ID
    if 'pearl_id' in st.session_state and st.session_state.pearl_id:
        st.subheader(f"Currently logged in with PEARL ID: {st.session_state.pearl_id}")
        st.write("You can now access all features related to your PEARL ID.")
    else:
        st.info("Please unlock your vault or create a new PEARL ID to get started.")