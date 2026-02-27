import streamlit as st
import pandas as pd
from App.src.agent_pearl.agent_pearl import AgentPearl
from App.src.ui.streamlit_cache_utils import get_all_table_names_cached

def render_query_builder_page(agent: AgentPearl, sql_dir: str):
    st.title("SQL Query Builder")
    st.write("Build and execute SQL queries against the active database.")

    query_type = st.radio(
        "Select Query Type:",
        ("SELECT", "INSERT", "UPDATE", "DELETE"),
        key="query_type_radio"
    )

    st.markdown("--- ")

    tables = get_all_table_names_cached(db_path=agent.pearl_client.active_db, sql_dir=sql_dir)
    if not tables:
        st.warning("No tables found in the database.")
        return

    # Table selection
    table_options = [f"{i+1}. {table}" for i, table in enumerate(tables)]
    selected_table_option = st.selectbox(
        "Select a table:",
        table_options,
        key="table_selection"
    )

    if not selected_table_option:
        st.warning("Please select a table.")
        return
    
    selected_table = tables[table_options.index(selected_table_option)]

    if query_type == "SELECT":
        render_select_query_builder(agent, selected_table)
    elif query_type == "INSERT":
        render_insert_query_builder(agent, selected_table)
    elif query_type == "UPDATE":
        render_update_query_builder(agent, selected_table)
    elif query_type == "DELETE":
        render_delete_query_builder(agent, selected_table)

def render_select_query_builder(agent: AgentPearl, table_name: str):
    st.subheader(f"Build SELECT Query for {table_name}")
    columns = agent.pearl_client.get_table_columns(table_name)
    
    if not columns:
        st.warning(f"No columns found for table '{table_name}'.")
        return

    all_columns_option = ["* (All Columns)"] + columns
    column_options = [f"{i+1}. {col}" for i, col in enumerate(all_columns_option)]
    selected_column_options = st.multiselect(
        "Select columns to display:",
        column_options,
        default=[column_options[0]], # Default to "* (All Columns)"
        key=f"select_columns_{table_name}"
    )

    if column_options[0] in selected_column_options:
        columns_to_select = "*"
    else:
        selected_columns = [all_columns_option[column_options.index(opt)] for opt in selected_column_options]
        columns_to_select = ", ".join(selected_columns)

    st.markdown("--- ")
    st.subheader("Build WHERE Clause (Optional)")

    where_clause_parts = []
    
    # Get column types to determine if a column is numeric
    column_info = agent.pearl_client.get_table_column_info(table_name) # Assuming this method exists or will be added
    column_types = {info[1]: info[2] for info in column_info} # {column_name: type}

    # Manage WHERE conditions dynamically
    if f"num_where_conditions_{table_name}" not in st.session_state:
        st.session_state[f"num_where_conditions_{table_name}"] = 1 # Start with one condition by default

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Condition", key=f"add_condition_btn_{table_name}"):
            st.session_state[f"num_where_conditions_{table_name}"] += 1
    with col2:
        if st.session_state[f"num_where_conditions_{table_name}"] > 0:
            if st.button("Remove Last Condition", key=f"remove_condition_btn_{table_name}"):
                st.session_state[f"num_where_conditions_{table_name}"] -= 1

    num_conditions = st.session_state[f"num_where_conditions_{table_name}"]

    for i in range(num_conditions):
        st.markdown(f"**Condition {i+1}**")
        col_to_filter_options = [f"{j+1}. {col}" for j, col in enumerate(columns)]
        selected_col_to_filter_option = st.selectbox(
            f"Select column to filter by for condition {i+1}:",
            col_to_filter_options,
            key=f"filter_column_{table_name}_{i}"
        )
        
        if selected_col_to_filter_option:
                selected_filter_column = columns[col_to_filter_options.index(selected_col_to_filter_option)]
                column_type = column_types.get(selected_filter_column, "TEXT") # Default to TEXT

                MAX_DISTINCT_VALUES_FOR_SELECTBOX = 50
                distinct_values = agent.pearl_client.get_distinct_column_values(table_name, selected_filter_column)

                if len(distinct_values) <= MAX_DISTINCT_VALUES_FOR_SELECTBOX and len(distinct_values) > 0:
                    # Use selectbox for a manageable number of distinct values
                    key_selectbox_input = f"filter_value_selectbox_{table_name}_{i}"
                    filter_value = st.selectbox(
                        f"Value for {selected_filter_column} (Condition {i+1}):",
                        options=distinct_values,
                        key=key_selectbox_input
                    )
                    if filter_value is not None:
                        if column_type in ["REAL", "INTEGER"]:
                            where_clause_parts.append(f"{selected_filter_column} = {filter_value}")
                        else:
                            escaped_filter_value = str(filter_value).replace("'", "''")
                            where_clause_parts.append(f"{selected_filter_column} = '{escaped_filter_value}'")
                else:
                    # Fallback to text/number input for many distinct values or no values
                    if column_type in ["REAL", "INTEGER"]:
                        key_num_input = f"filter_value_{table_name}_{i}"
                        current_num_value = st.session_state.get(key_num_input, 0.0)

                        num_value = st.number_input(
                            f"Value for {selected_filter_column} (Condition {i+1}):",
                            value=current_num_value,
                            key=key_num_input,
                            min_value=None
                        )
                        if num_value is not None:
                            key_tolerance_input = f"tolerance_{table_name}_{i}"
                            current_tolerance_value = st.session_state.get(key_tolerance_input, 0.0001)

                            tolerance = st.number_input(
                                f"Tolerance for {selected_filter_column} (e.g., 0.0001 for floats):",
                                min_value=0.0,
                                value=current_tolerance_value,
                                step=0.00001,
                                key=key_tolerance_input
                            )
                            where_clause_parts.append(f"{selected_filter_column} BETWEEN {num_value - tolerance} AND {num_value + tolerance}")
                    else:
                        key_text_input = f"filter_value_{table_name}_{i}"
                        current_text_value = st.session_state.get(key_text_input, "")

                        filter_value = st.text_input(
                            f"Value for {selected_filter_column} (Condition {i+1}):",
                            value=current_text_value,
                            key=key_text_input
                        )

                        if filter_value:
                            escaped_filter_value = filter_value.replace("'", "''")
                            where_clause_parts.append(f"{selected_filter_column} = '{escaped_filter_value}'")

    final_where_clause = " AND ".join(where_clause_parts)

    query = f"SELECT {columns_to_select} FROM {table_name}"
    if final_where_clause:
        query += f" WHERE {final_where_clause}"
    query += ";"

    st.code(query, language="sql")

    if st.button("Execute SELECT Query", key=f"execute_select_{table_name}"):
        try:
            result, column_names = agent.run_query(query)
            if result:
                df = pd.DataFrame(result, columns=column_names)
                st.dataframe(df)
            else:
                st.info("No results found.")
        except Exception as e:
            st.error(f"Error executing query: {e}")

def render_insert_query_builder(agent: AgentPearl, table_name: str):
    st.subheader(f"Build INSERT Query for {table_name}")
    columns = agent.pearl_client.get_table_columns(table_name)

    if not columns:
        st.warning(f"No columns found for table '{table_name}'.")
        return

    st.write("Select columns to insert into and enter values:")
    
    column_options = [f"{i+1}. {col}" for i, col in enumerate(columns)]
    selected_insert_column_options = st.multiselect(
        "Select columns for insertion:",
        column_options,
        key=f"insert_columns_selection_{table_name}"
    )

    if not selected_insert_column_options:
        st.warning("Please select at least one column for insertion.")
        return

    insert_columns = [columns[column_options.index(opt)] for opt in selected_insert_column_options]
    
    values = {}
    
    # Special handling for 'transactions' table to enforce pearl_id
    if table_name == "transactions":
        if "pearl_id" not in insert_columns:
            insert_columns.insert(0, "pearl_id") # Ensure pearl_id is the first column
        
        active_pearl_id = st.session_state.get("pearl_id")
        if not active_pearl_id:
            st.warning("Cannot insert into 'transactions' table: No active PEARL ID selected. Please select or generate a PEARL ID first.")
            return

    for col in insert_columns:
        if table_name == "transactions" and col == "pearl_id":
            values[col] = st.text_input(f"Value for {col}", value=active_pearl_id, key=f"insert_value_{table_name}_{col}", disabled=True)
        else:
            values[col] = st.text_input(f"Value for {col}", key=f"insert_value_{table_name}_{col}")

    insert_values_for_query = []
    for col in insert_columns:
        val = values.get(col)
        if val:
            # Basic sanitization: quote strings, leave numbers as is
            if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
                processed_value = val
            elif val.replace('.', '', 1).isdigit():
                processed_value = val
            else:
                processed_value = f"'{val}'"
            insert_values_for_query.append(processed_value)
        else:
            insert_values_for_query.append("NULL")

    if not insert_columns:
        st.warning("Please provide values for at least one column.")
        return

    columns_str = ", ".join(insert_columns)
    values_str = ", ".join(insert_values_for_query)

    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});"
    st.code(query, language="sql")

    if st.button("Execute INSERT Query", key=f"execute_insert_{table_name}"):
        try:
            agent.run_query(query)
            st.success("Query executed successfully.")
        except Exception as e:
            st.error(f"Error executing query: {e}")

def render_update_query_builder(agent: AgentPearl, table_name: str):
    st.subheader(f"Build UPDATE Query for {table_name}")
    columns = agent.pearl_client.get_table_columns(table_name)

    if not columns:
        st.warning(f"No columns found for table '{table_name}'.")
        return

    st.write("Select columns to update and enter new values:")
    
    column_options = [f"{i+1}. {col}" for i, col in enumerate(columns)]
    selected_update_column_options = st.multiselect(
        "Select columns to update:",
        column_options,
        key=f"update_columns_selection_{table_name}"
    )

    if not selected_update_column_options:
        st.warning("Please select at least one column to update.")
        return

    update_columns = [columns[column_options.index(opt)] for opt in selected_update_column_options]

    set_clauses = []
    for col in update_columns:
        new_value = st.text_input(f"New value for {col}", key=f"update_value_{table_name}_{col}")
        if new_value:
            # Basic sanitization: quote strings, leave numbers as is
            if (new_value.startswith("'") and new_value.endswith("'")) or (new_value.startswith('"') and new_value.endswith('"')):
                processed_value = new_value
            elif new_value.replace('.', '', 1).isdigit():
                processed_value = new_value
            else:
                processed_value = f"'{new_value}'"
            set_clauses.append(f"{col} = {processed_value}")

    if not set_clauses:
        st.warning("Please provide new values for at least one column.")
        return

    set_clause_str = ", ".join(set_clauses)

    where_clause = st.text_input(
        "WHERE clause (e.g., id = 'abc', status = 'active'):",
        key=f"update_where_{table_name}"
    )

    query = f"UPDATE {table_name} SET {set_clause_str}"
    if where_clause:
        query += f" WHERE {where_clause}"
    query += ";"

    st.code(query, language="sql")

    if st.button("Execute UPDATE Query", key=f"execute_update_{table_name}"):
        try:
            agent.run_query(query)
            st.success("Query executed successfully.")
        except Exception as e:
            st.error(f"Error executing query: {e}")

def render_delete_query_builder(agent: AgentPearl, table_name: str):
    st.subheader(f"Build DELETE Query for {table_name}")
    columns = agent.pearl_client.get_table_columns(table_name)

    if not columns:
        st.warning(f"No columns found for table '{table_name}'.")
        return

    st.write("Build WHERE clause (optional):")
    
    column_options = [f"{i+1}. {col}" for i, col in enumerate(columns)]
    selected_where_column_option = st.selectbox(
        "Select a column for the WHERE clause (optional):",
        ["None"] + column_options,
        key=f"delete_where_column_{table_name}"
    )

    where_clause = ""
    if selected_where_column_option != "None":
        selected_column = columns[column_options.index(selected_where_column_option)]
        where_value = st.text_input(f"Value for {selected_column}", key=f"delete_where_value_{table_name}_{selected_column}")
        if where_value:
            # Basic sanitization: quote strings, leave numbers as is
            if (where_value.startswith("'") and where_value.endswith("'")) or (where_value.startswith('"') and where_value.endswith('"')):
                processed_value = where_value
            elif where_value.replace('.', '', 1).isdigit():
                processed_value = where_value
            else:
                processed_value = f"'{where_value}'"
            where_clause = f"{selected_column} = {processed_value}"

    query = f"DELETE FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"
    query += ";"

    st.code(query, language="sql")

    if st.button("Execute DELETE Query", key=f"execute_delete_{table_name}"):
        if not where_clause:
            st.warning("WARNING: No WHERE clause specified. This will delete ALL rows from the table.")
            confirm_all = st.checkbox("Confirm deletion of ALL rows", key=f"confirm_delete_all_{table_name}")
            if not confirm_all:
                st.info("Deletion cancelled.")
                return

        try:
            agent.run_query(query)
            st.success("Query executed successfully.")
        except Exception as e:
            st.error(f"Error executing query: {e}")
