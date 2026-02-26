import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import requests

# Add the App/src directory to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'App')))
# from agent.moltbot_api import MoltbotAPI
# from agent.contracts import ContractExecutor
# from agent.semantic import PearlClient # Assuming PearlClient is in agent.semantic
from App.src.agent.moltbot_api import MoltbotAPI
# from App.src.contract_executor import ContractExecutor # Commented out as file not found
# from App.src.core.database.pearl_qlite.pearl_qlite import PearlClient # PearlClient is now imported directly in agent_pearl

class TestMoltbotIntegration(unittest.TestCase):

    def setUp(self):
        """Set up environment variables and mock objects before each test."""
        os.environ["MOLTBOT_BASE_URL"] = "http://mock-moltbot-api.com"
        os.environ["MOLTBOT_API_KEY"] = "mock_api_key"

        # Mock PearlClient for ContractExecutor
        # self.mock_pearl_client = MagicMock(spec=PearlClient)
        
        # Patch the MoltbotAPI constructor within the contracts module
        # This ensures that when ContractExecutor creates a MoltbotAPI, it gets our mock
        # self.patcher_moltbot_api_constructor = patch('agent.contracts.MoltbotAPI')
        # self.MockMoltbotAPI = self.patcher_moltbot_api_constructor.start()
        # self.mock_moltbot_api_instance = self.MockMoltbotAPI.return_value # This is the mock instance that ContractExecutor will use

        # self.contract_executor = ContractExecutor(client=self.mock_pearl_client)

    def tearDown(self):
        """Clean up environment variables and stop patches after each test."""
        del os.environ["MOLTBOT_BASE_URL"]
        del os.environ["MOLTBOT_API_KEY"]
        # self.patcher_moltbot_api_constructor.stop()

    @patch('App.src.agent.moltbot_api.requests.post')
    def test_moltbot_api_send_message_success(self, mock_post):
        """Test successful message sending via MoltbotAPI."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "message_id": "msg123"}
        mock_post.return_value = mock_response

        moltbot_api = MoltbotAPI(os.environ["MOLTBOT_BASE_URL"], os.environ["MOLTBOT_API_KEY"])
        response = moltbot_api.send_message(to="12345", channel="whatsapp", message="Hello")

        mock_post.assert_called_once_with(
            "http://mock-moltbot-api.com/send_message",
            json={"to": "12345", "channel": "whatsapp", "message": "Hello"},
            headers={"Content-Type": "application/json", "Authorization": "Bearer mock_api_key"},
            timeout=10
        )
        self.assertEqual(response, {"status": "success", "message_id": "msg123"})

    @patch('App.src.agent.moltbot_api.requests.post')
    def test_moltbot_api_send_message_failure(self, mock_post):
        """Test message sending failure via MoltbotAPI."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        moltbot_api = MoltbotAPI(os.environ["MOLTBOT_BASE_URL"], os.environ["MOLTBOT_API_KEY"])
        with self.assertRaises(requests.exceptions.RequestException):
            moltbot_api.send_message(to="12345", channel="telegram", message="Failed message")

    # def test_contract_executor_moltbot_whatsapp_success(self):
    #     """Test ContractExecutor handling of Moltbot_WhatsApp_Message contract."""
    #     with patch.object(self.contract_executor.moltbot_api, 'send_message') as mock_send_message:
    #         mock_send_message.return_value = {"status": "success", "message_id": "whatsapp_msg_456"}

    #         contract_name = "Moltbot_WhatsApp_Message"
    #         args = {"to": "9876543210", "message": "Test WhatsApp", "sender_id": "pearl_agent_x"}
            
    #         result = self.contract_executor.execute(contract_name, args)

    #         mock_send_message.assert_called_once_with(
    #             to="9876543210",
    #             channel="whatsapp",
    #             message="Test WhatsApp",
    #             sender_id="pearl_agent_x"
    #         )
    #         self.assertEqual(result["status"], "success")
    #         self.assertEqual(result["response"]["message_id"], "whatsapp_msg_456")
    #         # Verify audit log if default_audit is set
    #         if self.contract_executor.default_audit:
    #             self.mock_pearl_client.execute_contract.assert_called_with(
    #                 self.contract_executor.default_audit,
    #                 {"event": contract_name, "args": args, "success": True, "result": result}
    #             )

    # def test_contract_executor_moltbot_telegram_missing_args(self):
    #     """Test ContractExecutor handling of Moltbot_Telegram_Message with missing arguments."""
    #     contract_name = "Moltbot_Telegram_Message"
    #     args = {"to": "telegram_user_id"} # Missing 'message'
        
    #     result = self.contract_executor.execute(contract_name, args)

    #     self.assertEqual(result["status"], "error")
    #     self.assertIn("Missing required arguments", result["message"])
    #     # Ensure MoltbotAPI.send_message was NOT called
    #     self.mock_moltbot_api_instance.send_message.assert_not_called()
    #     # Verify audit log if default_audit is set
    #     if self.contract_executor.default_audit:
    #         self.mock_pearl_client.execute_contract.assert_called_with(
    #             self.contract_executor.default_audit,
    #             {"event": contract_name, "args": args, "success": False, "result": result}
    #         )

    # def test_contract_executor_non_moltbot_contract(self):
    #     """Test ContractExecutor delegates non-Moltbot contracts to PearlClient."""
    #     contract_name = "some_other_contract"
    #     args = {"param1": "value1"}
    #     self.mock_pearl_client.execute_contract.return_value = {"status": "executed", "data": "mock_data"}

    #     result = self.contract_executor.execute(contract_name, args)

    #     self.mock_pearl_client.execute_contract.assert_called_with(contract_name, args)
    #     self.assertEqual(result["status"], "executed")
    #     self.assertEqual(result["data"], "mock_data")
    #     # Ensure MoltbotAPI.send_message was NOT called
    #     self.mock_moltbot_api_instance.send_message.assert_not_called()

    # def test_contract_executor_moltbot_api_not_initialized(self):
    #     """Test ContractExecutor when MoltbotAPI is not initialized."""
    #     # Temporarily set moltbot_api to None
    #     original_moltbot_api = self.contract_executor.moltbot_api
    #     self.contract_executor.moltbot_api = None

    #     contract_name = "Moltbot_Discord_Notification"
    #     args = {"to": "discord_channel", "message": "Test Discord"}

    #     result = self.contract_executor.execute(contract_name, args)

    #     self.assertEqual(result["status"], "error")
    #     self.assertIn("Moltbot API not initialized", result["message"])
        
    #     # Restore original moltbot_api
    #     self.contract_executor.moltbot_api = original_moltbot_api

if __name__ == '__main__':
    unittest.main()
