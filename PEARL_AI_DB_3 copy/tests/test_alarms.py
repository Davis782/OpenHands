import pytest
import sqlite3
import os
from datetime import datetime, timedelta
from App.src.core.database.data_access import DataAccess
from App.src.core.database.pearl_qlite.pearl_qlite import PearlClient
import tempfile

# Mock PearlClient for testing purposes
class MockPearlClient:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

@pytest.fixture
def dal():
    # Create a temporary file for the SQLite database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db_file:
        db_path = tmp_db_file.name

    mock_pearl_client = MockPearlClient(db_path)
    data_access = DataAccess(db_path, "", mock_pearl_client) # sql_dir not needed for raw sql

    # Manually create the alarms table for testing
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE alarms (
            alarm_id TEXT PRIMARY KEY,
            pearl_id TEXT NOT NULL,
            job_id TEXT,
            task_id TEXT,
            alarm_message TEXT NOT NULL,
            alarm_time TEXT NOT NULL,
            recurrence TEXT NOT NULL, -- 'once', 'daily', 'weekly', 'monthly'
            start_date TEXT NOT NULL,
            end_date TEXT,
            is_active INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

    yield data_access

    # Clean up the temporary database file after tests
    os.remove(db_path)

def test_get_due_alarms_once(dal):
    # Insert a 'once' alarm
    alarm_time = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    dal._execute_raw_sql(
        "INSERT INTO alarms (alarm_id, pearl_id, job_id, task_id, alarm_message, alarm_time, recurrence, start_date, end_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("alarm1", "pearl1", "job1", "task1", "Once alarm", alarm_time, "once", "2023-01-01", None, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_alarms = dal.get_due_alarms(current_time)
    assert len(due_alarms) == 1
    assert due_alarms[0]["alarm_id"] == "alarm1"

def test_get_due_alarms_daily(dal):
    # Insert a 'daily' alarm set for 10 minutes ago, starting yesterday, ending tomorrow
    alarm_time_str = (datetime.now() - timedelta(minutes=10)).strftime("%H:%M:%S")
    alarm_datetime_str = (datetime.now().replace(hour=int(alarm_time_str[:2]), minute=int(alarm_time_str[3:5]), second=int(alarm_time_str[6:]))).strftime("%Y-%m-%d %H:%M:%S")

    dal._execute_raw_sql(
        "INSERT INTO alarms (alarm_id, pearl_id, job_id, task_id, alarm_message, alarm_time, recurrence, start_date, end_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("alarm2", "pearl2", "job2", "task2", "Daily alarm", alarm_datetime_str, "daily", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    # Current time is after the alarm time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_alarms = dal.get_due_alarms(current_time)
    assert len(due_alarms) == 1
    assert due_alarms[0]["alarm_id"] == "alarm2"

    # Current time is before the alarm time
    current_time_before = (datetime.now() - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")
    due_alarms_before = dal.get_due_alarms(current_time_before)
    assert len(due_alarms_before) == 0

def test_get_due_alarms_weekly(dal):
    # Insert a 'weekly' alarm for today's day of the week, 10 minutes ago
    alarm_time_dt = datetime.now() - timedelta(minutes=10)
    alarm_time_str = alarm_time_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    dal._execute_raw_sql(
        "INSERT INTO alarms (alarm_id, pearl_id, job_id, task_id, alarm_message, alarm_time, recurrence, start_date, end_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("alarm3", "pearl3", "job3", "task3", "Weekly alarm", alarm_time_str, "weekly", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"), (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"), 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    # Current time is after the alarm time on the correct day
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_alarms = dal.get_due_alarms(current_time)
    assert len(due_alarms) == 1
    assert due_alarms[0]["alarm_id"] == "alarm3"

    # Current time is on a different day of the week
    current_time_diff_day = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    due_alarms_diff_day = dal.get_due_alarms(current_time_diff_day)
    assert len(due_alarms_diff_day) == 0

def test_get_due_alarms_monthly(dal):
    # Insert a 'monthly' alarm for today's day of the month, 10 minutes ago
    alarm_time_dt = datetime.now() - timedelta(minutes=10)
    alarm_time_str = alarm_time_dt.strftime("%Y-%m-%d %H:%M:%S")

    dal._execute_raw_sql(
        "INSERT INTO alarms (alarm_id, pearl_id, job_id, task_id, alarm_message, alarm_time, recurrence, start_date, end_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("alarm4", "pearl4", "job4", "task4", "Monthly alarm", alarm_time_str, "monthly", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"), (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"), 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    # Current time is after the alarm time on the correct day of the month
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_alarms = dal.get_due_alarms(current_time)
    assert len(due_alarms) == 1
    assert due_alarms[0]["alarm_id"] == "alarm4"

    # Current time is on a different day of the month
    current_time_diff_day = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    due_alarms_diff_day = dal.get_due_alarms(current_time_diff_day)
    assert len(due_alarms_diff_day) == 0

def test_get_due_alarms_inactive(dal):
    # Insert an inactive alarm
    alarm_time = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    dal._execute_raw_sql(
        "INSERT INTO alarms (alarm_id, pearl_id, job_id, task_id, alarm_message, alarm_time, recurrence, start_date, end_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("alarm5", "pearl5", "job5", "task5", "Inactive alarm", alarm_time, "once", "2023-01-01", None, 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_alarms = dal.get_due_alarms(current_time)
    assert len(due_alarms) == 0

def test_snooze_alarm(dal):
    # Insert an alarm
    initial_alarm_time = datetime.now()
    initial_alarm_time_str = initial_alarm_time.strftime("%Y-%m-%d %H:%M:%S")
    dal._execute_raw_sql(
        "INSERT INTO alarms (alarm_id, pearl_id, job_id, task_id, alarm_message, alarm_time, recurrence, start_date, end_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("alarm10", "pearl10", "job10", "task10", "Snooze alarm", initial_alarm_time_str, "once", "2023-01-01", None, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    # Snooze the alarm for 15 minutes
    snooze_duration = 15
    dal.snooze_alarm("alarm10", snooze_duration)

    # Fetch the updated alarm and check its time
    updated_alarm = dal._fetch_raw_sql_one("SELECT alarm_time FROM alarms WHERE alarm_id = :alarm_id;", {"alarm_id": "alarm10"})
    updated_alarm_time = datetime.strptime(updated_alarm["alarm_time"], "%Y-%m-%d %H:%M:%S")

    expected_alarm_time = initial_alarm_time + timedelta(minutes=snooze_duration)
    # Allow for a small time difference due to execution time
    assert abs((updated_alarm_time - expected_alarm_time).total_seconds()) < 5

    # Check that it's no longer due immediately
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_alarms = dal.get_due_alarms(current_time)
    assert "alarm10" not in {a["alarm_id"] for a in due_alarms}

def test_dismiss_alarm(dal):
    # Insert an alarm
    alarm_time = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    dal._execute_raw_sql(
        "INSERT INTO alarms (alarm_id, pearl_id, job_id, task_id, alarm_message, alarm_time, recurrence, start_date, end_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("alarm9", "pearl9", "job9", "task9", "Dismissible alarm", alarm_time, "once", "2023-01-01", None, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    # Dismiss the alarm
    dal.dismiss_alarm("alarm9")

    # Check if it's no longer active
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_alarms = dal.get_due_alarms(current_time)
    assert len(due_alarms) == 0

def test_get_due_alarms_outside_date_range(dal):
    # Insert an alarm that is active but outside its date range
    alarm_time = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    dal._execute_raw_sql(
        "INSERT INTO alarms (alarm_id, pearl_id, job_id, task_id, alarm_message, alarm_time, recurrence, start_date, end_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("alarm6", "pearl6", "job6", "task6", "Outside date range alarm", alarm_time, "once", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"), 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_alarms = dal.get_due_alarms(current_time)
    assert len(due_alarms) == 0

def test_get_due_alarms_multiple_due(dal):
    # Insert multiple alarms that should be due
    alarm_time_once = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    alarm_time_daily = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    alarm_datetime_daily_str = (datetime.now().replace(hour=int(alarm_time_daily[11:13]), minute=int(alarm_time_daily[14:16]), second=int(alarm_time_daily[17:19]))).strftime("%Y-%m-%d %H:%M:%S")

    dal._execute_raw_sql(
        "INSERT INTO alarms (alarm_id, pearl_id, job_id, task_id, alarm_message, alarm_time, recurrence, start_date, end_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("alarm7", "pearl7", "job7", "task7", "Multiple alarm 1", alarm_time_once, "once", "2023-01-01", None, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    dal._execute_raw_sql(
        "INSERT INTO alarms (alarm_id, pearl_id, job_id, task_id, alarm_message, alarm_time, recurrence, start_date, end_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("alarm8", "pearl8", "job8", "task8", "Multiple alarm 2", alarm_datetime_daily_str, "daily", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_alarms = dal.get_due_alarms(current_time)
    assert len(due_alarms) == 2
    alarm_ids = {a["alarm_id"] for a in due_alarms}
    assert "alarm7" in alarm_ids
    assert "alarm8" in alarm_ids

def test_get_due_alarms_no_alarms(dal):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_alarms = dal.get_due_alarms(current_time)
    assert len(due_alarms) == 0
