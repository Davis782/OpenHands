UPDATE Accounting
SET transaction_date = :transaction_date,
    description = :description,
    amount = :amount,
    type = :type
WHERE id = :id AND pearl_id = :pearl_id;