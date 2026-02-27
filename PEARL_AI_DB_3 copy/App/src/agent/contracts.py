import os
from .semantic import PearlClient
from .moltbot_api import MoltbotAPI

class ContractExecutor:
    def __init__(self, client: PearlClient, default_audit: str | None = None):
        self.client = client
        self.default_audit = default_audit

        # Initialize MoltbotAPI client
        moltbot_base_url = os.getenv("MOLTBOT_BASE_URL")
        moltbot_api_key = os.getenv("MOLTBOT_API_KEY")

        if moltbot_base_url and moltbot_api_key:
            self.moltbot_api = MoltbotAPI(moltbot_base_url, moltbot_api_key)
        else:
            self.moltbot_api = None
            print("Warning: Moltbot API credentials not found. Moltbot contracts will not function.")

    def execute(self, name: str, args: dict):
        """
        Executes a contract based on its name and arguments.
        If the contract is Moltbot-related, it uses the MoltbotAPI.
        Otherwise, it delegates to the PearlClient's execute_contract.
        """
        moltbot_contract_prefix = "Moltbot_"

        if name.startswith(moltbot_contract_prefix):
            if not self.moltbot_api:
                return {"status": "error", "message": "Moltbot API not initialized. Cannot send message."}
            
            # Extract channel from contract name, e.g., "Moltbot_WhatsApp_Message" -> "whatsapp"
            channel_part = name[len(moltbot_contract_prefix):].lower()
            channel = channel_part.split('_')[0] # Takes "whatsapp" from "whatsapp_message"

            # Validate required arguments for Moltbot messages
            required_args = ["to", "message"]
            if not all(arg in args for arg in required_args):
                return {"status": "error", "message": f"Missing required arguments for {name}. Expected: {', '.join(required_args)}"}

            try:
                moltbot_response = self.moltbot_api.send_message(
                    to=args["to"],
                    channel=channel,
                    message=args["message"],
                    sender_id=args.get("sender_id")
                )
                result = {"status": "success", "response": moltbot_response}
            except Exception as e:
                result = {"status": "error", "message": str(e)}
        elif name == "rtm_create_task":
            # Mock logic for RTM scheduling contract
            print(f"[MOCK] Executing RTM_CREATE_TASK with args: {args}")
            result = {"status": "success", "message": "RTM task created successfully (mock)", "task_id": "mock_rtm_123"}
        elif name == "audit_log_transaction":
            # Mock logic for Blockchain audit contract
            print(f"[MOCK] Executing AUDIT_LOG_TRANSACTION with args: {args}")
            result = {"status": "success", "message": "Audit transaction logged successfully (mock)", "audit_id": "mock_audit_456"}
        elif name == "csv_import":
            # Mock logic for CSV import contract
            print(f"[MOCK] Executing CSV_IMPORT with args: {args}")
            result = {"status": "success", "message": "CSV import initiated successfully (mock)", "import_id": "mock_csv_789"}
        else:
            # Existing logic for other contracts
            result = self.client.execute_contract(name, args)
        
        if self.default_audit:
            audit_args = {
                "event": name,
                "args": args,
                "success": result.get("status") == "success",
                "result": result # Include the full result in the audit log
            }
            self.client.execute_contract(self.default_audit, audit_args)
        return result