SELECT
  job_id,
  job_name,
  description,
  budget,
  start_date,
  end_date,
  pearl_id
FROM Jobs
WHERE pearl_id = :pearl_id;