import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MoltbotAPI:
    """
    A utility class for interacting with the Moltbot outbound messaging API.
    """
    def __init__(self, base_url: str, api_key: str):
        """
        Initializes the MoltbotAPI client.

        Args:
            base_url (str): The base URL of the Moltbot API.
            api_key (str): The API key for authentication with Moltbot.
        """
        if not base_url:
            raise ValueError("Moltbot API base URL cannot be empty.")
        if not api_key:
            raise ValueError("Moltbot API key cannot be empty.")

        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" # Assuming Bearer token authentication
        }
        logging.info(f"MoltbotAPI initialized with base URL: {self.base_url}")

    def send_message(self, to: str, channel: str, message: str, sender_id: str = None) -> dict:
        """
        Sends an outbound message via the Moltbot API.

        Args:
            to (str): The recipient identifier (e.g., phone number, user ID).
            channel (str): The messaging channel (e.g., "whatsapp", "telegram", "discord").
            message (str): The content of the message to send.
            sender_id (str, optional): An optional PEARL agent ID. Defaults to None.

        Returns:
            dict: The JSON response from the Moltbot API.
        
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        endpoint = f"{self.base_url}/send_message" # Assuming a /send_message endpoint
        payload = {
            "to": to,
            "channel": channel,
            "message": message,
        }
        if sender_id:
            payload["sender_id"] = sender_id

        logging.info(f"Attempting to send message to {to} via {channel}.")
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            logging.info(f"Message sent successfully to {to} via {channel}. Response: {response.status_code}")
            return response.json()
        except requests.exceptions.Timeout:
            logging.error(f"Moltbot API request timed out when sending to {to} via {channel}.")
            raise
        except requests.exceptions.ConnectionError:
            logging.error(f"Moltbot API connection error when sending to {to} via {channel}. Check network and base URL.")
            raise
        except requests.exceptions.HTTPError as e:
            logging.error(f"Moltbot API HTTP error when sending to {to} via {channel}: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logging.error(f"An unexpected error occurred during Moltbot API request: {e}")
            raise

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    # In a real scenario, these would come from environment variables or a config file
    MOLTBOT_BASE_URL = os.getenv("MOLTBOT_BASE_URL", "http://localhost:8000") 
    MOLTBOT_API_KEY = os.getenv("MOLTBOT_API_KEY", "your_moltbot_api_key")

    if MOLTBOT_API_KEY == "your_moltbot_api_key":
        logging.warning("Using default Moltbot API key. Please set MOLTBOT_API_KEY environment variable for production.")

    try:
        moltbot_client = MoltbotAPI(MOLTBOT_BASE_URL, MOLTBOT_API_KEY)
        
        # Example: Send a WhatsApp message
        # response_whatsapp = moltbot_client.send_message(
        #     to="1234567890", 
        #     channel="whatsapp", 
        #     message="Hello from PEARL via Moltbot WhatsApp!",
        #     sender_id="pearl_agent_001"
        # )
        # print(f"WhatsApp Send Response: {response_whatsapp}")

        # Example: Send a Telegram message
        # response_telegram = moltbot_client.send_message(
        # #     to="telegram_user_id", 
        # #     channel="telegram", 
        # #     message="Hello from PEARL via Moltbot Telegram!",
        # # )
        # # print(f"Telegram Send Response: {response_telegram}")

    except ValueError as ve:
        logging.error(f"Configuration Error: {ve}")
    except requests.exceptions.RequestException as re:
        logging.error(f"Moltbot API Error: {re}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
