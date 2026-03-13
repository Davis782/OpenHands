import streamlit as st
import pandas as pd
from App.src.agent_pearl.agent_pearl import AgentPearl
from App.src.ui.streamlit_cache_utils import get_all_table_names_cached

def render_query_builder_page(agent: AgentPearl, sql_dir: str):
    st.title("SQL Query Builder")
    st.write("Build and execute SQL queries against the active database.")

    query_type = st.radio(
        "Select Query Type:",
        ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE TABLE", "ALTER TABLE", "DROP TABLE", "CREATE INDEX", "DROP INDEX", "CREATE VIEW", "BEGIN TRANSACTION", "COMMIT", "ROLLBACK", "SAVEPOINT", "ANALYZE", "VACUUM", "PRAGMA", "ADVANCED QUERIES"),
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
    elif query_type == "CREATE TABLE":
        render_create_table_query_builder(agent)
    elif query_type == "ALTER TABLE":
        render_alter_table_query_builder(agent, selected_table)
    elif query_type == "DROP TABLE":
        render_drop_table_query_builder(agent, selected_table)
    elif query_type == "CREATE INDEX":
        render_create_index_query_builder(agent, selected_table)
    elif query_type == "DROP INDEX":
        render_drop_index_query_builder(agent, selected_table)
    elif query_type == "CREATE VIEW":
            render_create_view_query_builder(agent, selected_table)
    elif query_type == "BEGIN TRANSACTION":
        render_begin_transaction_query_builder(agent)
    elif query_type == "COMMIT":
        render_commit_query_builder(agent)
    elif query_type == "ROLLBACK":
        render_rollback_query_builder(agent)
    elif query_type == "SAVEPOINT":
        render_savepoint_query_builder(agent)
    elif query_type == "ANALYZE":
        render_analyze_query_builder(agent)
    elif query_type == "VACUUM":
        render_vacuum_query_builder(agent)
    elif query_type == "PRAGMA":
        render_pragma_query_builder(agent)
    elif query_type == "ADVANCED QUERIES":
        render_advanced_queries_builder(agent, selected_table)

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

    with st.expander("How to build WHERE clauses?"):
        st.markdown("**WHERE clauses filter rows based on conditions.**")
        st.markdown("**Examples:**")
        st.markdown("- `column = 'value'` (exact match for text)")
        st.markdown("- `column > 100` (greater than for numbers)")
        st.markdown("- `column LIKE '%text%'` (text contains 'text')")
        st.markdown("- `column IN ('value1', 'value2')` (column is one of the listed values)")
        st.markdown("- `column IS NULL` (column has no value)")
        st.markdown("**Operators:** `=`, `!=`, `>`, `<`, `>=`, `<=`, `LIKE`, `NOT LIKE`, `IN`, `NOT IN`, `IS NULL`, `IS NOT NULL`")

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

                # Determine default operator based on column type
                default_operator = "="
                if column_type == "TEXT":
                    default_operator = "LIKE"
                elif column_type in ["REAL", "INTEGER"]:
                    default_operator = "="
                # Add more sophisticated logic for DATE, BOOLEAN if needed

                operator = st.selectbox(
                    f"Operator for {selected_filter_column} (Condition {i+1}):",
                    options=["=", "!=", ">", "<", ">=", "<=", "LIKE", "NOT LIKE", "IN", "NOT IN", "IS NULL", "IS NOT NULL"],
                    index=["=", "!=", ">", "<", ">=", "<=", "LIKE", "NOT LIKE", "IN", "NOT IN", "IS NULL", "IS NOT NULL"].index(default_operator),
                    key=f"filter_operator_{table_name}_{i}"
                )

                MAX_DISTINCT_VALUES_FOR_SELECTBOX = 50
                distinct_values = agent.pearl_client.get_distinct_column_values(table_name, selected_filter_column)

                if operator in ["IS NULL", "IS NOT NULL"]:
                    where_clause_parts.append(f"{selected_filter_column} {operator}")
                elif len(distinct_values) <= MAX_DISTINCT_VALUES_FOR_SELECTBOX and len(distinct_values) > 0 and operator in ["=", "!=", "IN", "NOT IN"]:
                    # Use selectbox for a manageable number of distinct values
                    key_selectbox_input = f"filter_value_selectbox_{table_name}_{i}"
                    filter_value = st.selectbox(
                        f"Value for {selected_filter_column} (Condition {i+1}):",
                        options=distinct_values,
                        key=key_selectbox_input
                    )
                    if filter_value is not None:
                        if operator in ["IN", "NOT IN"]:
                            # For IN/NOT IN, allow multiple selections or a comma-separated string
                            # For simplicity, let's assume single selection for now, or user types comma-separated
                            escaped_filter_value = str(filter_value).replace("'", "''")
                            where_clause_parts.append(f"{selected_filter_column} {operator} ('{escaped_filter_value}')")
                        elif column_type in ["REAL", "INTEGER"]:
                            where_clause_parts.append(f"{selected_filter_column} {operator} {filter_value}")
                        else:
                            escaped_filter_value = str(filter_value).replace("'", "''")
                            where_clause_parts.append(f"{selected_filter_column} {operator} '{escaped_filter_value}'")
                else:
                    # Fallback to text/number input for many distinct values or no values
                    # Determine default value based on type and operator
                    default_value_input = ""
                    if operator == "LIKE":
                        default_value_input = "%%"
                    elif column_type in ["REAL", "INTEGER"]:
                        default_value_input = 0

                    if column_type in ["REAL", "INTEGER"] and operator not in ["LIKE", "NOT LIKE"]:
                        key_num_input = f"filter_value_{table_name}_{i}"
                        current_num_value = st.session_state.get(key_num_input, default_value_input)

                        num_value = st.number_input(
                            f"Value for {selected_filter_column} (Condition {i+1}):",
                            value=current_num_value,
                            key=key_num_input,
                            min_value=None
                        )
                        if num_value is not None:
                            if operator in [">", "<", ">=", "<="]:
                                where_clause_parts.append(f"{selected_filter_column} {operator} {num_value}")
                            else: # Assume = or != for direct comparison
                                where_clause_parts.append(f"{selected_filter_column} {operator} {num_value}")

                            # Removed tolerance for simplicity with direct operators, can be re-added for BETWEEN
                            # if operator == "BETWEEN":
                            #     key_tolerance_input = f"tolerance_{table_name}_{i}"
                            #     current_tolerance_value = st.session_state.get(key_tolerance_input, 0.0001)
                            #     tolerance = st.number_input(
                            #         f"Tolerance for {selected_filter_column} (e.g., 0.0001 for floats):",
                            #         min_value=0.0,
                            #         value=current_tolerance_value,
                            #         step=0.00001,
                            #         key=key_tolerance_input
                            #     )
                            #     where_clause_parts.append(f"{selected_filter_column} BETWEEN {num_value - tolerance} AND {num_value + tolerance}")

                    else: # TEXT or other types, or LIKE/NOT LIKE operator
                        key_text_input = f"filter_value_{table_name}_{i}"
                        current_text_value = st.session_state.get(key_text_input, default_value_input)

                        filter_value = st.text_input(
                            f"Value for {selected_filter_column} (Condition {i+1}):",
                            value=current_text_value,
                            key=key_text_input
                        )

                        if filter_value:
                            escaped_filter_value = filter_value.replace("'", "''")
                            if operator in ["LIKE", "NOT LIKE"]:
                                where_clause_parts.append(f"{selected_filter_column} {operator} '{escaped_filter_value}'")
                            else:
                                where_clause_parts.append(f"{selected_filter_column} {operator} '{escaped_filter_value}'")

    final_where_clause = " AND ".join(where_clause_parts)

    # JOIN Clause
    st.markdown("--- ")
    st.subheader("Build JOIN Clause (Optional)")

    with st.expander("How to build JOIN clauses?"):
        st.markdown("**JOIN clauses combine rows from two or more tables based on a related column.**")
        st.markdown("**Join Types:**")
        st.markdown("- **INNER JOIN:** Returns rows when there is a match in both tables.")
        st.markdown("- **LEFT JOIN:** Returns all rows from the left table, and the matched rows from the right table.")
        st.markdown("- **RIGHT JOIN:** Returns all rows from the right table, and the matched rows from the left table.")
        st.markdown("- **FULL OUTER JOIN:** Returns all rows when there is a match in one of the tables.")
        st.markdown("**ON Condition Example:** `Table1.column_name = Table2.column_name`")

    if f"num_joins_{table_name}" not in st.session_state:
        st.session_state[f"num_joins_{table_name}"] = 0

    col_j1, col_j2 = st.columns(2)
    with col_j1:
        if st.button("Add JOIN", key=f"add_join_btn_{table_name}"):
            st.session_state[f"num_joins_{table_name}"] += 1
    with col_j2:
        if st.session_state[f"num_joins_{table_name}"] > 0:
            if st.button("Remove Last JOIN", key=f"remove_join_btn_{table_name}"):
                st.session_state[f"num_joins_{table_name}"] -= 1

    join_clauses = []
    all_tables = agent.pearl_client.get_all_table_names()
    all_tables.remove(table_name) # Don't allow joining a table to itself

    # Get primary key of the main table for suggested ON condition
    main_table_pk = "id" # Default guess
    main_table_column_info = agent.pearl_client.get_table_column_info(table_name)
    for col_info in main_table_column_info:
        if col_info[5]: # pk column is index 5
            main_table_pk = col_info[1] # column name is index 1
            break

    for i in range(st.session_state[f"num_joins_{table_name}"]):
        st.markdown(f"**JOIN {i+1}**")
        join_type = st.selectbox(
            f"Join Type {i+1}:",
            ("INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN"),
            key=f"join_type_{table_name}_{i}"
        )
        joined_table = st.selectbox(
            f"Table to Join {i+1}:",
            all_tables,
            key=f"joined_table_{table_name}_{i}"
        )

        # Suggest a default ON condition
        default_on_condition = f"{table_name}.{main_table_pk} = {joined_table}.{table_name}_{main_table_pk}"

        on_condition = st.text_input(
            f"ON Condition {i+1} (e.g., {table_name}.{main_table_pk} = {joined_table}.{table_name}_{main_table_pk}):",
            value=default_on_condition, # Pre-populate with suggested value
            key=f"on_condition_{table_name}_{i}"
        )
        if joined_table and on_condition:
            join_clauses.append(f"{join_type} {joined_table} ON {on_condition}")

    # ORDER BY Clause
    st.markdown("--- ")
    st.subheader("Build ORDER BY Clause (Optional)")

    with st.expander("How to build ORDER BY clauses?"):
        st.markdown("**ORDER BY sorts the result set by one or more columns.**")
        st.markdown("**Direction:** `ASC` (ascending, default) or `DESC` (descending).")
        st.markdown("**Example:** `ORDER BY name ASC, age DESC`")

    order_by_columns = st.multiselect(
        "Select columns to order by:",
        columns,
        key=f"order_by_columns_{table_name}"
    )
    order_by_direction = st.radio(
        "Order Direction:",
        ("ASC", "DESC"),
        key=f"order_by_direction_{table_name}",
        horizontal=True
    )

    order_by_clause = ""
    if order_by_columns:
        order_by_clause = f"ORDER BY {', '.join(order_by_columns)} {order_by_direction}"

    # LIMIT Clause
    st.markdown("--- ")
    st.subheader("Build LIMIT Clause (Optional)")

    with st.expander("How to build LIMIT clauses?"):
        st.markdown("**LIMIT restricts the number of rows returned by a query.**")
        st.markdown("**Example:** `LIMIT 10` (returns only the first 10 rows)")

    limit_value = st.number_input(
        "Limit results to (0 for no limit):",
        min_value=0,
        value=0,
        step=1,
        key=f"limit_value_{table_name}"
    )

    limit_clause = ""
    if limit_value > 0:
        limit_clause = f"LIMIT {limit_value}"

    # GROUP BY Clause
    st.markdown("--- ")
    st.subheader("Build GROUP BY Clause (Optional)")

    with st.expander("How to build GROUP BY clauses?"):
        st.markdown("**GROUP BY groups rows that have the same values into summary rows.**")
        st.markdown("It is often used with aggregate functions (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`).")
        st.markdown("**Example:** `GROUP BY category_id` (to count products per category)")

    group_by_columns = st.multiselect(
        "Select columns to group by:",
        columns,
        key=f"group_by_columns_{table_name}"
    )

    group_by_clause = ""
    if group_by_columns:
        group_by_clause = f"GROUP BY {', '.join(group_by_columns)}"

    # HAVING Clause
    st.markdown("--- ")
    st.subheader("Build HAVING Clause (Optional)")

    with st.expander("How to build HAVING clauses?"):
        st.markdown("**HAVING clauses filter groups based on conditions, after aggregation.**")
        st.markdown("It is used with `GROUP BY` and aggregate functions.")
        st.markdown("**Examples:**")
        st.markdown("- `COUNT(order_id) > 5` (groups with more than 5 orders)")
        st.markdown("- `AVG(price) < 50` (groups where average price is less than 50)")

    having_clause = st.text_input(
        "HAVING condition (e.g., COUNT(id) > 1):",
        key=f"having_clause_{table_name}"
    )

    query = f"SELECT {columns_to_select} FROM {table_name}"
    if join_clauses:
        query += f" {' '.join(join_clauses)}"
    if final_where_clause:
        query += f" WHERE {final_where_clause}"
    if group_by_clause:
        query += f" {group_by_clause}"
    if having_clause:
        query += f" HAVING {having_clause}"
    if order_by_clause:
        query += f" {order_by_clause}"
    if limit_clause:
        query += f" {limit_clause}"
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

    insert_type = st.radio(
        "Select Insert Type:",
        ("INSERT INTO", "INSERT OR IGNORE INTO", "REPLACE INTO", "UPSERT (ON CONFLICT)"),
        key=f"insert_type_{table_name}",
        horizontal=True
    )

    if insert_type == "UPSERT (ON CONFLICT)":
        st.markdown("--- ")
        st.subheader("UPSERT (ON CONFLICT) Configuration")

        with st.expander("How to use UPSERT (ON CONFLICT)?"):
            st.markdown("**UPSERT allows you to INSERT a row, or UPDATE it if it already exists.**")
            st.markdown("You specify a column (or columns) to check for conflicts (e.g., a PRIMARY KEY or UNIQUE column).")
            st.markdown("**Actions on Conflict:**")
            st.markdown("- **DO UPDATE SET:** If a conflict occurs, update the existing row with new values.")
            st.markdown("- **DO NOTHING:** If a conflict occurs, do nothing (the existing row remains unchanged).")
            st.markdown("**Example:** `INSERT INTO users (id, name) VALUES (1, 'Alice') ON CONFLICT(id) DO UPDATE SET name = EXCLUDED.name;`")

        upsert_conflict_column = st.selectbox(
            "Column(s) to check for conflict (e.g., PRIMARY KEY column):",
            columns,
            key=f"upsert_conflict_column_{table_name}"
        )
        upsert_action = st.radio(
            "Action on Conflict:",
            ("DO UPDATE SET", "DO NOTHING"),
            key=f"upsert_action_{table_name}",
            horizontal=True
        )

        if upsert_action == "DO UPDATE SET":
            st.info("Select columns to update on conflict. Values will be taken from the new record.")
            update_on_conflict_columns = st.multiselect(
                "Columns to UPDATE on conflict:",
                columns,
                key=f"update_on_conflict_columns_{table_name}"
            )
        else:
            update_on_conflict_columns = [] # No columns to update if DO NOTHING
    else:
        upsert_conflict_column = None
        upsert_action = None
        update_on_conflict_columns = []

    columns_info = agent.pearl_client.get_table_column_info(table_name)
    columns = [info[1] for info in columns_info]

    # Identify non-auto-incrementing columns for default selection
    non_auto_increment_columns = []
    for col_info in columns_info:
        col_name = col_info[1]
        col_type = col_info[2]
        is_pk = col_info[5]

        # Heuristic for auto-increment: INTEGER PRIMARY KEY
        # SQLite's AUTOINCREMENT is a keyword, but table_info only shows PK.
        # Assuming INTEGER PRIMARY KEY often implies auto-increment for default exclusion.
        if not (is_pk and col_type.upper() == "INTEGER"):
            non_auto_increment_columns.append(col_name)

    if not columns:
        st.warning(f"No columns found for table '{table_name}'.")
        return

    st.write("Select columns to insert into and enter values:")

    column_options = [f"{i+1}. {col}" for i, col in enumerate(columns)]

    # Pre-select non-auto-incrementing columns by default
    default_selected_options = [f"{i+1}. {col}" for i, col in enumerate(columns) if col in non_auto_increment_columns]

    selected_insert_column_options = st.multiselect(
        "Select columns for insertion:",
        column_options,
        default=default_selected_options, # Pre-select columns
        key=f"insert_columns_selection_{table_name}"
    )

    if not selected_insert_column_options:
        st.warning("Please select at least one column for insertion.")
        return

    insert_columns = [columns[column_options.index(opt)] for opt in selected_insert_column_options]

    values = {}

    # Map column names to their full info for default value suggestions
    column_name_to_info = {info[1]: info for info in columns_info}

    # Special handling for 'transactions' table to enforce pearl_id
    if table_name == "transactions":
        if "pearl_id" not in insert_columns:
            insert_columns.insert(0, "pearl_id") # Ensure pearl_id is the first column

        active_pearl_id = st.session_state.get("pearl_id")
        if not active_pearl_id:
            st.warning("Cannot insert into 'transactions' table: No active PEARL ID selected. Please select or generate a PEARL ID first.")
            return

    for col in insert_columns:
        col_info = column_name_to_info.get(col)
        col_type = col_info[2].upper() if col_info else "TEXT"
        is_not_null = col_info[3] # 1 if NOT NULL, 0 otherwise
        default_value_from_schema = col_info[4] # Default value from schema, can be None or a string

        # Determine suggested default value for input field
        suggested_value = ""
        if col == "pearl_id" and table_name == "transactions":
            suggested_value = active_pearl_id
        elif default_value_from_schema is not None:
            # Use schema default if available
            suggested_value = str(default_value_from_schema)
        elif not is_not_null: # If nullable, suggest NULL
            suggested_value = "NULL"
        elif col_type == "INTEGER":
            suggested_value = "0"
        elif col_type == "REAL":
            suggested_value = "0.0"
        elif col_type == "TEXT":
            suggested_value = "''" # Empty string for text
        # For BLOB, no easy default

        if table_name == "transactions" and col == "pearl_id":
            values[col] = st.text_input(f"Value for {col}", value=suggested_value, key=f"insert_value_{table_name}_{col}", disabled=True)
        else:
            values[col] = st.text_input(f"Value for {col}", value=suggested_value, key=f"insert_value_{table_name}_{col}")

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

    if insert_type == "UPSERT (ON CONFLICT)" and upsert_conflict_column:
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str}) ON CONFLICT({upsert_conflict_column}) "
        if upsert_action == "DO UPDATE SET" and update_on_conflict_columns:
            set_clauses = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_on_conflict_columns])
            query += f"DO UPDATE SET {set_clauses};"
        elif upsert_action == "DO NOTHING":
            query += "DO NOTHING;"
        else:
            st.warning("UPSERT selected, but conflict action or columns to update are missing.")
            return
    else:
        query = f"{insert_type} {table_name} ({columns_str}) VALUES ({values_str});"
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

    # Get primary key for suggested WHERE clause
    main_table_pk = "id" # Default guess
    main_table_column_info = agent.pearl_client.get_table_column_info(table_name)
    for col_info in main_table_column_info:
        if col_info[5]: # pk column is index 5
            main_table_pk = col_info[1] # column name is index 1
            break

    default_where_clause = f"{main_table_pk} = 'value'" # Suggest PK for filtering

    where_clause = st.text_input(
        f"WHERE clause (e.g., {main_table_pk} = 'value', status = 'active'):",
        value=default_where_clause,
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

    # Get primary key for suggested WHERE clause
    main_table_pk = "id" # Default guess
    main_table_column_info = agent.pearl_client.get_table_column_info(table_name)
    for col_info in main_table_column_info:
        if col_info[5]: # pk column is index 5
            main_table_pk = col_info[1] # column name is index 1
            break

    default_where_clause = f"{main_table_pk} = 'value'" # Suggest PK for filtering

    where_clause = st.text_input(
        f"WHERE clause (e.g., {main_table_pk} = 'value'):",
        value=default_where_clause,
        key=f"delete_where_{table_name}"
    )

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

def render_create_table_query_builder(agent: AgentPearl):
    st.subheader("Build CREATE TABLE Query")

    table_name = st.text_input("Table Name:", key="create_table_name")

    st.markdown("--- ")
    st.write("Define Columns:")

    if "num_columns" not in st.session_state:
        st.session_state.num_columns = 1

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Column", key="add_column_btn"):
            st.session_state.num_columns += 1
    with col2:
        if st.session_state.num_columns > 1:
            if st.button("Remove Last Column", key="remove_column_btn"):
                st.session_state.num_columns -= 1

    column_definitions = []
    for i in range(st.session_state.num_columns):
        st.markdown(f"**Column {i+1}**")

        default_col_name = "id" if i == 0 else ""
        default_col_type_index = 1 if i == 0 else 0 # INTEGER for first, TEXT for others
        default_is_primary_key = True if i == 0 else False
        default_is_not_null = True if i == 0 else False

        col_name = st.text_input(f"Column Name {i+1}:", value=default_col_name, key=f"col_name_{i}")
        col_type = st.selectbox(
            f"Column Type {i+1}:",
            ("TEXT", "INTEGER", "REAL", "BLOB"),
            index=default_col_type_index,
            key=f"col_type_{i}"
        )
        is_primary_key = st.checkbox(f"Primary Key {i+1}", value=default_is_primary_key, key=f"col_pk_{i}")
        is_not_null = st.checkbox(f"NOT NULL {i+1}", value=default_is_not_null, key=f"col_nn_{i}")

        # Add AUTOINCREMENT if it's an INTEGER PRIMARY KEY
        autoincrement_str = " AUTOINCREMENT" if is_primary_key and col_type == "INTEGER" else ""

        if col_name:
            definition = f"{col_name} {col_type}"
            if is_not_null:
                definition += " NOT NULL"
            if is_primary_key:
                definition += " PRIMARY KEY"
            definition += autoincrement_str
            column_definitions.append(definition)

    if table_name and column_definitions:
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_definitions)});"
        st.code(query, language="sql")

        if st.button("Execute CREATE TABLE Query", key="execute_create_table"):
            try:
                agent.run_query(query)
                st.success(f"Table '{table_name}' created successfully.")
            except Exception as e:
                st.error(f"Error executing query: {e}")
    else:
        st.info("Please enter a table name and define at least one column.")

def render_alter_table_query_builder(agent: AgentPearl, table_name: str):
    st.subheader(f"Build ALTER TABLE Query for {table_name}")

    alter_type = st.radio(
        "Select ALTER TABLE operation:",
        ("ADD COLUMN", "DROP COLUMN", "RENAME COLUMN"),
        key=f"alter_type_{table_name}"
    )

    query = ""
    if alter_type == "ADD COLUMN":
        new_col_name = st.text_input("New Column Name:", key=f"add_col_name_{table_name}")
        new_col_type = st.selectbox(
            "New Column Type:",
            ("TEXT", "INTEGER", "REAL", "BLOB"),
            key=f"add_col_type_{table_name}"
        )
        is_not_null = st.checkbox("NOT NULL", key=f"add_col_nn_{table_name}")
        default_value_input = st.text_input("Default Value (optional):", key=f"add_col_default_{table_name}")

        col_definition = f"{new_col_name} {new_col_type}"
        if is_not_null:
            col_definition += " NOT NULL"
        if default_value_input:
            # Basic sanitization for default value
            if new_col_type in ["INTEGER", "REAL"] and default_value_input.replace('.', '', 1).isdigit():
                col_definition += f" DEFAULT {default_value_input}"
            else:
                escaped_default_value = default_value_input.replace("'", "''")
                col_definition += f" DEFAULT '{escaped_default_value}'"

        if new_col_name:
            query = f"ALTER TABLE {table_name} ADD COLUMN {col_definition};"
    elif alter_type == "DROP COLUMN":
        columns = agent.pearl_client.get_table_columns(table_name)
        if columns:
            col_to_drop = st.selectbox(
                "Column to Drop:",
                columns,
                key=f"drop_col_name_{table_name}"
            )
            if col_to_drop:
                query = f"ALTER TABLE {table_name} DROP COLUMN {col_to_drop};"
        else:
            st.warning(f"No columns found in table {table_name}.")
    elif alter_type == "RENAME COLUMN":
        columns = agent.pearl_client.get_table_columns(table_name)
        if columns:
            old_col_name = st.selectbox(
                "Old Column Name:",
                columns,
                key=f"old_col_name_{table_name}"
            )
            new_col_name = st.text_input("New Column Name:", key=f"rename_new_col_name_{table_name}")
            if old_col_name and new_col_name:
                query = f"ALTER TABLE {table_name} RENAME COLUMN {old_col_name} TO {new_col_name};"
        else:
            st.warning(f"No columns found in table {table_name}.")

    if query:
        st.code(query, language="sql")
        if st.button("Execute ALTER TABLE Query", key=f"execute_alter_table_{table_name}"):
            try:
                agent.run_query(query)
                st.success("Query executed successfully.")
            except Exception as e:
                st.error(f"Error executing query: {e}")
    else:
        st.info("Please select an operation and provide necessary details.")

def render_drop_table_query_builder(agent: AgentPearl, table_name: str):
    st.subheader(f"Build DROP TABLE Query for {table_name}")

    confirm_drop = st.checkbox(
        f"I understand that dropping table '{table_name}' is irreversible.",
        key=f"confirm_drop_table_{table_name}"
    )

    query = f"DROP TABLE IF EXISTS {table_name};"

    st.code(query, language="sql")

    if st.button("Execute DROP TABLE Query", key=f"execute_drop_table_{table_name}"):
        if confirm_drop:
            try:
                agent.run_query(query)
                st.success(f"Table '{table_name}' dropped successfully.")
            except Exception as e:
                st.error(f"Error executing query: {e}")
        else:
            st.warning("Please confirm to drop the table.")

def render_create_index_query_builder(agent: AgentPearl, table_name: str):
    st.subheader(f"Build CREATE INDEX Query for {table_name}")

    # Get primary key for default selection
    main_table_pk = "id" # Default guess
    main_table_column_info = agent.pearl_client.get_table_column_info(table_name)
    for col_info in main_table_column_info:
        if col_info[5]: # pk column is index 5
            main_table_pk = col_info[1] # column name is index 1
            break

    default_index_name = f"idx_{table_name}_{main_table_pk}"
    index_name = st.text_input("Index Name:", value=default_index_name, key=f"index_name_{table_name}")
    columns = agent.pearl_client.get_table_columns(table_name)

    if not columns:
        st.warning(f"No columns found for table '{table_name}'.")
        return

    default_selected_columns = [main_table_pk] if main_table_pk in columns else []

    selected_columns = st.multiselect(
        "Select columns for index:",
        columns,
        default=default_selected_columns, # Pre-select primary key
        key=f"index_columns_{table_name}"
    )

    is_unique = st.checkbox("Unique Index", key=f"unique_index_{table_name}")

    if index_name and selected_columns:
        unique_str = "UNIQUE " if is_unique else ""
        columns_str = ", ".join(selected_columns)
        query = f"CREATE {unique_str}INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str});"
        st.code(query, language="sql")

        if st.button("Execute CREATE INDEX Query", key=f"execute_create_index_{table_name}"):
            try:
                agent.run_query(query)
                st.success(f"Index '{index_name}' created successfully on table '{table_name}'.")
            except Exception as e:
                st.error(f"Error executing query: {e}")
    else:
        st.info("Please enter an index name and select at least one column.")

def render_drop_index_query_builder(agent: AgentPearl, table_name: str):
    st.subheader(f"Build DROP INDEX Query for {table_name}")

    # Get existing indexes for the table
    # SQLite doesn't have a direct way to list indexes for a specific table easily via PRAGMA index_list(table_name)
    # We'll fetch all indexes and filter by table name
    all_indexes_query = "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name = ?;"
    try:
        all_indexes_result, _ = agent.run_query(all_indexes_query, (table_name,))
        existing_indexes = [row[0] for row in all_indexes_result]
    except Exception as e:
        st.error(f"Error fetching existing indexes: {e}")
        existing_indexes = []

    if not existing_indexes:
        st.info(f"No indexes found for table '{table_name}'.")
        return

    index_to_drop = st.selectbox(
        "Select Index to Drop:",
        existing_indexes,
        key=f"drop_index_name_{table_name}"
    )

    if index_to_drop:
        confirm_drop = st.checkbox(
            f"I understand that dropping index '{index_to_drop}' is irreversible.",
            key=f"confirm_drop_index_{table_name}"
        )

        query = f"DROP INDEX IF EXISTS {index_to_drop};"

        st.code(query, language="sql")

        if st.button("Execute DROP INDEX Query", key=f"execute_drop_index_{table_name}"):
            if confirm_drop:
                try:
                    agent.run_query(query)
                    st.success(f"Index '{index_to_drop}' dropped successfully.")
                except Exception as e:
                    st.error(f"Error executing query: {e}")
            else:
                st.warning("Please confirm to drop the index.")
    else:
        st.info("No index selected to drop.")

def render_create_view_query_builder(agent: AgentPearl, table_name: str):
    st.subheader("Build CREATE VIEW Query")

    view_name = st.text_input("View Name:", key="create_view_name")
    select_query = st.text_area(
        "SELECT Query for View:",
        value=f"SELECT * FROM {table_name} WHERE condition;",
        height=150,
        key="create_view_select_query"
    )

    if view_name and select_query:
        query = f"CREATE VIEW IF NOT EXISTS {view_name} AS {select_query};"
        st.code(query, language="sql")

        if st.button("Execute CREATE VIEW Query", key="execute_create_view"):
            try:
                agent.run_query(query)
                st.success(f"View '{view_name}' created successfully.")
            except Exception as e:
                st.error(f"Error executing query: {e}")
    else:
        st.info("Please enter a view name and a SELECT query.")

def render_begin_transaction_query_builder(agent: AgentPearl):
    st.subheader("BEGIN TRANSACTION")
    query = "BEGIN TRANSACTION;"
    st.code(query, language="sql")
    if st.button("Execute BEGIN TRANSACTION", key="execute_begin_transaction"):
        try:
            agent.run_query(query) # TCL commands don't return results
            st.success("Transaction started.")
        except Exception as e:
            st.error(f"Error executing query: {e}")

def render_commit_query_builder(agent: AgentPearl):
    st.subheader("COMMIT TRANSACTION")
    query = "COMMIT;"
    st.code(query, language="sql")
    if st.button("Execute COMMIT", key="execute_commit"):
        try:
            agent.run_query(query) # TCL commands don't return results
            st.success("Transaction committed.")
        except Exception as e:
            st.error(f"Error executing query: {e}")

def render_rollback_query_builder(agent: AgentPearl):
    st.subheader("ROLLBACK TRANSACTION")
    query = "ROLLBACK;"
    st.code(query, language="sql")
    if st.button("Execute ROLLBACK", key="execute_rollback"):
        try:
            agent.run_query(query) # TCL commands don't return results
            st.success("Transaction rolled back.")
        except Exception as e:
            st.error(f"Error executing query: {e}")

def render_savepoint_query_builder(agent: AgentPearl):
    st.subheader("SAVEPOINT")
    savepoint_name = st.text_input("Savepoint Name:", key="savepoint_name")
    if savepoint_name:
        query = f"SAVEPOINT {savepoint_name};"
        st.code(query, language="sql")
        if st.button("Execute SAVEPOINT", key="execute_savepoint"):
            try:
                agent.run_query(query) # TCL commands don't return results
                st.success(f"Savepoint '{savepoint_name}' created.")
            except Exception as e:
                st.error(f"Error executing query: {e}")
    else:
        st.info("Please enter a savepoint name.")

def render_analyze_query_builder(agent: AgentPearl):
    st.subheader("ANALYZE Database")
    query = "ANALYZE;"
    st.code(query, language="sql")
    if st.button("Execute ANALYZE", key="execute_analyze"):
        try:
            agent.run_query(query) # DDL/Utility commands don't return results
            st.success("Database analyzed.")
        except Exception as e:
            st.error(f"Error executing query: {e}")

def render_vacuum_query_builder(agent: AgentPearl):
    st.subheader("VACUUM Database")
    query = "VACUUM;"
    st.code(query, language="sql")
    if st.button("Execute VACUUM", key="execute_vacuum"):
        try:
            agent.run_query(query) # DDL/Utility commands don't return results
            st.success("Database vacuumed.")
        except Exception as e:
            st.error(f"Error executing query: {e}")

def render_pragma_query_builder(agent: AgentPearl):
    st.subheader("PRAGMA Settings")

    with st.expander("What are PRAGMA commands?"):
        st.markdown("**PRAGMA commands are special commands in SQLite to control its environment or query its internal state.**")
        st.markdown("They are not standard SQL and are specific to SQLite.")
        st.markdown("**Examples:**")
        st.markdown("- `PRAGMA journal_mode = WAL;` (sets journaling mode)")
        st.markdown("- `PRAGMA foreign_keys = ON;` (enables foreign key enforcement)")
        st.markdown("- `PRAGMA table_info(my_table);` (gets column info for a table)")

    common_pragmas = {
        "journal_mode": {"value": "WAL", "description": "Sets the journaling mode for the database.", "options": ["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"]},
        "foreign_keys": {"value": "ON", "description": "Enables or disables foreign key constraint enforcement.", "options": ["ON", "OFF"]},
        "auto_vacuum": {"value": "FULL", "description": "Configures automatic database vacuuming.", "options": ["NONE", "FULL", "INCREMENTAL"]},
        "cache_size": {"value": "-2000", "description": "Sets the maximum number of database disk pages that can be held in memory.", "options": []},
        "synchronous": {"value": "NORMAL", "description": "Sets the level of disk synchronization.", "options": ["OFF", "NORMAL", "FULL"]},
        "recursive_triggers": {"value": "ON", "description": "Enables or disables recursive triggers.", "options": ["ON", "OFF"]},
        "secure_delete": {"value": "ON", "description": "Enables or disables secure deletion of data.", "options": ["ON", "OFF"]},
        "temp_store": {"value": "MEMORY", "description": "Sets where temporary tables and indices are stored.", "options": ["DEFAULT", "FILE", "MEMORY"]},
        "mmap_size": {"value": "134217728", "description": "Sets the maximum number of bytes of memory that may be used for memory-mapped I/O.", "options": []},
        "page_size": {"value": "4096", "description": "Sets the database page size.", "options": []},
        "read_uncommitted": {"value": "OFF", "description": "Enables or disables read uncommitted isolation level.", "options": ["ON", "OFF"]},
        "query_only": {"value": "OFF", "description": "Sets the database to read-only mode.", "options": ["ON", "OFF"]},
    }

    pragma_options = ["-- Select a PRAGMA command --"] + sorted(list(common_pragmas.keys()))
    selected_pragma_command_name = st.selectbox(
        "Select PRAGMA Command:",
        options=pragma_options,
        key="pragma_command_select"
    )

    pragma_command = ""
    pragma_value = ""
    if selected_pragma_command_name != "-- Select a PRAGMA command --":
        pragma_command = selected_pragma_command_name
        pragm-info == common_pragmas[pragma_command]

        default_pragma_value = pragm-info["value"]
        value_options = pragm-info["options"]

        if value_options:
            pragma_value = st.selectbox(
                f"Value for {pragma_command}:",
                options=value_options,
                index=value_options.index(default_pragma_value) if default_pragma_value in value_options else 0,
                key="pragma_value_select"
            )
        else:
            pragma_value = st.text_input(
                f"Value for {pragma_command} (e.g., {default_pragma_value}):",
                value=default_pragma_value,
                key="pragma_value_input"
            )

    query = ""
    if pragma_command:
        if pragma_value:
            query = f"PRAGMA {pragma_command} = {pragma_value};"
        else:
            query = f"PRAGMA {pragma_command};"

    if query:
        st.code(query, language="sql")
        if st.button("Execute PRAGMA", key="execute_pragma"):
            try:
                result, column_names = agent.run_query(query)
                if result:
                    df = pd.DataFrame(result, columns=column_names)
                    st.dataframe(df)
                else:
                    st.success("PRAGMA command executed.")
            except Exception as e:
                st.error(f"Error executing query: {e}")
    else:
        st.info("Please select a PRAGMA command.")

def render_advanced_queries_builder(agent: AgentPearl, table_name: str):
    st.subheader("Build Advanced Queries")

    advanced_query_type = st.radio(
        "Select Advanced Query Type:",
        ("Subquery (EXISTS/IN)", "UNION / UNION ALL", "FTS MATCH"),
        key=f"advanced_query_type_{table_name}"
    )

    if advanced_query_type == "Subquery (EXISTS/IN)":
        st.write("Build a query using EXISTS or IN with a subquery.")

        with st.expander("How to use Subqueries (EXISTS/IN)?"):
            st.markdown("**Subqueries are queries nested inside another query.**")
            st.markdown("They are used to perform operations that require data from another query as input.")
            st.markdown("**EXISTS / NOT EXISTS:** Checks for the existence of rows returned by the subquery.")
            st.markdown("**IN / NOT IN:** Checks if a value is present in the result set of the subquery.")
            st.markdown("**Examples:**")
            st.markdown("- `SELECT name FROM Customers WHERE EXISTS (SELECT 1 FROM Orders WHERE Orders.customer_id = Customers.id);`")
            st.markdown("- `SELECT product_name FROM Products WHERE category_id IN (SELECT id FROM Categories WHERE category_name = 'Electronics');`")

        main_query_part = st.text_area(
            "Main Query (e.g., SELECT * FROM main_table WHERE):",
            value=f"SELECT * FROM {table_name} WHERE ",
            key=f"subquery_main_part_{table_name}"
        )
        subquery_operator = st.selectbox(
            "Operator:",
            ("EXISTS", "NOT EXISTS", "IN", "NOT IN"),
            key=f"subquery_operator_{table_name}"
        )
        subquery_text = st.text_area(
            "Subquery (e.g., SELECT id FROM other_table WHERE condition):",
            key=f"subquery_text_{table_name}"
        )

        if main_query_part and subquery_text:
            query = f"{main_query_part} {subquery_operator} ({subquery_text});"
            st.code(query, language="sql")
            if st.button("Execute Subquery", key=f"execute_subquery_{table_name}"):
                try:
                    result, column_names = agent.run_query(query)
                    if result:
                        df = pd.DataFrame(result, columns=column_names)
                        st.dataframe(df)
                    else:
                        st.info("No results found.")
                except Exception as e:
                    st.error(f"Error executing query: {e}")
        else:
            st.info("Please provide both main query part and subquery.")

    elif advanced_query_type == "UNION / UNION ALL":
        st.write("Combine results from two SELECT queries.")

        with st.expander("How to use UNION / UNION ALL?"):
            st.markdown("**UNION / UNION ALL combine the result sets of two or more SELECT statements.**")
            st.markdown("**UNION:** Combines result sets and removes duplicate rows.")
            st.markdown("**UNION ALL:** Combines result sets and includes all duplicate rows.")
            st.markdown("Both SELECT statements must have the same number of columns and compatible data types.")
            st.markdown("**Example:** `SELECT name FROM Employees UNION ALL SELECT name FROM Contractors;`")

        first_select_query = st.text_area(
            "First SELECT Query:",
            value=f"SELECT * FROM {table_name};",
            key=f"union_first_query_{table_name}"
        )
        union_type = st.radio(
            "Union Type:",
            ("UNION", "UNION ALL"),
            key=f"union_type_{table_name}",
            horizontal=True
        )
        second_select_query = st.text_area(
            "Second SELECT Query:",
            key=f"union_second_query_{table_name}"
        )

        if first_select_query and second_select_query:
            query = f"{first_select_query} {union_type} {second_select_query};"
            st.code(query, language="sql")
            if st.button("Execute UNION Query", key=f"execute_union_{table_name}"):
                try:
                    result, column_names = agent.run_query(query)
                    if result:
                        df = pd.DataFrame(result, columns=column_names)
                        st.dataframe(df)
                    else:
                        st.info("No results found.")
                except Exception as e:
                    st.error(f"Error executing query: {e}")
        else:
            st.info("Please provide both SELECT queries.")

    elif advanced_query_type == "FTS MATCH":
        st.write("Perform a Full-Text Search (FTS) MATCH query.")

        with st.expander("How to use FTS MATCH queries?"):
            st.markdown("**FTS (Full-Text Search) allows efficient searching for words or phrases within text.**")
            st.markdown("This requires your table to be configured as an FTS table (e.g., using `CREATE VIRTUAL TABLE ... USING fts5`).")
            st.markdown("**MATCH Operators:**")
            st.markdown("- `AND`: Both terms must be present (e.g., `apple AND orange`)")
            st.markdown("- `OR`: Either term can be present (e.g., `apple OR orange`)")
            st.markdown("- `NOT`: Excludes results (e.g., `apple NOT orange`)")
            st.markdown("- `\"phrase\"`: Exact phrase match (e.g., `\"red apple\"`)")
            st.markdown("**Example:** `SELECT * FROM documents WHERE documents MATCH 'database AND SQL';`")

        fts_table_name = st.text_input(
            "FTS Table Name (must be an FTS table):",
            value=table_name,
            key=f"fts_table_name_{table_name}"
        )
        match_query = st.text_input(
            "MATCH Query (e.g., 'apple OR orange'):",
            key=f"fts_match_query_{table_name}"
        )

        if fts_table_name and match_query:
            query = f"SELECT * FROM {fts_table_name} WHERE {fts_table_name} MATCH '{match_query}';"
            st.code(query, language="sql")
            if st.button("Execute FTS MATCH Query", key=f"execute_fts_match_{table_name}"):
                try:
                    result, column_names = agent.run_query(query)
                    if result:
                        df = pd.DataFrame(result, columns=column_names)
                        st.dataframe(df)
                    else:
                        st.info("No results found.")
                except Exception as e:
                    st.error(f"Error executing query: {e}")
        else:
            st.info("Please enter FTS table name and MATCH query.")
