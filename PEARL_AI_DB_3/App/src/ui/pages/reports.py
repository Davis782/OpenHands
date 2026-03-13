import streamlit as st
import pandas as pd
import sqlite3
from io import StringIO, BytesIO, TextIOWrapper
import json
from App.src.core.database.query_builder import QueryBuilder

def _display_dataframe_and_download_csv(df: pd.DataFrame, report_name: str):
    """
    Displays a DataFrame and provides a download button for CSV.
    """
    if not df.empty:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"Download {report_name} as CSV",
            data=csv,
            file_name=f"{report_name.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            key=f"download_csv_{report_name.lower().replace(' ', '_')}"
        )
    else:
        st.info(f"No data available for {report_name}.")

def _export_dataframe_to_db(df: pd.DataFrame, table_name: str, db_name: str = "exported_report.db"):
    """
    Exports a Pandas DataFrame to a new SQLite database file.
    """
    conn = None
    try:
        print("DataFrame content before to_sql:")
        print(df)
        print("DataFrame dtypes before to_sql:")
        print(df.dtypes)
        conn = sqlite3.connect(db_name)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        st.success(f"Report successfully exported to '{table_name}' table in '{db_name}'.")
        return True
    except Exception as e:
        st.error(f"Error exporting report to database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def render_reports_page(dal):
    """
    Renders the Reports management page.
    """
    st.title("Reports & Analytics")

    st.write("Welcome to the Reports module. Here you can generate various business reports.")

    # --- Report Selection ---
    report_type = st.selectbox("Select Report Type", [
        "Job Cost Summary",
        "Tasks by Job",
        "Contact Directory",
        "Financial Transaction Log",
        "Jobs by Budget Range",
        "CSV Import",
        "Folder Structure Report"
    ])

    # Render the selected report's UI directly
    if report_type == "Job Cost Summary":
        render_job_cost_report(dal)
    elif report_type == "Tasks by Job":
        render_tasks_by_job_report(dal)
    elif report_type == "Contact Directory":
        render_contact_directory_report(dal)
    elif report_type == "Financial Transaction Log":
        render_financial_log_report(dal)
    elif report_type == "Jobs by Budget Range":
        st.subheader("Report: Jobs by Budget Range")
        st.subheader("Filter by Budget Range")
        min_budget = st.number_input("Minimum Budget", min_value=0.0, value=0.0, step=100.0, key="min_budget_input")
        max_budget = st.number_input("Maximum Budget", min_value=0.0, value=10000.0, step=100.0, key="max_budget_input")

        if st.button("Generate Budget Report"):
            try:
                sql_query = dal._load_sql_query("reports/jobs_by_budget_range.sql")
                params = {
                    "pearl_id": st.session_state.pearl_id,
                    "min_budget": min_budget,
                    "max_budget": max_budget
                }
                jobs = dal._fetch_raw_sql(sql_query, params)
                if jobs:
                    df = pd.DataFrame(jobs, columns=["job_name", "description", "budget", "start_date"])
                    _display_dataframe_and_download_csv(df, "Jobs by Budget Range")

                    # Add DB export option
                    if st.button("Export Jobs by Budget Range to DB"):
                        _export_dataframe_to_db(df, "jobs_by_budget_range")
                else:
                    st.info("No jobs found within the specified budget range.")
            except Exception as e:
                st.error(f"Error generating Jobs by Budget Range report: {e}")
    elif report_type == "CSV Import":
        render_csv_import_page(dal)
    elif report_type == "Folder Structure Report":
        render_folder_structure_report(dal)

def render_job_cost_report(dal):
    try:
        qb = QueryBuilder().from_table("Jobs").select(["job_name", "description", "budget", "start_date"])
        sql, params = qb.where("pearl_id = :pearl_id", {"pearl_id": st.session_state.pearl_id}).build()
        jobs = dal._fetch_raw_sql(sql, params)
        if jobs:
            df = pd.DataFrame(jobs, columns=["job_name", "description", "budget", "start_date"])
            _display_dataframe_and_download_csv(df, "Job Cost Summary")

            # Add DB export option
            if st.button("Export Job Cost Summary to DB"):
                _export_dataframe_to_db(df, "job_cost_summary")
        else:
            st.info("No jobs found to report.")
    except Exception as e:
        st.error(f"Error generating job report: {e}")

def render_contact_directory_report(dal):
    try:
        qb = QueryBuilder().from_table("Contacts").select(["first_name", "last_name", "email", "phone", "city"])
        sql, params = qb.where("pearl_id = :pearl_id", {"pearl_id": st.session_state.pearl_id}).build()
        contacts = dal._fetch_raw_sql(sql, params)
        if contacts:
            df = pd.DataFrame(contacts, columns=["first_name", "last_name", "email", "phone", "city"])
            _display_dataframe_and_download_csv(df, "Contact Directory")

            # Add DB export option
            if st.button("Export Contact Directory to DB"):
                _export_dataframe_to_db(df, "contact_directory")
        else:
            st.info("No contacts found to report.")
    except Exception as e:
        st.error(f"Error generating contact report: {e}")

def render_financial_log_report(dal):
    try:
        qb = QueryBuilder().from_table("Accounting").select(["transaction_date", "description", "amount", "type"])
        sql, params = qb.where("pearl_id = :pearl_id", {"pearl_id": st.session_state.pearl_id}).build()
        entries = dal._fetch_raw_sql(sql, params)
        if entries:
            df = pd.DataFrame(entries, columns=["transaction_date", "description", "amount", "type"])
            _display_dataframe_and_download_csv(df, "Financial Transaction Log")

            # Add DB export option
            if st.button("Export Financial Transaction Log to DB"):
                _export_dataframe_to_db(df, "financial_transaction_log")
        else:
            st.info("No financial entries found to report.")
    except Exception as e:
        st.error(f"Error generating financial report: {e}")

def render_csv_import_page(dal):
    """
    Renders the CSV import page, allowing users to upload a CSV file
    and select a target table for data import.
    """
    st.subheader("CSV Data Import")
    st.write("Upload a CSV file to import data into your database.")

    uploaded_file = st.file_uploader("Choose a data file", type=["csv", "txt"])
    selected_encoding = st.selectbox("Select file encoding", ["utf-8", "latin-1", "cp1252"], index=0)

    if uploaded_file is not None:
        try:
            uploaded_file.seek(0)
            # Use TextIOWrapper to handle encoding explicitly
            text_io_wrapper = io.TextIOWrapper(uploaded_file, encoding=selected_encoding, errors='replace')
            if uploaded_file.name.endswith('.txt'):
                # Assuming .txt files are also comma-separated for now.
                # A more robust solution would allow the user to specify a delimiter.
                df = pd.read_csv(text_io_wrapper, sep=',')
            else: # Default to CSV for .csv and other types
                df = pd.read_csv(text_io_wrapper)
            st.success("CSV file loaded successfully!")
            st.write("Preview of uploaded data:")
            st.dataframe(df.head())

            table_names = dal.get_all_table_names()
            if not table_names:
                st.warning("No tables found in the database. Please create tables before importing data.")
                return

            selected_table = st.selectbox("Select Target Table", table_names)

            # --- CSV Template Download ---
            if selected_table:
                try:
                    # Get column names for the selected table
                    table_columns = dal.get_table_columns(selected_table)
                    if table_columns:
                        # Create an empty DataFrame with these columns as headers
                        template_df = pd.DataFrame(columns=table_columns)
                        template_csv = template_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"Download {selected_table} CSV Template",
                            data=template_csv,
                            file_name=f"{selected_table}_template.csv",
                            mime="text/csv",
                            key=f"download_template_{selected_table}"
                        )
                    else:
                        st.info(f"No columns found for table '{selected_table}'. Cannot generate template.")
                except Exception as e:
                    st.error(f"Error generating CSV template for '{selected_table}': {e}")

            import_mode = st.radio("Import Mode", ("Insert New Records", "Update Existing Records"))

            if st.button("Process CSV Import"):
                st.info(f"Initiating import to table '{selected_table}' in '{import_mode}' mode...")
                try:
                    dal.import_csv_to_table(df, selected_table, import_mode)
                    st.success(f"CSV data successfully imported to table '{selected_table}'!")
                except Exception as e:
                    st.error(f"Error during CSV import: {e}")

        except Exception as e:
            st.error(f"Error during CSV import: {e}")

def render_folder_structure_report(dal):
    """
    Renders the folder structure report, showing PEARL IDs, their tables, and row counts.
    """
    st.markdown("## Folder Structure Report")
    st.write("This report visualizes the hierarchical structure of PEARL IDs and their associated tables.")

    if st.session_state.pearl_id:
        st.info(f"Displaying structure for active PEARL ID: {st.session_state.pearl_id}")
        try:
            # Assuming dal.pearl_client is an instance of PearlClient
            report_data = dal.pearl_client.get_folder_structure_report()

            if report_data:
                # Filter report to only show the active PEARL ID
                active_pearl_id_data = report_data.get(st.session_state.pearl_id)
                if active_pearl_id_data:
                    st.write(f"### PEARL ID: {st.session_state.pearl_id}")
                    st.write(f"**Entity Type:** {active_pearl_id_data["entity_type"]}")
                    st.write(f"**Attributes:** {active_pearl_id_data["attributes"]}")

                    report_rows = []
                    if active_pearl_id_data["tables"]:
                        for table in active_pearl_id_data["tables"]:
                            if table["name"] != "sqlite_sequence": # Exclude system table
                                # Convert attributes dictionary to JSON string for database storage
                                attributes_json = json.dumps(active_pearl_id_data["attributes"])
                                report_rows.append({
                                    "PEARL ID": st.session_state.pearl_id,
                                    "Entity Type": active_pearl_id_data["entity_type"],
                                    "Attributes": attributes_json,
                                    "Table Name": table["name"],
                                    "Row Count": table["row_count"]
                                })

                    if report_rows:
                        df = pd.DataFrame(report_rows)
                        _display_dataframe_and_download_csv(df, "Folder Structure Report")
                        if st.button("Export Folder Structure Report to DB"):
                            _export_dataframe_to_db(df, "folder_structure_report")
                    else:
                        st.info("No tables found for this PEARL ID.")
                else:
                    st.warning(f"No report data found for active PEARL ID: {st.session_state.pearl_id}")
            else:
                st.info("No folder structure data available.")
        except Exception as e:
            st.error(f"Error generating folder structure report: {e}")
    else:
        st.warning("Please select an active PEARL ID to view the folder structure report.")

def render_tasks_by_job_report(dal):
    """
    Renders the Tasks by Job report, allowing users to select a job
    and view all associated tasks.
    """
    st.subheader("Report: Tasks by Job")

    if not st.session_state.pearl_id:
        st.warning("Please set a PEARL ID in the sidebar to view tasks by job.")
        return

    try:
        # 1. Get all jobs for the current PEARL ID
        jobs = dal.fetch_all("jobs/get_all_jobs.sql")

        if jobs:
            job_names = [job["job_name"] for job in jobs]
            selected_job_name = st.selectbox("Select a Job to view its tasks", options=job_names)

            if selected_job_name:
                selected_job = next((dict(job) for job in jobs if job["job_name"] == selected_job_name), None)

                if selected_job:
                    st.write(f"### Tasks for Job: {selected_job['job_name']}")

                    # 2. Fetch tasks for the selected job
                    # We'll need a new SQL file: jobs/get_tasks_for_job.sql
                    tasks = dal.fetch_all("jobs/get_tasks_for_job.sql", {"job_id": selected_job["job_id"]})

                    if tasks:
                        tasks_df = pd.DataFrame([dict(task) for task in tasks])
                        _display_dataframe_and_download_csv(tasks_df, f"Tasks for {selected_job['job_name']}")

                        if st.button(f"Export Tasks for {selected_job['job_name']} to DB"):
                            _export_dataframe_to_db(tasks_df, f"tasks_for_{selected_job['job_name'].replace(' ', '_')}")
                    else:
                        st.info(f"No tasks found for job: {selected_job['job_name']}.")
                else:
                    st.error("Selected job not found.")
        else:
            st.info("No jobs found for the current PEARL ID. Create some jobs first.")
    except Exception as e:
        st.error(f"Error generating Tasks by Job report: {e}")


