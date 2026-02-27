import streamlit as st

def render_common_page(dal):
    """
    Renders the Common Utilities page, displaying general system information
    and the currently active PEARL ID.
    """ 
    st.title("Common Utilities")
    st.write("This module provides general application utilities and information.")

    st.subheader("Current PEARL ID")
    if 'pearl_id' in st.session_state:
        st.info(f"Active PEARL ID: {st.session_state.pearl_id}")
    else:
        st.warning("No PEARL ID set in session state.")

    st.subheader("Database Server Information")
    try:
        sql_query = dal._load_sql_query("common/get_server_info.sql")
        result = dal._fetch_raw_sql(sql_query)
        if result:
            st.json(dict(result[0])) # Display the first (and likely only) row as JSON
        else:
            st.info("Could not retrieve server information.")
    except Exception as e:
        st.error(f"Error fetching server information: {e}")
