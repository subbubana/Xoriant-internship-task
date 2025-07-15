# mcp-server/inventory_client.py
import requests
from typing import Dict, Any

class InventoryClient:
    """
    A client to interact with the Inventory Service API.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url

    def get_inventory(self) -> Dict[str, int]:
        """
        Retrieves the current inventory count.
        """
        try:
            response = requests.get(f"{self.base_url}/inventory")
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            # Log the error for debugging
            print(f"Error connecting to inventory service (GET /inventory): {e}")
            # For simplicity, re-raise or return a structured error for agent to handle
            raise ConnectionError(f"Failed to connect to Inventory Service: {e}")

    def update_inventory(self, item: str, change: int) -> Dict[str, Any]:
        """
        Updates the inventory for a specific item.

        Args:
            item (str): The name of the item ("tshirts" or "pants").
            change (int): The quantity to add (positive) or remove (negative).

        Returns:
            Dict[str, Any]: The updated inventory state or an error message.
        """
        payload = {"item": item, "change": change}
        try:
            response = requests.post(f"{self.base_url}/inventory", json=payload)
            response.raise_for_status() # Raise an HTTPError for 4xx or 5xx responses

            return response.json() # Successful update returns updated inventory

        except requests.exceptions.HTTPError as e:
            # This block handles 4xx or 5xx responses specifically
            error_response = {}
            try:
                error_json = response.json()
                error_response["status_code"] = response.status_code
                error_response["detail"] = error_json.get("detail", "An unexpected error occurred.")

                
                if response.status_code == 400:
                    # Our custom 400 errors from inventory_service
                    error_response["translated_message"] = error_response["detail"]

            except requests.exceptions.JSONDecodeError:
                error_response["status_code"] = response.status_code
                error_response["detail"] = response.text
                error_response["translated_message"] = "Received an unparseable error response from the inventory service."

            print(f"Error from inventory service ({response.status_code}): {error_response.get('translated_message', error_response.get('detail'))}")
            return {"error": error_response} # Return structured error for agent

        except requests.exceptions.RequestException as e:
            # Handles network errors, DNS issues, etc.
            print(f"Network error connecting to inventory service (POST /inventory): {e}")
            return {"error": {"status_code": 503, "detail": str(e), "translated_message": "Could not connect to the inventory service. Please ensure it is running."}}