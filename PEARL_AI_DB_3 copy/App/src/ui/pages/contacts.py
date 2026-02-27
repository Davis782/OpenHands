import streamlit as st
import pandas as pd
from App.src.core.database.data_access import DataAccess
from App.src.core.database.query_builder import QueryBuilder

def render_contacts_page(dal: DataAccess):
    """
    Renders the Contact Management page in the Streamlit application.
    Allows users to create, view, and edit contact records.
    """
    st.header("Contact Management")

    if not st.session_state.pearl_id:
        st.warning("Please set a PEARL ID in the sidebar to manage contacts.")
        return

    st.subheader("Create New Contact")
    with st.form("new_contact_form", clear_on_submit=True):
        first_name = st.text_input("First Name", max_chars=255)
        last_name = st.text_input("Last Name", max_chars=255)
        email = st.text_input("Email", max_chars=255)
        phone = st.text_input("Phone", max_chars=255)
        city = st.text_input("City", max_chars=255)

        submitted = st.form_submit_button("Add Contact")
        if submitted:
            if first_name and last_name and email and phone and city:
                try:
                    insert_sql = """
                    INSERT INTO Contacts (first_name, last_name, email, phone, city, pearl_id)
                    VALUES (:first_name, :last_name, :email, :phone, :city, :pearl_id)
                    """
                    insert_params = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "city": city,
                        "pearl_id": st.session_state.pearl_id
                    }
                    
                    dal._execute_raw_sql(insert_sql, insert_params)
                    st.success(f"Contact '{first_name} {last_name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding contact: {e}")
            else:
                st.error("Please fill in all required fields.")

    st.subheader("Existing Contacts")
    try:
        contacts = dal.fetch_all("contacts/get_all_contacts.sql", {"pearl_id": st.session_state.pearl_id})
        if contacts:
            contacts_df = pd.DataFrame(contacts)
            st.dataframe(contacts_df, use_container_width=True)

            st.subheader("Edit / Delete Contact")
            contact_to_edit_name = st.selectbox(
                "Select a contact to edit or delete",
                options=[""] + [f"{c['first_name']} {c['last_name']} (ID: {c['contact_id']})" for c in contacts],
                key="edit_contact_select"
            )

            if contact_to_edit_name:
                contact_id_str = contact_to_edit_name.split("(ID: ")[1][:-1]
                selected_contact_id = int(contact_id_str)
                selected_contact = next((c for c in contacts if c['contact_id'] == selected_contact_id), None)

                if selected_contact:
                    with st.form("edit_contact_form", clear_on_submit=False):
                        st.write(f"Editing Contact ID: {selected_contact['contact_id']}")
                        updated_first_name = st.text_input("First Name", value=selected_contact['first_name'], max_chars=255)
                        updated_last_name = st.text_input("Last Name", value=selected_contact['last_name'], max_chars=255)
                        updated_email = st.text_input("Email", value=selected_contact['email'], max_chars=255)
                        updated_phone = st.text_input("Phone", value=selected_contact['phone'], max_chars=255)
                        updated_city = st.text_input("City", value=selected_contact['city'], max_chars=255)

                        col1, col2 = st.columns(2)
                        with col1:
                            update_submitted = st.form_submit_button("Update Contact")
                        with col2:
                            delete_submitted = st.form_submit_button("Delete Contact")

                        if update_submitted:
                            if updated_first_name and updated_last_name and updated_email and updated_phone and updated_city:
                                try:
                                    update_params = {
                                        "first_name": updated_first_name,
                                        "last_name": updated_last_name,
                                        "email": updated_email,
                                        "phone": updated_phone,
                                        "city": updated_city,
                                        "contact_id": selected_contact['contact_id'],
                                        "pearl_id": st.session_state.pearl_id
                                    }
                                    dal._execute_raw_sql("contacts/update_contact.sql", update_params)
                                    st.success(f"Contact '{updated_first_name} {updated_last_name}' updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating contact: {e}")
                            else:
                                st.error("Please fill in all required fields for update.")
                        elif delete_submitted:
                            st.session_state.contact_to_delete = selected_contact['contact_id']
                            st.rerun()
                else:
                    st.info("Select a contact from the dropdown above to view its details and edit or delete it.")
            else:
                st.info("Select a contact from the dropdown above to view its details and edit or delete it.")
        else:
            st.info("No contacts found for this PEARL ID. Create a new contact above.")
    except Exception as e:
        st.error(f"Error loading contacts: {e}")

    if "contact_to_delete" in st.session_state and st.session_state.contact_to_delete:
        contact_id_to_delete = st.session_state.contact_to_delete
        # Fetch contact details for confirmation message
        contact_to_delete_details = next((c for c in contacts if c['contact_id'] == contact_id_to_delete), None)
        if contact_to_delete_details:
            st.warning(f"Are you sure you want to delete contact: {contact_to_delete_details['first_name']} {contact_to_delete_details['last_name']} (ID: {contact_id_to_delete})?")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("Confirm Delete", key="confirm_delete_contact"):
                    try:
                        dal._execute_raw_sql("contacts/delete_contact.sql", {"contact_id": contact_id_to_delete, "pearl_id": st.session_state.pearl_id})
                        st.success(f"Contact (ID: {contact_id_to_delete}) deleted successfully!")
                        del st.session_state.contact_to_delete
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting contact: {e}")
            with col_cancel:
                if st.button("Cancel", key="cancel_delete_contact"):
                    del st.session_state.contact_to_delete
                    st.rerun()
        else:
            del st.session_state.contact_to_delete # Clear if contact not found
            st.rerun()

