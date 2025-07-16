# Import FastAPI for creating the web service and HTTPException/status for error handling.
# These enable the Inventory Service to expose RESTful endpoints (/inventory) and return 
# standardized HTTP responses, which the MCP Server uses to fetch inventory data and update item counts.
from fastapi import FastAPI, HTTPException, status

# Import Pydantic's BaseModel and Field for defining and validating request/response models.
# Pydantic ensures strict type checking and validation (e.g., item names, integer quantities),
# which supports the MCP Server's need for reliable data and error messages for invalid inputs.
from pydantic import BaseModel, Field


# Import typing utilities to define precise data types (e.g., Dict for inventory, Literal for item names).
# This ensures type safety and clear schema definition for the OpenAPI spec, which the MCP Server uses
# to dynamically fetch valid item names (e.g., ["tshirts", "pants"]).
from typing import Dict, Literal, List, Any


# Initialize FastAPI app with metadata to generate a clear OpenAPI schema.
# The schema (accessible at /openapi.json) defines valid items and request/response structures,
# enabling the MCP Server to fetch valid_items dynamically and validate user queries.
app = FastAPI(
    title="Inventory Service",
    description="A simple web service to manage inventory for tshirts and pants.",
    version="1.0.0",
)

# In-memory dictionary to store inventory counts, initialized with default values.
# Using a dictionary simplifies state management for this prototype, as persistent storage isn't required.
# The MCP Server relies on this to retrieve current inventory and apply updates via POST requests.
inventory_db: Dict[str, int] = {
    "tshirts": 20,
    "pants": 15
}

# Pydantic model for GET /inventory response
class InventoryResponse(BaseModel):
    tshirts: int
    pants: int

# Pydantic model for GET /inventory response, defining the structure of inventory data.
# Explicitly lists tshirts and pants to match initial requirements, ensuring the MCP Server
# receives a consistent JSON response (e.g., {"tshirts": 20, "pants": 15}) for inventory summaries.
class InventoryUpdateRequest(BaseModel):
    item: Literal["tshirts", "pants"] = Field(description="The name of the item in the inventory. Must be exact; MCP agent handles case normalization.")
    change: int = Field(
        description="The quantity to add (positive) or remove (negative).",
        # ge=-10000, le=10000 # Commented out to avoid hardcoding limits, allowing flexibility for future changes.
        # The MCP Server handles large quantity errors via LLM interpretation of 400/422 responses.
    )


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


@app.get("/inventory", response_model=InventoryResponse)
async def get_inventory():
    # Returns the current inventory counts for all items in inventory_db.
    # The endpoint supports Task 4 in mcp-server/main.py (inventory summarization) by providing current counts
    # to the MCP Server, which uses get_inventory_tool for queries like "clear all pants"
    # or to summarize inventory after successful updates.
    # The response_model ensures the response matches the InventoryResponse schema.
    """Returns the current inventory count for all the items in inventory."""
    return inventory_db

@app.post(
    "/inventory",
    response_model=InventoryResponse,
    responses={
        status.HTTP_200_OK: {"description": "Successful Response", "model": InventoryResponse},
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
    new_count = inventory_db[request.item] + request.change
    
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
    return inventory_db