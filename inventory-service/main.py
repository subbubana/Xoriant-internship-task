from fastapi import FastAPI, HTTPException, status #To create the web service and HTTPException/status for error handling.
from pydantic import BaseModel, Field #To define and validate request/response models.
from typing import Dict, List, Any # To define precise data types (e.g., Dict for inventory, Any for error details).
from enum import Enum #To define the enum for the item names.

# Initialize FastAPI app with metadata to generate a clear OpenAPI schema.
# The schema (accessible at /openapi.json) defines valid items and request/response structures,
# enabling the MCP Server to fetch valid_items dynamically and validate user queries.
app = FastAPI(
    title="Inventory Service",
    description="A simple web service to manage inventory for tshirts and pants.",
    version="1.0.0",
)

# Define the enum for the item names("tshirts" and "pants"). This can be extended to include more items in the future.
class InventoryItem(str, Enum): # Inherit from str to ensure string values in JSON
    TSHIRTS = "tshirts"
    PANTS = "pants"

# In-memory dictionary to store inventory counts, initialized with default values.
# Using a dictionary simplifies state management for this prototype, as persistent storage isn't required.
# The MCP Server relies on this to retrieve current inventory and apply updates via POST requests.
inventory_db: Dict[str, int] = {
    "tshirts": 20,
    "pants": 15
}

# Pydantic model for GET /inventory response -- Not using this static model, to achieve a sacleable solution.
# class InventoryResponse(BaseModel):
#     tshirts: int
#     pants: int

# Pydantic model for POST /inventory request with strict validation
class InventoryUpdateRequest(BaseModel):
    # Use the Enum directly for type validation -- supports only the items in the enum.
    item: InventoryItem = Field(description="The name of the item ('tshirts' or 'pants').")
    change: int = Field(
        description="The quantity to add (positive) or remove (negative).",
        # ge=-10000, le=10000  # Commented out to avoid hardcoding limits, 
        # allowing flexibility for future changes.
    )

    # No case normalization validator needed here, as Enum members are exact.
    # The agent (MCP) will handle normalization before sending to this service.

# Pydantic model for 400 error responses, standardizing error messages.
# Used when inventory updates would result in negative counts, providing clear feedback
# to the MCP Server for LLM interpretation (e.g., "Cannot reduce tshirts count below zero.").
class HTTPErrorResponse(BaseModel):
    detail: str = Field(example="Cannot reduce tshirts count below zero.")


# Pydantic models for 422 validation errors, aligning with FastAPI's default error format.
# These provide structured error details (e.g., invalid item names) to the MCP Server,
# enabling user-friendly error messages for invalid queries (e.g., "pantis" not in enum).
class ValidationError(BaseModel):
    loc: List[Any] = Field(description="Location of the error (e.g., ['body', 'field_name'])")
    msg: str = Field(description="Error message")
    type: str = Field(description="Error type (e.g., 'value_error.missing')")

class HTTPValidationError(BaseModel):
    detail: List[ValidationError] = Field(
        example=[{"loc": ["body", "item"], "msg": "field required", "type": "value_error.missing"}],
        description="List of validation errors"
    )

@app.get("/inventory", response_model=Dict[str, int]) # Using generic response_model to support future items.
async def get_inventory():
     # Returns the current inventory counts for all items in inventory_db.
     # The endpoint supports Task 4 in mcp-server/main.py (inventory summarization) by providing current counts
     # to the MCP Server, which uses get_inventory_tool for queries like "clear all pants"
     # or to summarize inventory after successful updates.
     # The response_model ensures the response matches the InventoryResponse schema.
    """Returns the current inventory count for all items."""
    return inventory_db

@app.post(
    "/inventory",
    response_model=Dict[str, int],
    responses={
        status.HTTP_200_OK: {"description": "Successful Response", "model": Dict[str, int]},
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPErrorResponse,
            "description": "Bad Request: Attempt to reduce inventory below zero."
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": HTTPValidationError,
            "description": "Validation Error: Invalid request payload format or value."
        }
    }
)
async def update_inventory(request: InventoryUpdateRequest):
    # Pydantic validates 'item' (must be in enum) and 'change' (must be an integer).
    # Business logic prevents negative inventory, returning a 400 error if violated.
    # The endpoint supports Task 1 (quantity processing) and Task 3 (multi-item updates)
    # by allowing the MCP Server to apply changes via update_inventory_tool and receive
    # updated inventory counts or error messages for LLM interpretation.
    """
    Updates the inventory count for the specified item based on the change value.
    """
    # Calculate new inventory count based on the requested change.
    # This supports positive (add/buy) and negative (sell/remove) updates as per Task 1.
    # This also handled new items added to the enum in the future.
    new_count = inventory_db.get(request.item.value, 0) + request.change
    
    # Check for negative inventory to enforce business rules.
    # A 400 error is raised with a descriptive message, which the MCP Server uses
    # to generate user-friendly responses (e.g., for "sell 30 tshirts" when count is 20).
    if new_count < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce {request.item} count below zero. \
                  Current: {inventory_db[request.item]}, Attempted change: {request.change}"
        )
    
    # Update the inventory count in the in-memory database.
    # This ensures the MCP Server receives the updated state for Task 4 (inventory summarization).
    inventory_db[request.item] = new_count
    print(inventory_db)
    return inventory_db