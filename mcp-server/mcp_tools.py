# mcp-server/mcp_tools.py
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any

# Import our InventoryClient
from inventory_client import InventoryClient

# Initialize the InventoryClient instance (assuming it runs on default port)
# In a real app, you might get base_url from environment variables
inventory_client = InventoryClient()

# Define Pydantic models for tool input schemas
# These mirror the InventoryUpdateRequest from the Inventory Service's OpenAPI spec
class UpdateInventoryInput(BaseModel):
    item: str = Field(description="The name of the inventory item (e.g., 'tshirts' or 'pants').")
    change: int = Field(description="The integer quantity to add (positive) or remove (negative).")

@tool(args_schema=UpdateInventoryInput)
def update_inventory_tool(item: str, change: int) -> Dict[str, Any]:
    """
    Modifies the count of an item in the inventory.
    Use this tool when the user wants to add, subtract, sell, or purchase items.
    Requires the 'item' name (tshirts or pants) and the integer 'change' amount.
    A positive 'change' adds items, a negative 'change' removes them.
    Example: update_inventory_tool(item='tshirts', change=-3) to sell 3 tshirts.
    """
    print(f"Tool Call: update_inventory_tool(item={item}, change={change})")
    return inventory_client.update_inventory(item=item, change=change)

@tool
def get_inventory_tool() -> Dict[str, int]:
    """
    Retrieves the current inventory count for tshirts and pants.
    Use this tool when the user asks about current stock, how many items are available, or similar queries.
    """
    print("Tool Call: get_inventory_tool()")
    return inventory_client.get_inventory()