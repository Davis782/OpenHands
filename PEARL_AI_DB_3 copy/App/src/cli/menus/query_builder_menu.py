from App.src.cli.cli_utils import clear, get_user_input, print_menu
from App.src.agent_pearl.agent_pearl import AgentPearl

def query_builder_menu(agent: AgentPearl):
    """
    Provides a menu-driven interface for building and executing SQL queries.
    """
    while True:
        clear()
        print_menu("Query Builder", [
            "Build SELECT Query",
            "Build INSERT Query",
            "Build UPDATE Query",
            "Build DELETE Query",
            "Back to Main Menu"
        ])

        choice = get_user_input("Enter your choice")

        if choice == '1':
            _build_select_query(agent)
        elif choice == '2':
            _build_insert_query(agent)
        elif choice == '3':
            _build_update_query(agent)
        elif choice == '4':
            _build_delete_query(agent)
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")
            get_user_input("Press Enter to continue...")


def _build_insert_query(agent: AgentPearl):
    """
    Guides the user through building and executing an INSERT SQL query.
    """
    clear()
    print("--- Build INSERT Query ---")

    # Display available tables
    print("\nAvailable tables:")
    tables = agent.pearl_client.get_all_table_names()
    if tables:
        for i, table in enumerate(tables):
            print(f"  {i+1}. {table}")
    else:
        print("  No tables found in the database.")

    table_name_input = get_user_input("Enter table name (or number from list): ")
    if not table_name_input:
        print("Table name cannot be empty.")
        get_user_input("Press Enter to continue...")
        return

    try:
        table_index = int(table_name_input) - 1
        if 0 <= table_index < len(tables):
            table_name = tables[table_index]
        else:
            print("Invalid table number. Please try again.")
            get_user_input("Press Enter to continue...")
            return
    except ValueError:
        table_name = table_name_input # User entered a name, not a number

def _build_delete_query(agent: AgentPearl):
    """
    Guides the user through building and executing a DELETE SQL query.
    """
    clear()
    print("--- Build DELETE Query ---")

    # Display available tables
    print("\nAvailable tables:")
    tables = agent.pearl_client.get_all_table_names()
    if tables:
        for i, table in enumerate(tables):
            print(f"  {i+1}. {table}")
    else:
        print("  No tables found in the database.")

    table_name_input = get_user_input("Enter table name (or number from list): ")
    if not table_name_input:
        print("Table name cannot be empty.")
        get_user_input("Press Enter to continue...")
        return

    try:
        table_index = int(table_name_input) - 1
        if 0 <= table_index < len(tables):
            table_name = tables[table_index]
        else:
            print("Invalid table number. Please try again.")
            get_user_input("Press Enter to continue...")
            return
    except ValueError:
        table_name = table_name_input # User entered a name, not a number
    if not table_name:
        print("Table name cannot be empty.")
        get_user_input("Press Enter to continue...")
        return

    # Get and display columns for the selected table
    columns_in_table = agent.pearl_client.get_table_columns(table_name)
    if not columns_in_table:
        print(f"No columns found for table '{table_name}'.")
        get_user_input("Press Enter to continue...")
        return

    print("\nAvailable columns for WHERE clause:")
    for i, col in enumerate(columns_in_table):
        print(f"  {i+1}. {col}")
    print("  0. (No WHERE clause - delete all rows)")

    selected_column_input = get_user_input("Enter numbers of columns to use in WHERE clause (comma-separated, or 0 for no WHERE clause): ")
    
    where_clause_parts = []
    if selected_column_input == '0':
        print("WARNING: No WHERE clause specified. This will delete ALL rows from the table.")
        confirm_all = get_user_input("Are you sure you want to delete all rows? (y/n): ").lower()
        if confirm_all != 'y':
            print("Delete cancelled.")
            get_user_input("Press Enter to continue...")
            return
        where_clause = ""
    else:
        selected_column_indices = []
        try:
            selected_column_indices = [int(x.strip()) - 1 for x in selected_column_input.split(',')]
            for idx in selected_column_indices:
                if not (0 <= idx < len(columns_in_table)):
                    raise ValueError("Invalid column number.")
        except ValueError as e:
            print(f"Invalid input for column numbers: {e}. DELETE query cancelled.")
            get_user_input("Press Enter to continue...")
            return

        for idx in selected_column_indices:
            col_name = columns_in_table[idx]
            operator = get_user_input(f"Enter operator for '{col_name}' (e.g., =, >, <, LIKE): ")
            value = get_user_input(f"Enter value for '{col_name}': ")
            
            # Basic sanitization for values (add quotes for strings, leave numbers as is)
            if (value.startswith("'") and value.endswith("'")) or (value.startswith("\"") and value.endswith("\"")):
                processed_value = value # Already quoted
            elif value.replace('.', '', 1).isdigit(): # Check if it's a number (int or float)
                processed_value = value
            else:
                processed_value = f"'{value}'" # Quote as string
            
            where_clause_parts.append(f"{col_name} {operator} {processed_value}")
        where_clause = " AND ".join(where_clause_parts)

    if not where_clause and selected_column_input != '0': # If user selected columns but didn't provide valid input
        print("No WHERE clause generated. DELETE query cancelled.")
        get_user_input("Press Enter to continue...")
        return

    query = f"DELETE FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"
    query += ";"

    print(f"\nGenerated SQL: {query}")
    confirm = get_user_input("Execute this query? (y/n): ").lower()

    if confirm == 'y':
        try:
            agent.run_query(query)
            print("Query executed successfully.")
        except Exception as e:
            print(f"Error executing query: {e}")
    else:
        print("Query execution cancelled.")

    get_user_input("Press Enter to continue...")

def _build_update_query(agent: AgentPearl):
    """
    Guides the user through building and executing an UPDATE SQL query.
    """
    clear()
    print("--- Build UPDATE Query ---")
    
    # Display available tables
    print("\nAvailable tables:")
    tables = agent.pearl_client.get_all_table_names()
    if tables:
        for i, table in enumerate(tables):
            print(f"  {i+1}. {table}")
    else:
        print("  No tables found in the database.")
    
    table_name = get_user_input("Enter table name: ")
    if not table_name:
        print("Table name cannot be empty.")
        get_user_input("Press Enter to continue...")
        return

    # Get and display columns for the selected table
    columns = agent.pearl_client.get_table_columns(table_name)
    if not columns:
        print(f"No columns found for table '{table_name}'.")
        get_user_input("Press Enter to continue...")
        return

    print("\nAvailable columns for update:")
    for i, col in enumerate(columns):
        print(f"  {i+1}. {col}")

    selected_column_input = get_user_input("Enter numbers of columns to update (comma-separated): ")
    if not selected_column_input:
        print("No columns selected for update. Update cancelled.")
        get_user_input("Press Enter to continue...")
        return

    selected_column_indices = []
    try:
        selected_column_indices = [int(x.strip()) - 1 for x in selected_column_input.split(',')]
        for idx in selected_column_indices:
            if not (0 <= idx < len(columns)):
                raise ValueError("Invalid column number.")
    except ValueError as e:
        print(f"Invalid input for column numbers: {e}. Update cancelled.")
        get_user_input("Press Enter to continue...")
        return

    set_clauses = []
    for idx in selected_column_indices:
        col_name = columns[idx]
        new_value = get_user_input(f"Enter new value for column '{col_name}': ")
        
        # Basic sanitization for values (add quotes for strings, leave numbers as is)
        if new_value.startswith("'") and new_value.endswith("'") or new_value.startswith(""") and new_value.endswith("""):
            processed_value = new_value # Already quoted
        elif new_value.replace('.', '', 1).isdigit(): # Check if it's a number (int or float)
            processed_value = new_value
        else:
            processed_value = f"'{new_value}'" # Quote as string
        
        set_clauses.append(f"{col_name} = {processed_value}")
    
    set_clause_str = ", ".join(set_clauses)

    if not set_clause_str:
        print("No SET clauses generated. Update cancelled.")
        get_user_input("Press Enter to continue...")
        return

    where_clause = get_user_input("Enter WHERE clause (e.g., id = 'abc', status = 'active'): ")
    if not where_clause:
        print("WARNING: No WHERE clause specified. This will update ALL rows in the table.")
        confirm_all = get_user_input("Are you sure you want to update all rows? (y/n): ").lower()
        if confirm_all != 'y':
            print("Update cancelled.")
            get_user_input("Press Enter to continue...")
            return

    query = f"UPDATE {table_name} SET {set_clause_str}"
    if where_clause:
        query += f" WHERE {where_clause}"
    query += ";"

    print(f"\nGenerated SQL: {query}")
    confirm = get_user_input("Execute this query? (y/n): ").lower()

    if confirm == 'y':
        try:
            agent.run_query(query)
            print("Query executed successfully.")
        except Exception as e:
            print(f"Error executing query: {e}")
    else:
        print("Query execution cancelled.")

    get_user_input("Press Enter to continue...")

    # Get and display columns for the selected table
    columns = agent.pearl_client.get_table_columns(table_name)
    if not columns:
        print(f"No columns found for table '{table_name}'.")
        get_user_input("Press Enter to continue...")
        return

    print("\nAvailable columns for insertion:")
    for i, col in enumerate(columns):
        print(f"  {i+1}. {col}")

    selected_column_indices_str = get_user_input("Enter numbers of columns to insert into (comma-separated): ")
    if not selected_column_indices_str:
        print("No columns selected for insertion. Insert cancelled.")
        get_user_input("Press Enter to continue...")
        return

    selected_column_indices = []
    try:
        selected_column_indices = [int(x.strip()) - 1 for x in selected_column_indices_str.split(',')]
        for idx in selected_column_indices:
            if not (0 <= idx < len(columns)):
                raise ValueError("Invalid column number.")
    except ValueError as e:
        print(f"Invalid input for column numbers: {e}. Insert cancelled.")
        get_user_input("Press Enter to continue...")
        return

    insert_columns = [columns[idx] for idx in selected_column_indices]
    
    processed_values = []
    for col_name in insert_columns:
        value = get_user_input(f"Enter value for column '{col_name}': ")
        # Basic sanitization for values (add quotes for strings, leave numbers as is)
        if (value.startswith("'") and value.endswith("'")) or (value.startswith("\"") and value.endswith("\"")):
            processed_values.append(value) # Already quoted
        elif value.replace('.', '', 1).isdigit(): # Check if it's a number (int or float)
            processed_values.append(value)
        else:
            processed_values.append(f"'{value}'") # Quote as string

    columns_str = ", ".join(insert_columns)
    values_str = ", ".join(processed_values)

    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(processed_values)});"

    print(f"\nGenerated SQL: {query}")
    confirm = get_user_input("Execute this query? (y/n): ").lower()

    if confirm == 'y':
        try:
            agent.run_query(query)
            print("Query executed successfully.")
        except Exception as e:
            print(f"Error executing query: {e}")
    else:
        print("Query execution cancelled.")

    get_user_input("Press Enter to continue...")


def _build_select_query(agent: AgentPearl):
    """
    Guides the user through building and executing a SELECT SQL query.
    """
    clear()
    print("--- Build SELECT Query ---")

    # Display available tables
    print("\nAvailable tables:")
    tables = agent.pearl_client.get_all_table_names()
    if tables:
        for i, table in enumerate(tables):
            print(f"  {i+1}. {table}")
    else:
        print("  No tables found in the database.")

    table_name_input = get_user_input("Enter table name (or number from list): ")
    if not table_name_input:
        print("Table name cannot be empty.")
        get_user_input("Press Enter to continue...")
        return

    try:
        table_index = int(table_name_input) - 1
        if 0 <= table_index < len(tables):
            table_name = tables[table_index]
        else:
            print("Invalid table number. Please try again.")
            get_user_input("Press Enter to continue...")
            return
    except ValueError:
        table_name = table_name_input # User entered a name, not a number

    # Get and display columns for the selected table
    columns_in_table = agent.pearl_client.get_table_columns(table_name)
    if not columns_in_table:
        print(f"No columns found for table '{table_name}'.")
        get_user_input("Press Enter to continue...")
        return

    print("\nAvailable columns for selection:")
    for i, col in enumerate(columns_in_table):
        print(f"  {i+1}. {col}")
    print("  0. * (Select all columns)")

    selected_column_input = get_user_input("Enter numbers of columns to select (comma-separated, or 0 for all): ")
    if not selected_column_input:
        print("No columns selected. SELECT query cancelled.")
        get_user_input("Press Enter to continue...")
        return

    if selected_column_input == '0':
        columns = "*"
    else:
        selected_column_indices = []
        try:
            selected_column_indices = [int(x.strip()) - 1 for x in selected_column_input.split(',')]
            for idx in selected_column_indices:
                if not (0 <= idx < len(columns_in_table)):
                    raise ValueError("Invalid column number.")
        except ValueError as e:
            print(f"Invalid input for column numbers: {e}. SELECT query cancelled.")
            get_user_input("Press Enter to continue...")
            return
        columns = ", ".join([columns_in_table[idx] for idx in selected_column_indices])

    where_clause = get_user_input("Enter WHERE clause (optional, e.g., id = 'abc', status = 'active'): ")

    query = f"SELECT {columns} FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"
    query += ";"

    print(f"\nGenerated SQL: {query}")
    confirm = get_user_input("Execute this query? (y/n): ").lower()

    if confirm == 'y':
        try:
            results = agent.run_query(query)
            if results:
                print("\n--- Query Results ---")
                # Attempt to get column names for header if not '*' and results are dicts
                if columns != '*' and isinstance(results[0], dict):
                    # This part is tricky without direct cursor access here.
                    # For simplicity, we'll just print the dict keys if available.
                    print(", ".join(results[0].keys()))
                elif isinstance(results[0], tuple):
                    # If results are tuples, we can't easily get column names without schema info
                    pass # Will print tuples directly

                for row in results:
                    print(row)
            else:
                print("No results found.")
        except Exception as e:
            print(f"Error executing query: {e}")
    else:
        print("Query execution cancelled.")

    get_user_input("Press Enter to continue...")
