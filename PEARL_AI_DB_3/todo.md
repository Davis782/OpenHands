# To-Do List

## Current Task: Debugging 'Folder Structure Report' Export to Database

**Problem:** The "Folder Structure Report" export to the database is failing with the error: `Error binding parameter 3: type 'dict' is not supported`.

**Current Status:**
Debug `print()` statements have been added to `App\src\ui\pages\reports.py` within the `_export_dataframe_to_db` function, just before the `df.to_sql` call. These statements are intended to output the DataFrame's content and its data types to the terminal where the Streamlit application is running.

**Next Steps:**
1.  **User Action Required:** Run the Streamlit application (`python -m streamlit run App\src\ui\main_app.py`).
2.  **User Action Required:** Navigate to the "Reports" page, select "Folder Structure Report", and click the "Export Folder Structure Report to DB" button.
3.  **User Action Required:** Provide the output from the terminal where the Streamlit application is running. This output should include:
    *   "DataFrame content before to_sql:"
    *   The DataFrame's content.
    *   "DataFrame dtypes before to_sql:"
    *   The data types of each column in the DataFrame.

**Goal:** Analyze the provided terminal output to identify which specific column in the DataFrame is still of type `dict` (or an unsupported object type) and then apply the necessary serialization fix (e.g., `json.dumps()`) to that column before exporting to SQLite.