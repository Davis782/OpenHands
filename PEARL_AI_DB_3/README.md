python -m App.src.cli.main_cli_menu
python run_app.py
streamlit run App/src/ui/main_app.py   
pearl_b558f2f3f3da
vault_door_password:test1;identity_password:test2;metadata_password:test3
pearl_81d7fc51a5af

streamlit cache clear
 

python App/src/main.py --test test_inputs.txt


# PEARL AI Database

This repository houses the PEARL AI Database system, a sophisticated platform designed for intelligent data management, secure identity handling, and robust conflict-free replication.

## Current System Functionality & Architecture

The PEARL AI system has evolved significantly, focusing on modularity, advanced data management, and robust security.

### Modular Architecture
The project now adheres to a clean `App/src` structure, separating core logic, database interfaces, and UI components for improved maintainability and scalability. `App/src/ui/main_app.py` serves as the primary entry point for the interactive Streamlit application, while `App/src/main.py` handles command-line operations.

### Core Components
*   **`PearlClient`**: Acts as the primary interface for database interactions, built upon SQLite.
*   **`AgentPearl`**: The orchestration layer that manages the flow between the user interface (Streamlit/CLI), `PearlClient`, and other specialized modules.

### Key Features

*   **Streamlit Web Interface**: An interactive web application (`App/src/ui/main_app.py`) provides a user-friendly interface for vault management, PEARL ID creation and selection, and other core functionalities. The sidebar allows for easy selection of the active PEARL ID for database operations.

*   **CRDT Implementation**: The system incorporates Conflict-free Replicated Data Types (CRDTs), specifically a PN-Counter and append-only logs, to enable distributed logging and counters, ensuring conflict-free state synchronization. This is managed through `crdt_log` and `crdt_counter` tables within `PearlClient`.

*   **Identity Geometry & Security**:
    *   **Relational Seeding**: A mechanism for deterministic ID generation, where unique identifiers are mapped to 3D unit vectors. This is implemented in `App/src/core/seedtools/seedtools.py`, with `pearl_qlite.py` updated to store `x`, `y`, and `z` coordinates.
    *   **Private Identity Vault**: A secure vault (`App/src/core/security/vault.py`) that uses Fernet symmetric encryption to protect sensitive public IDs. Access to the vault is password-protected and integrated into `AgentPearl`.
    *   **Limited Access Key Store**: Manages keys for limited access entries, allowing for granular control over data access. This is implemented in `App/src/core/security/limited_access_key_store.py`.
    *   **Master Key Seed Functionality**: Vault unlocking and limited access entry creation can now be performed using a single Master PEARL ID Seed, streamlining the authentication process.
    *   **Cryptographic Pipeline Fixes**: Addressed critical issues in the cryptographic pipeline, including ensuring Argon2id outputs raw 32-byte keys for AES-256-GCM, correcting seed validation logic (from `if not self._seed` to `if self._seed is None`), and fixing `AttributeError` in metadata retrieval.
    *   **Authenticated Vault Management**: Critical operations such as overwriting or deleting a vault now require the existing vault's password, adding a crucial layer of security against unauthorized data manipulation.

*   **Multi-Format Export**: Users can export query results into various formats, including JSON, CSV, TXT, and Pickle, facilitated by the `export_query_results` function in `PearlClient` and `AgentPearl`.

*   **Automated Testing & Output Capture**: A robust `--test` mode allows for automated testing by mocking user inputs from a specified file (e.g., `test_inputs.txt`). All console output during these test runs is redirected and captured into unique timestamped files (e.g., `test_run_capture_*.txt`) for thorough verification. This is achieved through `builtins.input` override and `sys.stdout`/`sys.stderr` reassignment in `main.py`.

*   **CLI Enhancements**: The command-line interface (`App/src/cli/menus.py`) has been significantly refactored for modularity and intuitiveness. Input prompts now include descriptive examples to guide users, and `clear()` logic has been adjusted to maintain menu visibility, especially during automated testing.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone [repository_url]
    cd PEARL_AI_DB_2
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    ./venv/Scripts/activate  # On Windows
    source venv/bin/activate # On macOS/Linux
    pip install -r requirements.txt
    ```

3.  **Run the Streamlit web application:**
    ```bash
    streamlit run App/src/ui/main_app.py
    ```

4.  **Run the command-line application:**
    ```bash
    python App/src/main.py
    ```

5.  **Run in Test Mode (with automated inputs and output capture):**
    ```bash
    python App/src/main.py --test test_inputs.txt
    ```
    This will read inputs from `test_inputs.txt` and write all console output to a file named `test_run_capture_YYYYMMDD_HHMMSS.txt` in the project root.

## Project Structure

```
.
├── App/
│   ├── src/
│   │   ├── agent_pearl/
│   │   │   ├── __init__.py
│   │   │   └── agent_pearl.py
│   │   ├── cli/
│   │   │   ├── __init__.py
│   │   │   └── menus.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── limited_access_key_store.py
│   │   │   │   └── vault.py
│   │   │   └── seedtools/
│   │   │       ├── __init__.py
│   │   │       └── seedtools.py
│   │   ├── pearl_qlite/
│   │   │   ├── __init__.py
│   │   │   └── pearl_qlite.py
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── main_app.py
│   │   │   ├── pages/
│   │   │   └── streamlit_cache_utils.py
│   │   └── main.py
├── databases/
├── deleted_files/
├── docs/
├── tests/
│   ├── NEXT_STEPS/
│   │   ├── Security_PRD.md
│   │   └── WHITEPAPER_Relational_Seeding_in_PEARL_Identity_Geometry.md
│   └── test_crdt.py
├── .env
├── requirements.txt
├── test_inputs.txt
└── README.md
```

## Refactoring Suggestions

To further enhance the application's organization and maintainability, consider the following refactoring opportunities:

1.  **Centralized Configuration Management**:
    *   **Description**: Implement a dedicated `config.py` module or a configuration class to manage all application settings.
    *   **Benefit**: Provides a single source of truth for configurations, simplifies management of defaults and overrides, and improves clarity.

2.  **Improved Error Handling and Logging**:
    *   **Description**: Adopt a consistent and robust error handling strategy using Python's `logging` module. Replace direct `print` statements to `sys.__stderr__` with structured logging.
    *   **Benefit**: Centralized error logging, easier debugging, and better control over log levels and output destinations. Consider defining custom exception types for specific error scenarios.



4.  **Enhanced Test Utilities**:
    *   **Description**: While the current `--test` mode is functional for end-to-end testing, integrating a dedicated testing framework like `pytest` would provide a more structured approach for unit and integration tests.
    *   **Benefit**: Offers better test discovery, streamlined setup/teardown procedures, comprehensive reporting, and a more robust testing ecosystem.

