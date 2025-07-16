import logging #To capture tool execution details for debugging.
from langchain_core.tools import tool #To define functions that the LLM can call.
from pydantic import BaseModel, Field #To define input schemas for tools.
from typing import Dict, Any #To define precise return types (e.g., Dict[str, int] for inventory).
from inventory_client import InventoryClient #To interact with the Inventory Service’s API.

#Set up logging with INFO level to capture tool call details.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Instantiate InventoryClient to connect to the Inventory Service.
# Uses INVENTORY_SERVICE_URL environment variable or defaults to http://127.0.0.1:8000
inventory_client = InventoryClient()
# The client handles HTTP requests for get_inventory and update_inventory, enabling tools to perform API calls without duplicating logic.


# Define Pydantic model for update_inventory_tool’s input schema, mirroring Inventory Service’s InventoryUpdateRequest.
# Ensures item is a string and change is an integer, supporting Task 1 (quantity processing) by enforcing exact quantities.
# The MCP Server validates item against valid_items (from openapi.json), 
# ensuring only valid items (e.g., “tshirts”, “pants”) are passed.
class UpdateInventoryInput(BaseModel):
    item: str = Field(description="The name of the inventory item (e.g., 'tshirts' or 'pants').")
    change: int = Field(description="The integer quantity to add (positive) or remove (negative).")

@tool(args_schema=UpdateInventoryInput)
def update_inventory_tool(item: str, change: int) -> Dict[str, Any]:
    """
    Modifies the count of an item in the inventory.
    Use this tool when the user wants to add, subtract, sell, or purchase items.
    Requires the 'item' name and the integer 'change' amount.
    A positive 'change' adds items, a negative 'change' removes them.
    Example: update_inventory_tool(item='tshirts', change=-3) to sell 3 tshirts.
    Returns raw API responses, including 422 validation errors (e.g., out-of-bounds change),
    which the MCP agent's LLM interprets for user-friendly messages.
    """
    # Log tool call details for debugging, capturing item and change to trace user requests and API interactions.
    logger.info(f"Tool Call: update_inventory_tool(item={item}, change={change})")
    # Delegate to InventoryClient to send POST /inventory request, returning updated inventory or error response.
    # The LLM interprets results (e.g., {"tshirts": 25, "pants": 15} or {"error": {...}}) for user-friendly responses.
    return inventory_client.update_inventory(item=item, change=change)


@tool
def get_inventory_tool() -> Dict[str, int]:
    """
    Retrieves the current inventory count for items in the inventory.
    Use this tool when the user asks about current stock, how many items are available, or similar queries.
    """
    # Log tool call for debugging, ensuring traceability of inventory retrieval requests.
    logger.info("Tool Call: get_inventory_tool()")
    # Delegate to InventoryClient to send GET /inventory request, returning current inventory (e.g., {"tshirts": 20, "pants": 15}).
    # The LLM uses this for summarization or to compute changes for complex queries.
    return inventory_client.get_inventory()