# inventory-service/main.py
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict

# Initialize FastAPI app
app = FastAPI(
    title="Inventory Service",
    description="A simple web service to manage inventory for tshirts and pants.",
    version="1.0.0",
)

# In-memory data store
inventory_db: Dict[str, int] = {
    "tshirts": 20,
    "pants": 15
}

# Pydantic model for GET /inventory response
class InventoryResponse(BaseModel):
    tshirts: int
    pants: int

# Pydantic model for POST /inventory request
class InventoryUpdateRequest(BaseModel):
    item: str # "tshirts" or "pants"
    change: int # Positive for adding, negative for removing

# Pydantic model for custom error responses
class CustomErrorResponse(BaseModel):
    detail: str = Field(..., example="Item 'hats' not found. Only 'tshirts' and 'pants' are supported.")


@app.get("/inventory", response_model=InventoryResponse)
async def get_inventory():
    """
    Returns the current inventory count for tshirts and pants.
    """
    return inventory_db

@app.post("/inventory", response_model=InventoryResponse,
          responses={
              status.HTTP_400_BAD_REQUEST: { # Using status.HTTP_400_BAD_REQUEST for clarity
                  "model": CustomErrorResponse,
                  "description": "Bad Request: Invalid item name or attempt to reduce inventory below zero."
              }
          })
async def update_inventory(request: InventoryUpdateRequest):
    """
    Modifies the count of an item in the inventory.

    - **item**: The name of the item ("tshirts" or "pants").
    - **change**: The quantity to add (positive) or remove (negative).
    """
    item_name = request.item.lower() # Normalize to lowercase

    # Validate item name
    if item_name not in inventory_db:
        raise HTTPException(status_code=400, detail=f"Item '{request.item}' not found. Only 'tshirts' and 'pants' are supported.")

    current_count = inventory_db[item_name]
    new_count = current_count + request.change

    # Prevent negative inventory
    if new_count < 0:
        raise HTTPException(status_code=400, detail=f"Cannot reduce {item_name} count below zero. Current: {current_count}, Attempted change: {request.change}")

    inventory_db[item_name] = new_count
    return inventory_db