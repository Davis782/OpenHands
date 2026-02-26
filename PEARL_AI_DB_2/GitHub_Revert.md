## Revert Information

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
