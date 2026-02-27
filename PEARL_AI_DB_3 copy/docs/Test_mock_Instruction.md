# CLI Testing with Mock Inputs

This document outlines how to run automated tests for the Command Line Interface (CLI) using mock inputs. This method allows you to simulate user interactions with the CLI without manual input, making it ideal for regression testing and verifying specific user flows.

## How it Works

The `App/src/cli/main_cli_menu.py` script is designed to accept a sequence of mock inputs when run in `test_mode`. This sequence simulates the user typing commands and pressing Enter.

## Running Tests

To run a test, you need to:

1.  **Define Your Mock Input Sequence:** Open `App/src/cli/main_cli_menu.py` and locate the `if __name__ == "__main__":` block. Inside this block, you will find a `mock_inputs_sequence` list. Modify this list to represent the series of inputs you want to provide to the CLI.

    Each string in the `mock_inputs_sequence` list corresponds to a single line of user input (followed by an Enter key press). Empty strings (`""`) can be used to simulate pressing Enter without typing any text (e.g., to continue after a `pause()` call).

    **Example `mock_inputs_sequence` for unlocking a vault:**

    ```python
    # App/src/cli/main_cli_menu.py

    # ... (other code) ...

    if __name__ == "__main__":
        mock_inputs_sequence = [
            "1", # Main Menu: Select/Change Database
            "1", # Select the first database in the list (e.g., PEARL_AI_DB.sqlite)
            "",  # Press ENTER to continue... (after database selection)
            "2", # Main Menu: Vault Management
            "1", # Vault Management: Unlock Vault
            "1", # Select Unlock Method: Individual Passwords
            "your_vault_door_password", # Input for Vault Door password
            "your_identity_password",   # Input for Identity password
            "your_metadata_password",   # Input for Metadata password
            "",  # Press ENTER to continue... (after load_vault result)
            "4", # Select Unlock Method: Back to Vault Management
            "",  # Press ENTER to continue... (after menu_vault_management loop)
            "7"  # Main Menu: Exit
        ]
        main_menu(test_mode=True, mock_inputs=mock_inputs_sequence)
    ```

2.  **Execute the Test:** Once your `mock_inputs_sequence` is defined, open your terminal in the project's root directory (`PEARL_AI_DB_2`) and run the following command:

    ```bash
    python -m App.src.cli.main_cli_menu
    ```

    The CLI will execute automatically, consuming the inputs from `mock_inputs_sequence`.

## Important Notes

*   **`test_mode=True`:** This flag, passed to `main_menu`, activates the mock input system and suppresses actual `input()` calls, replacing them with values from `mock_inputs_sequence`.
*   **`_test_context`:** The `cli_utils.py` module contains a `_test_context` object that manages the mock input queue. When `test_mode` is active, `builtins.input` is temporarily replaced with `_test_context.mock_input`.
*   **Output Verification:** After running the test, you can review the terminal output to verify that the CLI behaved as expected. Look for specific messages, menu transitions, and results of operations.
*   **Temporary Changes:** Remember to revert any changes made to `mock_inputs_sequence` in `main_cli_menu.py` after you are done with your testing, or ensure your version control ignores these changes.

By following these steps, you can effectively automate testing of the CLI's various functionalities.