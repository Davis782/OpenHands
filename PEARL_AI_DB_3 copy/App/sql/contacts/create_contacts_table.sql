
CREATE TABLE IF NOT EXISTS Contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    country TEXT,
    pearl_id TEXT NOT NULL,
    FOREIGN KEY (pearl_id) REFERENCES Pearls(pearl_id)
);
