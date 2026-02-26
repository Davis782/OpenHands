UPDATE Contacts
SET
    first_name = :first_name,
    last_name = :last_name,
    email = :email,
    phone = :phone,
    city = :city
WHERE
    contact_id = :contact_id AND pearl_id = :pearl_id;