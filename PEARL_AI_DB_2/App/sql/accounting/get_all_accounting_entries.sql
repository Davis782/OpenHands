SELECT id, pearl_id, transaction_date, description, amount, type
FROM Accounting
WHERE pearl_id = :pearl_id;