UPDATE Alarms
SET
    alarm_time = :alarm_time,
    message = :message,
    recurrence = :recurrence,
    start_date = :start_date,
    end_date = :end_date,
    snooze_until = :snooze_until,
    dismissed_at = :dismissed_at,
    is_active = :is_active
WHERE
    alarm_id = :alarm_id AND pearl_id = :pearl_id;