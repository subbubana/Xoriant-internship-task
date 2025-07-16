import requests #To communicate with the Inventory Service.
import os #To access environment variables (e.g., INVENTORY_SERVICE_URL).
import json #To parse Inventory Service responses and handle non-JSON errors.
from typing import Dict, Any #To define precise return types (e.g., Dict[str, int] for inventory).

class InventoryClient:
    """
    A client to interact with the Inventory Service API, enabling the MCP Server to fetch and update inventory.
    Used by get_inventory_tool and update_inventory_tool to support all four tasks: quantity processing (Task 1),
    item validation (Task 2, indirectly via openapi.json), multi-item updates (Task 3),
    and inventory summarization (Task 4).
    """
    def __init__(self, base_url: str = os.getenv("INVENTORY_SERVICE_URL", "http://127.0.0.1:8000")):
        """
        Initialize the client with the Inventory Service base URL.

        Args:
            base_url (str): The base URL of the Inventory Service (default from environment variable or localhost).
        
        """
        # The base_url is configurable via environment variable to support different deployments,
        # ensuring the MCP Server can connect to the Inventory Service reliably.
        self.base_url = base_url

    def _build_error_response(self, status_code: int, detail: Any, translated_message: str = None) -> Dict[str, Any]:
        # This method standardizes error responses for the LLM to interpret (e.g., 400 for negative inventory,
        # 422 for invalid items), supporting user-friendly error messages in Tasks 2 and 3 (e.g., "Pantis is not supported").
        # Logging aids debugging while translated_message provides context for the LLM.
        """
        Build a structured error response for the MCP agent to pass to the LLM.

        Args:
            status_code (int): HTTP status code from the Inventory Service or client error.
            detail: Raw error details (string, dict, or list) from the response.
            translated_message (str, optional): User-friendly message for the LLM to refine.

        Returns:
            Dict[str, Any]: Structured error response with status_code, detail, and optional translated_message.
        """
        error = {"status_code": status_code, "detail": detail}
        if translated_message:
            error["translated_message"] = translated_message
        
        # Log the full error for debugging, ensuring developers can trace issues while the LLM uses the translated message.
        print(f"Error from inventory service ({status_code}): {translated_message or detail}")
        return {"error": error}

    def get_inventory(self) -> Dict[str, int]:
        # This method supports Task 4 (inventory summarization) by providing current counts for the MCP Server
        # to include in responses (e.g., after "add 5 tshirts"). It’s used by get_inventory_tool for queries like
        # "clear all pants" to fetch the current count before setting change to its negative (Task 1).
        """
        Retrieves the current inventory count from the Inventory Service.

        Returns:
            Dict[str, int]: Current inventory state (e.g., {"tshirts": 20, "pants": 15}) or an error response.
        """
        try:
            response = requests.get(f"{self.base_url}/inventory")
            response.raise_for_status()
            # Return JSON response directly, which matches InventoryResponse schema (e.g., {"tshirts": 20, "pants": 15}).
            # This ensures the MCP Server receives consistent inventory data for summarization.
            return response.json()
        except requests.exceptions.RequestException as e:
            return self._build_error_response(
                503,
                str(e),
                "Could not connect to the Inventory Service. Please ensure it is running."
            )

    def update_inventory(self, item: str, change: int) -> Dict[str, Any]:
        # This method supports Tasks 1 (quantity processing) and 3 (multi-item updates) by sending validated
        # item names and integer changes to the Inventory Service. The MCP Server ensures item names match
        # the openapi.json enum (Task 2), and this method handles the HTTP request and error responses for LLM interpretation.
        """
        Updates the inventory for a specific item via the Inventory Service.

        Args:
            item (str): The name of the item (e.g., "tshirts", "pants"), validated by the MCP Server against valid_items.
            change (int): The quantity to add (positive) or remove (negative), per Task 1.

        Returns:
            Dict[str, Any]: Updated inventory state or an error response.
        """
        

        # Construct payload for POST /inventory, relying on MCP Server for item and change validation.
        # This minimizes client-side logic, as Pydantic in the Inventory Service enforces strict validation.
        payload = {"item": item, "change": change}
        try:
            response = requests.post(f"{self.base_url}/inventory", json=payload)
            response.raise_for_status()
            # Return updated inventory on success (HTTP 200), supporting Task 4 (inventory summarization)
            return response.json()

        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors (e.g., 400 for negative inventory, 422 for invalid items).
            error_status_code = response.status_code
            error_detail = None
            translated_message = None

            try:
                error_json = response.json()
                error_detail = error_json.get("detail", response.text)

                if error_status_code == 400:
                     # Handle business logic errors (e.g., negative inventory) with the Inventory Service’s message.
                    # The LLM uses this to generate user-friendly responses (e.g., "Cannot reduce tshirts below zero").
                    translated_message = error_detail
                elif error_status_code == 422:
                    # Handle validation errors (e.g., invalid item names) with a generic hint.
                    # The raw detail (list of dicts) is passed to the LLM for interpretation, supporting Task 2.
                    translated_message = f"API Validation Error: {error_detail}"
                else:
                    # Handle other HTTP errors with a generic message, passing raw details for LLM flexibility.
                    translated_message = f"API Error ({error_status_code}): {error_detail}"

            except json.JSONDecodeError:
               # Handle non-JSON responses (e.g., server errors) with a fallback message.
                error_detail = response.text
                translated_message = f"Received an unparseable error response from the Inventory Service ({error_status_code})."
            
            return self._build_error_response(
                error_status_code,
                error_detail, # Pass the raw detail for the LLM to interpret
                translated_message # Pass the generic hint for the LLM
            )

        except requests.exceptions.RequestException as e:
            # Handle network errors (e.g., connection issues) with a 503 error.
            # The structured response allows the LLM to inform the user to check the Inventory Service
            return self._build_error_response(
                503,
                str(e),
                "Could not connect to the Inventory Service. Please ensure it is running."
            )