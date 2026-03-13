## Revert Information

- **Commit:** FEAT: Allow .txt file uploads in Streamlit reports page
- **Date:** 2026-03-13
- **Hash:** <new_hash_here>
- **Description:**
  - Modified `st.file_uploader` in `App/src/ui/pages/reports.py` to accept both "csv" and "txt" file types.
  - Added logic to `render_csv_import_page` to read `.txt` files using `pd.read_csv` with `sep=','` (assuming comma-separated for now).

- **Commit:** Fix: Resolve all test failures and ensure proper in-memory database handling for CRDT tests.
- **Date:** 2026-03-13
- **Hash:** fb6d7efe8
- **Description:**
  - Resolved `test_snooze_alarm` failure in `test_alarms.py` by correcting the assertion to check `snooze_until` instead of `alarm_time`.
  - Resolved `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file` in `test_crdt.py` by:
    - Modifying `PearlClient.__init__` to correctly handle `":memory:"` as an in-memory database, preventing it from being combined with a file path.
    - Modifying `PearlClient._ensure_db_and_tables` to skip loading SQL files from disk when using an in-memory database, and instead manually creating the `crdt_log` and `crdt_counter` tables.
    - Patching `App.src.agent_pearl.agent_pearl.AgentPearl._initialize_text_to_sql` in `test_crdt.py` to bypass `ai_text_to_sql`'s problematic `SQLiteConnector` initialization during testing.
  - Fixed `IndentationError` in `test_alarms.py` by removing an incorrect line continuation character.

- **Commit:** FEAT: Implement comprehensive SQL Query Builder features and UI enhancements, and update PRD for voting system
- **Date:** 2026-03-13
- **Hash:** e96c65797fea64ac119d2ec2aa3e7022ef8b08e9
- **Description:**
  - Implemented comprehensive DDL, DQL, DML, TCL, Utility, and Advanced Pattern features in the Streamlit SQL Query Builder.
  - Enhanced UI with dynamic pre-filling for various query types (e.g., CREATE VIEW, Subquery, UNION, FTS MATCH).
  - Added contextual instructional bubbles (using `st.expander`) for complex SQL clauses (WHERE, JOIN, GROUP BY, HAVING, ORDER BY, LIMIT, UPSERT, PRAGMA, Advanced Queries) to guide users.
  - Fixed `IndentationError` in `query_builder_page.py`.
  - Fixed `TypeError: 'NoneType' object is not iterable` for non-SELECT queries by modifying `PearlClient.execute_query` to return empty lists for non-result-set queries.
  - Fixed `SyntaxError: expected 'except' or 'finally' block` in `render_savepoint_query_builder`.
  - Updated `PRD_Voting_Pearl_ID.md` to reflect a simplified, integration-focused architecture for a secure anonymous public voting system.

- **Commit:** FEAT: Implement alarm and task editing/deletion, fix form submission errors
- **Date:** 2026-02-23
- **Hash:** c54c6e7
- **Description:**
  - Implemented alarm editing and deletion functionality.
  - Implemented task editing and deletion functionality.
  - Fixed "Binding 1 has no name" error for alarm deletion by aligning SQL parameters.
  - Fixed `st.button() can't be used in an st.form()` errors for both job and task deletion.

- **Commit:** FEAT: Implement CLI vault unlock methods
- **Date:** 2026-02-23
- **Hash:** a214536
- **Description:**
  - Implemented a menu in the CLI for selecting different vault unlock methods (Individual Passwords, Master Key Seed, Limited Access Credentials).
  - Modified the `_load_existing_vault_flow` function in `App/src/cli/cli_utils.py` to present these options and call the corresponding `AgentPearl` method.

- **Commit:** Implement Drill-down Selection and Dynamic Filter UX
- **Date:** 2026-02-12
- **Description:**
  - Implemented drill-down selection for WHERE clause values in the Streamlit Query Builder, allowing users to select from existing distinct column values when the count is <= 50.
  - Replaced the 'Number of WHERE conditions' input with 'Add Condition' and 'Remove Last Condition' buttons for a more intuitive user experience.
  - Enhanced float precision handling for numeric inputs in the WHERE clause by using a BETWEEN clause with a configurable tolerance.
  - Fixed `StreamlitJSNumberBoundsError` by ensuring proper default values and formatting for `st.number_input`.
- **Commit:** Milestone: Vault unlock and basic PEARL ID handling are functional. Still investigating empty PEARL ID dropdown.
- **Date:** 2026-02-19
- **Hash:** bf5915b
- **Description:**
  - Refactored the "Create Limited Access Entry" UI to use a single "Master PEARL ID Seed" input.
  - Fixed fundamental logic flaws in `LimitedAccessKeyStore` interaction.
  - Resolved persistent `NOT NULL constraint failed` errors by adding a sidebar widget for "Active PEARL ID".
  - Fixed various Python errors including `UnboundLocalError`, `UnhashableParamError`, `ImportError`, and `AttributeError`.
  - Recovered `agent_pearl.py` from file corruption caused by faulty tool use.
  - Added missing `get_master_pearl_id` methods to `AgentPearl` and `Vault` classes.
  - Added missing `_initialize_limited_access_key_store` method to `AgentPearl`.
  - Corrected `LimitedAccessKeyStore`'s `__init__` method to accept `vault_path`.
  - The vault unlock process is now functional, but the "PEARL ID's" dropdown in the sidebar remains empty.
