import streamlit as st
from App.src.core.database.query_builder import QueryBuilder
from datetime import date

def render_accounting_page(dal):
    """
    Renders the Accounting management page with full CRUD capabilities.
    """
    st.title("Accounting Management")

    if st.session_state.pearl_id is None:
        st.warning("Please select an active PEARL ID in the PEARL ID Management section to manage accounting entries.")
        return
    dal.set_pearl_id(st.session_state.pearl_id)
    
    # --- Create New Entry ---
    st.subheader("Add New Transaction")
    with st.form("add_transaction_form"):
        col1, col2 = st.columns(2)
        with col1:
            transaction_date = st.date_input("Transaction Date", value=date.today())
            description = st.text_input("Description")
        with col2:
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            transaction_type = st.selectbox("Type", ["Income", "Expense"])
        
        submit_button = st.form_submit_button("Add Transaction")
        
        if submit_button:
            if not description:
                st.error("Description is required.")
            elif not st.session_state.pearl_id: # Added explicit check for pearl_id
                st.error("PEARL ID is required to add a transaction. Please select one.")
            else:
                st.write(f"DEBUG: st.session_state.pearl_id before insert: {st.session_state.pearl_id}") # Debugging line
                try:
                    # Use QueryBuilder for Insert
                    insert_builder = QueryBuilder().from_table("Accounting").insert(
                        pearl_id=st.session_state.pearl_id,
                        transaction_date=transaction_date.isoformat(),
                        description=description,
                        amount=amount,
                        type=transaction_type
                    )
                    sql, params = insert_builder.build_insert()
                    dal._execute_raw_sql(sql, params)
                    st.success("Transaction added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding transaction: {e}")

    # --- Existing Transactions ---
    st.subheader("Existing Transactions")
    try:
        # Use QueryBuilder for Select
        select_builder = QueryBuilder().from_table("Accounting").select([
            "id", "transaction_date", "description", "amount", "type"
        ]).where("pearl_id = :pearl_id", {"pearl_id": st.session_state.pearl_id})
        
        sql, params = select_builder.build()
        transactions = dal._fetch_raw_sql(sql, params)
        
        if transactions:
            for entry in transactions:
                with st.expander(f"{entry['transaction_date']} - {entry['description']} ({entry['type']})"):
                    # Edit Form
                    with st.form(f"edit_form_{entry['id']}"):
                        e_col1, e_col2 = st.columns(2)
                        with e_col1:
                            e_date = st.date_input("Date", value=date.fromisoformat(entry['transaction_date']), key=f"date_{entry['id']}")
                            e_desc = st.text_input("Description", value=entry['description'], key=f"desc_{entry['id']}")
                        with e_col2:
                            e_amount = st.number_input("Amount", value=float(entry['amount']), min_value=0.0, format="%.2f", key=f"amount_{entry['id']}")
                            e_type = st.selectbox("Type", ["Income", "Expense"], index=0 if entry['type'] == "Income" else 1, key=f"type_{entry['id']}")
                        
                        update_btn = st.form_submit_button("Update")
                        if update_btn:
                            try:
                                update_builder = QueryBuilder().from_table("Accounting").update(
                                    transaction_date=e_date.isoformat(),
                                    description=e_desc,
                                    amount=e_amount,
                                    type=e_type
                                ).where("id = :id", {"id": entry['id']})
                                
                                sql, params = update_builder.build_update()
                                dal._execute_raw_sql(sql, params)
                                st.success("Transaction updated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating: {e}")
                    
                    # Delete Button
                    if st.button(f"Delete Transaction {entry['id']}", key=f"del_{entry['id']}"):
                        try:
                            delete_builder = QueryBuilder().from_table("Accounting").from_table("Accounting").delete().where("id = :id", {"id": entry['id']})
                            sql, params = delete_builder.build_delete()
                            dal._execute_raw_sql(sql, params)
                            st.success("Transaction deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting: {e}")
        else:
            st.info("No transactions found for this PEARL ID.")
            
    except Exception as e:
        st.error(f"Error loading transactions: {e}")