UPDATE Tasks
SET
    task_name = :task_name,
    description = :description,
    due_date = :due_date,
    status = :status,
    assigned_to = :assigned_to
WHERE
    task_id = :task_id AND pearl_id = :pearl_id;