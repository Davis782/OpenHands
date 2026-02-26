# Testing Plan for csv_importer.py (PEARL_ID and Autoincrement Logic)

## Overall Goal:
Verify that the updated `import_or_update_table_from_csv` function correctly handles `PEARL_ID` and `autoincrement` ID creation based on table type and user input.

## Pre-requisites (to be done by the Agent after reboot):

1.  **Create `products.csv`**:
    *   **Content**:
        ```csv
        product_name,price,category
        Laptop,1200.00,Electronics
        Mouse,25.50,Electronics
        Keyboard,75.00,Electronics
        Monitor,300.00,Electronics
        ```
    *   **Location**: `data/products.csv` (assuming file access issues are resolved)

2.  **Create `customers.csv`**:
    *   **Content**:
        ```csv
        customer_name,email,city
        Alice,alice@example.com,New York
        Bob,bob@example.com,Los Angeles
        Charlie,charlie@example.com,Chicago
        ```
    *   **Location**: `data/customers.csv` (assuming file access issues are resolved)

3.  **Ensure `transactions.csv` exists**: This file should already be present from previous interactions.

## Testing Steps (to be executed by the Agent after reboot):

**For each test, the Agent will need to:**
*   Run `python PEARL_AI_DB/admin_tools/PEARL_Admin.py`
*   Select option `1` for "Semantic Memory Tools".
*   Select option `2` for "Import or Update table from CSV/TXT".
*   Provide the specified file path and table name.
*   Respond to any prompts as indicated.
*   Verify the outcome by querying the database.

---

### Test 1: Transactions Table (Automatic PEARL_ID)

*   **Action**: Import `transactions.csv` into the `transactions` table.
    *   **File Path**: `data/transactions.csv`
    *   **Table Name**: `transactions`
    *   **Prompt Response**: (No prompt expected for 'transactions' table regarding PEARL_ID)

*   **Expected Outcome**:
    *   The `transactions` table should be created (if it doesn't exist) with a `pearl_id TEXT PRIMARY KEY` column.
    *   Data from `transactions.csv` should be imported, and each row should have a deterministically generated `pearl_id`.

*   **Verification**:
    *   Query the `transactions` table to check for the `pearl_id` column.
    *   Display a few rows to confirm `pearl_id` values are populated.

---

### Test 2: Opt-in PEARL_ID for a new table

*   **Action**: Import `products.csv` into a new table named `Products`.
    *   **File Path**: `data/products.csv`
    *   **Table Name**: `Products`
    *   **Prompt Response**: When asked "Do you want to add a 'pearl_id' column to it? (y/n):", respond with `y`.

*   **Expected Outcome**:
    *   The `Products` table should be created with a `pearl_id TEXT PRIMARY KEY` column.
    *   Data from `products.csv` should be imported, and each row should have a deterministically generated `pearl_id`.

*   **Verification**:
    *   Query the `Products` table to check for the `pearl_id` column.
    *   Display a few rows to confirm `pearl_id` values are populated.

---

### Test 3: Autoincrement ID for a new table

*   **Action**: Import `customers.csv` into a new table named `Customers`.
    *   **File Path**: `data/customers.csv`
    *   **Table Name**: `Customers`
    *   **Prompt Response**: When asked "Do you want to add a 'pearl_id' column to it? (y/n):", respond with `n`.

*   **Expected Outcome**:
    *   The `Customers` table should be created with an `id INTEGER PRIMARY KEY AUTOINCREMENT` column.
    *   Data from `customers.csv` should be imported, and each row should have an `autoincrement` `id`.

*   **Verification**:
    *   Query the `Customers` table to check for the `id` column.
    *   Display a few rows to confirm `id` values are populated and incrementing.