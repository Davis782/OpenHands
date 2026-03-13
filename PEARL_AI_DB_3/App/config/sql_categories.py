from dataclasses import dataclass, field
from typing import List

@dataclass
class SqlCategory:
    """
    Represents a category of SQL queries, mapping to a directory in the App/sql/ structure.
    """
    name: str          # User-friendly name, e.g., "Job Management"
    directory: str     # The actual subdirectory name, e.g., "jobs"
    description: str   # A brief description of what this category covers
    sql_files: frozenset[tuple[str, str]] = field(default_factory=frozenset) # frozenset of (name, path) tuples


SQL_CATEGORIES: List[SqlCategory] = [
    SqlCategory(name="Common Utilities", directory="common", description="General purpose SQL queries that are not specific to any module.", sql_files=frozenset([
        ("get_server_info", "common/get_server_info.sql"),
        ("create_common_table", "common/create_pearls_table.sql"),
        ("create_crdt_log_table", "common/create_crdt_log_table.sql"),
        ("create_crdt_counter_table", "common/create_crdt_counter_table.sql"),
    ])),
    SqlCategory(name="Job Management", directory="jobs", description="Queries related to job creation, tracking, and updates.", sql_files=frozenset([
        ("get_all_jobs", "jobs/get_all_jobs.sql"),
        ("create_jobs_table", "jobs/create_jobs_table.sql"),
        ("create_tasks_table", "jobs/create_tasks_table.sql"),
        ("get_tasks_for_job", "jobs/get_tasks_for_job.sql"),
        ("create_task", "jobs/create_task.sql"),
        ("update_task", "jobs/update_task.sql"),
        ("delete_task", "jobs/delete_task.sql"),
    ])),
    SqlCategory(name="Contact Management", directory="contacts", description="Queries for managing clients, subcontractors, and suppliers.", sql_files=frozenset([
        ("get_all_contacts", "contacts/get_all_contacts.sql"),
        ("create_contacts_table", "contacts/create_contacts_table.sql"),
        ("update_contact", "contacts/update_contact.sql"),
        ("delete_contact", "contacts/delete_contact.sql"),
    ])),
    SqlCategory(name="Accounting", directory="accounting", description="Financial transaction and reporting queries.", sql_files=frozenset([
        ("create_accounting_table", "accounting/create_accounting_table.sql"),
        ("insert_accounting_entry", "accounting/insert_accounting_entry.sql"),
        ("get_all_accounting_entries", "accounting/get_all_accounting_entries.sql"),
        ("update_accounting_entry", "accounting/update_accounting_entry.sql"),
        ("delete_accounting_entry", "accounting/delete_accounting_entry.sql"),
    ])),
    SqlCategory(name="Reports", directory="reports", description="Complex queries for generating various business reports.", sql_files=frozenset([
        ("create_reports_table", "reports/create_reports_table.sql"),
        ("jobs_by_budget_range", "reports/jobs_by_budget_range.sql"),
    ])),
    SqlCategory(name="Groups", directory="groups", description="Queries for managing PEARL ID groups and their members.", sql_files=frozenset([
        ("create_groups_table", "groups/create_pearl_id_groups_table.sql"),
        ("create_group_members_table", "groups/create_group_members_table.sql"),
    ])),
    SqlCategory(name="Alarms", directory="alarms", description="Queries for managing alarms associated with jobs.", sql_files=frozenset([
        ("create_alarms_table", "alarms/create_alarms_table.sql"),
        ("insert_alarm", "alarms/insert_alarm.sql"),
        ("get_alarm_by_id", "alarms/get_alarm_by_id.sql"),
        ("get_all_alarms_for_job", "alarms/get_all_alarms_for_job.sql"),
        ("update_alarm", "alarms/update_alarm.sql"),
        ("delete_alarm", "alarms/delete_alarm.sql"),
    ])),

]
