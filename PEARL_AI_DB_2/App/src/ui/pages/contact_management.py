import streamlit as st
from App.src.core.database.data_access import DataAccess
from App.src.core.database.query_builder import QueryBuilder

def render_contact_management_page(dal: DataAccess, pearl_id: str):
    dal.set_pearl_id(pearl_id)
    """
    Renders the Contact Management page, allowing users to create, view, update, and delete contacts.

    Args:
        dal (DataAccess): The DataAccess object for database interactions.
        pearl_id (str): The PEARL ID of the current user session.
    """
    st.header("Contact Management")

    # Create New Contact Form
    st.subheader("Create New Contact")
    with st.form("create_contact_form", clear_on_submit=True):
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        address = st.text_input("Address")
        city = st.text_input("City")
        state = st.text_input("State")
        zip_code = st.text_input("Zip Code")
        country = st.text_input("Country")
        submitted = st.form_submit_button("Add Contact")

        if submitted:
            if first_name and last_name:
                # Check if email already exists for the current pearl_id
                qb_check = QueryBuilder()
                sql_check, params_check = qb_check.select(["COUNT(*)"]).from_table("Contacts").where(condition="email = :email AND pearl_id = :pearl_id", params={"email": email, "pearl_id": pearl_id}).build()
                email_exists = dal._fetch_raw_sql(sql_check, params_check)[0]['COUNT(*)'] > 0

                if email_exists:
                    st.error(f"Error adding contact: A contact with the email '{email}' already exists for this PEARL ID.")
                else:
                    try:
                        qb = QueryBuilder()
                        sql, params = qb.from_table("Contacts").insert(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            phone=phone,
                            address=address,
                            city=city,
                            state=state,
                            zip_code=zip_code,
                            country=country,
                            pearl_id=pearl_id
                        ).build_insert()
                        dal._execute_raw_sql(sql, params)
                        st.success("Contact added successfully!")
                    except Exception as e:
                        st.error(f"Error adding contact: {e}")
            else:
                st.error("First Name and Last Name are required.")

    st.subheader("Existing Contacts")
    try:
        # Fetch all contacts for the current pearl_id
        qb = QueryBuilder()
        sql, params = qb.select(["*"]).from_table("Contacts").where(condition="pearl_id = :pearl_id", params={"pearl_id": pearl_id}).build()
        contacts = dal._fetch_raw_sql(sql, params)

        if contacts:
            for i, contact in enumerate(contacts):
                with st.expander(f"{contact['first_name']} {contact['last_name']} (ID: {contact['contact_id']})"):
                    st.write(f"**Email:** {contact['email']}")
                    st.write(f"**Phone:** {contact['phone']}")
                    st.write(f"**Address:** {contact['address']}, {contact['city']}, {contact['state']} {contact['zip_code']}, {contact['country']}")

                    # Update Form
                    st.subheader("Update Contact")
                    with st.form(f"update_contact_form_{contact['contact_id']}"):
                        new_first_name = st.text_input("First Name", value=contact['first_name'], key=f"ufn_{contact['contact_id']}")
                        new_last_name = st.text_input("Last Name", value=contact['last_name'], key=f"uln_{contact['contact_id']}")
                        new_email = st.text_input("Email", value=contact['email'], key=f"ue_{contact['contact_id']}")
                        new_phone = st.text_input("Phone", value=contact['phone'], key=f"up_{contact['contact_id']}")
                        new_address = st.text_input("Address", value=contact['address'], key=f"ua_{contact['contact_id']}")
                        new_city = st.text_input("City", value=contact['city'], key=f"uc_{contact['contact_id']}")
                        new_state = st.text_input("State", value=contact['state'], key=f"us_{contact['contact_id']}")
                        new_zip_code = st.text_input("Zip Code", value=contact['zip_code'], key=f"uzc_{contact['contact_id']}")
                        new_country = st.text_input("Country", value=contact['country'], key=f"uco_{contact['contact_id']}")
                        update_submitted = st.form_submit_button("Update Contact")

                        if update_submitted:
                            if new_first_name and new_last_name:
                                try:
                                    qb = QueryBuilder()
                                    sql, params = qb.from_table("Contacts").update(
                                        first_name=new_first_name,
                                        last_name=new_last_name,
                                        email=new_email,
                                        phone=new_phone,
                                        address=new_address,
                                        city=new_city,
                                        state=new_state,
                                        zip_code=new_zip_code,
                                        country=new_country
                                    ).where(condition="contact_id = :contact_id AND pearl_id = :pearl_id", params={"contact_id": contact['contact_id'], "pearl_id": pearl_id}).build_update()
                                    dal._execute_raw_sql(sql, params)
                                    st.success("Contact updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating contact: {e}")
                            else:
                                st.error("First Name and Last Name are required.")

                    # Delete Button
                    if st.button(f"Delete Contact (ID: {contact['contact_id']})", key=f"delete_contact_{contact['contact_id']}"):
                        try:
                            qb = QueryBuilder()
                            sql, params = qb.from_table("Contacts").delete().where(condition="contact_id = :contact_id AND pearl_id = :pearl_id", params={"contact_id": contact['contact_id'], "pearl_id": pearl_id}).build_delete()
                            dal._execute_raw_sql(sql, params)
                            st.success("Contact deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting contact: {e}")
        else:
            st.info("No contacts found.")
    except Exception as e:
        st.error(f"Error loading contacts: {e}")
