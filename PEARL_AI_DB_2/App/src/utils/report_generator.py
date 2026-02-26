
import datetime
import os
import json

def generate_vault_report(
    vault_name: str,
    password: str,
    metadata: dict,
    report_dir: str = "reports"
) -> str:
    """
    Generates a comprehensive report for a newly created vault.

    The report includes the vault name, master password, and any associated metadata.
    It is saved as a JSON file in the specified report directory.

    Args:
        vault_name (str): The name or identifier of the vault.
        password (str): The master password for the vault.
        metadata (dict): The metadata associated with the vault.
        report_dir (str): The directory where the report file will be saved.
                          Defaults to 'reports'.

    Returns:
        str: The absolute path to the generated report file.
    """
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"vault_report_{vault_name}_{timestamp}.json"
    report_path = os.path.join(report_dir, report_filename)

    report_content = {
        "vault_name": vault_name,
        "master_password": password,
        "metadata": metadata,
        "creation_timestamp": datetime.datetime.now().isoformat()
    }

    try:
        with open(report_path, "w") as f:
            json.dump(report_content, f, indent=4)
        print(f"Vault report generated successfully at: {os.path.abspath(report_path)}")
        return os.path.abspath(report_path)
    except IOError as e:
        print(f"Error generating vault report to {os.path.abspath(report_path)}: {e}")
        return ""
