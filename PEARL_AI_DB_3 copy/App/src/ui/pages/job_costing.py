import streamlit as st
from App.src.core.database.data_access import DataAccess
from App.src.core.database.query_builder import QueryBuilder
import pandas as pd

def render_job_costing_page(dal: DataAccess):
    """
    Renders the Job Cost Tracking page in the Streamlit application.
    Allows users to create, view, and edit job records.
    """
    st.header("Job Cost Tracking")

    if not st.session_state.pearl_id:
        st.warning("Please set a PEARL ID in the sidebar to manage jobs.")
        return

    selected_job = None # Initialize selected_job to None

    st.subheader("Create New Job")
    with st.form("new_job_form", clear_on_submit=True):
        job_name = st.text_input("Job Name", max_chars=255)
        description = st.text_area("Description")
        budget = st.number_input("Budget", min_value=0.0, format="%.2f")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

        submitted = st.form_submit_button("Add Job")
        if submitted:
            if job_name and budget is not None and start_date and end_date:
                try:
                    # Using QueryBuilder for INSERT
                    qb = QueryBuilder()
                    sql, params = qb.from_table("Jobs").insert(
                        job_name=job_name,
                        description=description,
                        budget=budget,
                        start_date=start_date.isoformat(),
                        end_date=end_date.isoformat(),
                        pearl_id=st.session_state.pearl_id
                    ).build_insert()
                    
                    # The QueryBuilder.insert() and build_insert() methods are not yet implemented.
                    # For now, we'll use a raw SQL string.
                    
                    insert_sql = """
                    INSERT INTO Jobs (job_name, description, budget, start_date, end_date, pearl_id)
                    VALUES (:job_name, :description, :budget, :start_date, :end_date, :pearl_id)
                    """
                    insert_params = {
                        "job_name": job_name,
                        "description": description,
                        "budget": budget,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "pearl_id": st.session_state.pearl_id
                    }
                    
                    dal._execute_raw_sql(insert_sql, insert_params)
                    st.success(f"Job '{job_name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding job: {e}")
            else:
                st.error("Please fill in all required fields (Job Name, Budget, Start Date, End Date).")

    st.subheader("Existing Jobs")
    try:
        # Set the PEARL ID for the DataAccess object

        # Using static SQL file for SELECT all jobs for the current PEARL_ID
        jobs = dal.fetch_all("jobs/get_all_jobs.sql")
        if jobs:
            # Convert list of sqlite3.Row to pandas DataFrame for better display
            df = pd.DataFrame([dict(row) for row in jobs])
            st.dataframe(df)

            # --- Edit/Delete Job (Placeholder) ---
            st.subheader("Edit / Delete Job")
            job_names = [job["job_name"] for job in jobs]
            selected_job_name = st.selectbox("Select a job to edit or delete", options=job_names)
            st.info("Select a job from the dropdown above to view its details and edit or delete it.")

            if selected_job_name:
                # Fetch details of the selected job
                # This would ideally use a specific SQL query like get_job_by_name.sql
                # For now, we'll filter from the fetched list
                selected_job = next((dict(job) for job in jobs if job["job_name"] == selected_job_name), None)

                if selected_job:
                    with st.form(f"edit_job_form_{selected_job['job_id']}"):
                        st.write(f"Editing Job ID: {selected_job['job_id']}")
                        edited_job_name = st.text_input("Job Name", value=selected_job["job_name"], key=f"edit_name_{selected_job['job_id']}")
                        edited_description = st.text_area("Description", value=selected_job["description"], key=f"edit_desc_{selected_job['job_id']}")
                        edited_budget = st.number_input("Budget", value=float(selected_job["budget"]), min_value=0.0, format="%.2f", key=f"edit_budget_{selected_job['job_id']}")
                        edited_start_date = st.date_input("Start Date", value=pd.to_datetime(selected_job["start_date"]), key=f"edit_start_{selected_job['job_id']}")
                        edited_end_date = st.date_input("End Date", value=pd.to_datetime(selected_job["end_date"]), key=f"edit_end_{selected_job['job_id']}")

                        col1, col2 = st.columns(2)
                        with col1:
                            update_submitted = st.form_submit_button("Update Job")
                        with col2:
                            delete_submitted = st.form_submit_button("Delete Job")

                        if update_submitted:
                            try:
                                qb = QueryBuilder()
                                sql, params = qb.from_table("Jobs").update(
                                    job_name=edited_job_name,
                                    description=edited_description,
                                    budget=edited_budget,
                                    start_date=edited_start_date.isoformat(),
                                    end_date=edited_end_date.isoformat()
                                ).where("job_id = :job_id AND pearl_id = :pearl_id", {"job_id": selected_job["job_id"], "pearl_id": st.session_state.pearl_id}).build_update()
                                
                                dal._execute_raw_sql(sql, params)
                                st.success(f"Job '{edited_job_name}' updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating job: {e}")

                        if delete_submitted:
                            st.warning(f"Are you sure you want to delete job '{selected_job_name}'? This action cannot be undone.")
                            try:
                                qb = QueryBuilder()
                                sql, params = qb.from_table("Jobs").where(
                                    "job_id = :job_id", {"job_id": selected_job["job_id"]}
                                ).delete().build_delete()
                                
                                dal._execute_raw_sql(sql, params)
                                st.success(f"Job '{selected_job_name}' deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting job: {e}")

        else:
            st.info("No jobs found for this PEARL ID. Create a new job above.")

    except Exception as e:
        st.error(f"Error loading jobs: {e}")

    # --- Alarm Management for Selected Job ---
    if selected_job:
        st.subheader(f"Alarms for Job: {selected_job['job_name']}")

        # Form to create a new alarm
        with st.form(f"new_alarm_form_{selected_job['job_id']}", clear_on_submit=True):
            st.write("Set a New Alarm")
            alarm_date = st.date_input("Alarm Date")
            alarm_time = st.time_input("Alarm Time")
            alarm_message = st.text_area("Message (Optional)")
            alarm_recurrence = st.selectbox("Recurrence", ['once', 'daily', 'weekly', 'monthly', 'yearly'], index=0)
            is_alarm_active = st.checkbox("Is Active?", value=True)
            add_alarm_submitted = st.form_submit_button("Add Alarm")

            if add_alarm_submitted:
                if alarm_date and alarm_time:
                    alarm_datetime_str = f"{alarm_date} {alarm_time}"
                    if selected_job and selected_job.get('job_id') and selected_job.get('job_id') != '': # Added check for empty string
                        try:
                            dal.create_alarm(
                                job_id=selected_job['job_id'],
                                pearl_id=st.session_state.pearl_id,
                                alarm_time=alarm_datetime_str,
                                message=alarm_message,
                                recurrence=alarm_recurrence,
                                is_alarm_active=is_alarm_active
                            )
                            st.success("Alarm added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding alarm: {e}")
                    else:
                        st.error("Cannot add alarm: Selected job ID is missing or invalid.")
                else:
                    st.error("Alarm Date and Time are required.")

        # Display existing alarms for the selected job
        st.markdown("#### Existing Alarms")
        try:
            job_alarms = dal.get_all_alarms_for_job(selected_job['job_id'], st.session_state.pearl_id)
            if job_alarms:
                alarms_df = pd.DataFrame([dict(alarm) for alarm in job_alarms])
                st.dataframe(alarms_df)

                # Edit/Delete existing alarms
                st.markdown("##### Edit / Delete Existing Alarms")
                alarm_ids = [alarm['alarm_id'] for alarm in job_alarms]
                selected_alarm_id = st.selectbox("Select an alarm to edit or delete", options=alarm_ids, key=f"select_alarm_{selected_job['job_id']}")

                if selected_alarm_id:
                    selected_alarm = next((alarm for alarm in job_alarms if alarm['alarm_id'] == selected_alarm_id), None)
                    if selected_alarm:
                        with st.form(f"edit_alarm_form_{selected_alarm_id}"):
                            st.write(f"Editing Alarm ID: {selected_alarm_id}")
                            edited_alarm_date = st.date_input("Alarm Date", value=pd.to_datetime(selected_alarm['alarm_time']).date(), key=f"edit_alarm_date_{selected_alarm_id}")
                            edited_alarm_time = st.time_input("Alarm Time", value=pd.to_datetime(selected_alarm['alarm_time']).time(), key=f"edit_alarm_time_{selected_alarm_id}")
                            edited_alarm_message = st.text_area("Message (Optional)", value=selected_alarm['message'], key=f"edit_alarm_message_{selected_alarm_id}")
                            edited_alarm_recurrence = st.selectbox("Recurrence", ['once', 'daily', 'weekly', 'monthly', 'yearly'], index=['once', 'daily', 'weekly', 'monthly', 'yearly'].index(selected_alarm['recurrence']), key=f"edit_alarm_recurrence_{selected_alarm_id}")
                            edited_is_alarm_active = st.checkbox("Is Active?", value=bool(selected_alarm['is_active']), key=f"edit_is_alarm_active_{selected_alarm_id}")

                            col_alarm1, col_alarm2 = st.columns(2)
                            with col_alarm1:
                                update_alarm_submitted = st.form_submit_button("Update Alarm")
                            with col_alarm2:
                                delete_alarm_submitted = st.form_submit_button("Delete Alarm")

                            if update_alarm_submitted:
                                if edited_alarm_date and edited_alarm_time:
                                    edited_alarm_datetime_str = f"{edited_alarm_date} {edited_alarm_time}"
                                    try:
                                        # Assuming an update_alarm method exists in dal
                                        dal.update_alarm(
                                            alarm_id=selected_alarm_id,
                                            alarm_time=edited_alarm_datetime_str,
                                            message=edited_alarm_message,
                                            recurrence=edited_alarm_recurrence,
                                            is_alarm_active=edited_is_alarm_active
                                        )
                                        st.success(f"Alarm {selected_alarm_id} updated successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating alarm: {e}")
                                else:
                                    st.error("Alarm Date and Time are required.")

                            if delete_alarm_submitted:
                                st.warning(f"Deleting alarm {selected_alarm_id}. This action cannot be undone.")
                                try:
                                    dal.delete_alarm(alarm_id=selected_alarm_id, pearl_id=st.session_state.pearl_id)
                                    st.success(f"Alarm {selected_alarm_id} deleted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting alarm: {e}")

        except Exception as e:
            st.error(f"Error loading alarms: {e}")




    # --- Task Management for Selected Job ---
    if selected_job:
        st.subheader(f"Tasks for Job: {selected_job['job_name']}")

        # Form to create a new task
        with st.form(f"new_task_form_{selected_job['job_id']}", clear_on_submit=True):
            st.write("Add New Task")
            task_name = st.text_input("Task Name", max_chars=255, key=f"new_task_name_{selected_job['job_id']}")
            description = st.text_area("Description", key=f"new_task_description_{selected_job['job_id']}")
            status_options = ['pending', 'in_progress', 'completed', 'on_hold', 'cancelled']
            status = st.selectbox("Status", options=status_options, index=0, key=f"new_task_status_{selected_job['job_id']}")
            assigned_to = st.text_input("Assigned To", key=f"new_task_assigned_to_{selected_job['job_id']}")
            due_date = st.date_input("Due Date", key=f"new_task_due_date_{selected_job['job_id']}")

            add_task_submitted = st.form_submit_button("Add Task")

            if add_task_submitted:
                if task_name:
                    try:
                        dal.pearl_client.create_task(
                            job_id=selected_job['job_id'],
                            task_name=task_name,
                            description=description,
                            status=status,
                            assigned_to=assigned_to,
                            due_date=due_date.isoformat() if due_date else None
                        )
                        st.success(f"Task '{task_name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding task: {e}")
                else:
                    st.error("Task Name is required.")

        # Display existing tasks for the selected job
        st.markdown("#### Existing Tasks")
        try:
            job_tasks = dal.pearl_client.get_tasks_by_job_id(selected_job['job_id'])
            if job_tasks:
                tasks_df = pd.DataFrame(job_tasks)
                st.dataframe(tasks_df)

                # Edit/Delete existing tasks
                st.markdown("##### Edit / Delete Existing Tasks")
                task_ids = [task['id'] for task in job_tasks]
                selected_task_id = st.selectbox("Select a task to edit or delete", options=task_ids, format_func=lambda x: f"Task ID: {x} - {next((t['task_name'] for t in job_tasks if t['id'] == x), '')}", key=f"select_task_{selected_job['job_id']}")

                if selected_task_id:
                    selected_task = next((task for task in job_tasks if task['id'] == selected_task_id), None)
                    if selected_task:
                        with st.form(f"edit_task_form_{selected_task_id}"):
                            st.write(f"Editing Task ID: {selected_task_id}")
                            edited_task_name = st.text_input("Task Name", value=selected_task['task_name'], key=f"edit_task_name_{selected_task_id}")
                            edited_description = st.text_area("Description", value=selected_task['description'], key=f"edit_task_description_{selected_task_id}")
                            edited_status = st.selectbox("Status", options=status_options, index=status_options.index(selected_task['status']), key=f"edit_task_status_{selected_task_id}")
                            edited_assigned_to = st.text_input("Assigned To", value=selected_task['assigned_to'], key=f"edit_task_assigned_to_{selected_task_id}")
                            edited_due_date = st.date_input("Due Date", value=pd.to_datetime(selected_task['due_date']) if selected_task['due_date'] else None, key=f"edit_task_due_date_{selected_task_id}")

                            col_task1, col_task2 = st.columns(2)
                            with col_task1:
                                update_task_submitted = st.form_submit_button("Update Task")
                            with col_task2:
                                delete_task_submitted = st.form_submit_button("Delete Task")

                            if update_task_submitted:
                                if edited_task_name:
                                    try:
                                        dal.pearl_client.update_task(
                                            task_id=selected_task_id,
                                            task_name=edited_task_name,
                                            description=edited_description,
                                            status=edited_status,
                                            assigned_to=edited_assigned_to,
                                            due_date=edited_due_date.isoformat() if edited_due_date else None
                                        )
                                        st.success(f"Task '{edited_task_name}' updated successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating task: {e}")
                                else:
                                    st.error("Task Name is required.")

                            if delete_task_submitted:
                                st.warning(f"Are you sure you want to delete task '{selected_task['task_name']}'? This action cannot be undone.")
                                try:
                                    dal.pearl_client.delete_task(selected_task_id)
                                    st.success(f"Task '{selected_task['task_name']}' deleted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting task: {e}")
            else:
                st.info("No tasks found for this job.")
        except Exception as e:
            st.error(f"Error loading tasks for this job: {e}")
    else:
        st.info("Please select a job to manage tasks.")
