# 🎯 Inventory Management + GenAI Interface - Internship Task Solution

This repository presents a solution to the internship task, comprising two interconnected components:

1. **Inventory Web Service** for managing stock of 'tshirts' and 'pants'
2. **MCP (Model Control Plane) Server** that provides a GenAI-powered natural language interface to interact with the Inventory Service

The project is designed to demonstrate proficiency in backend service development, LLM integration, API contract adherence (OpenAPI), and robust error handling.

## ✨ Key Features

- **RESTful Inventory API:** Simple, clear API for inventory management (`GET /inventory`, `POST /inventory`)
- **Natural Language Interface:** Interact with the inventory using plain English queries (e.g., "sell 5 tshirts", "how many pants do I have?")
- **GenAI-Powered Agent:** Utilizes Google's Gemini-Flash model orchestrated by LangChain and LangGraph for intelligent query interpretation and tool execution
- **Robust Error Handling:** Comprehensive error management at both service and agent layers, providing user-friendly feedback
- **OpenAPI-Driven Design:** Adherence to OpenAPI specification for defining the Inventory Service's API contract

## 🛠️ Technologies Used

- **Backend Framework:** FastAPI (Python)
- **AI Frameworks:** LangChain, LangGraph
- **Large Language Model (LLM):** Google Gemini-Flash (`gemini-1.5-flash-latest`)
- **Dependency Management:** Python Virtual Environments, `pip`
- **API Interaction:** `requests` library
- **Data Validation:** Pydantic

## 📁 Project Structure

The repository is organized as follows, aligning with the task's submission requirements:

```
root/
├── inventory-service/           # Contains the Inventory Web Service
│   ├── venv/                    # Python virtual environment (ignored by Git)
│   ├── main.py                  # FastAPI application for Inventory Service
│   ├── requirements.txt         # Direct dependencies for Inventory Service
│   └── requirements-lock.txt    # Exact dependency versions (pip freeze) for reproducibility
├── mcp-server/                  # Contains the Model Control Plane (MCP) Server
│   ├── venv/                    # Python virtual environment (ignored by Git)
│   ├── main.py                  # FastAPI application for MCP Server (includes LLMAgent)
│   ├── inventory_client.py      # HTTP client for Inventory Service
│   ├── mcp_tools.py             # LangChain tool definitions
│   ├── requirements.txt         # Direct dependencies for MCP Server
│   └── requirements-lock.txt    # Exact dependency versions (pip freeze) for reproducibility
├── openapi.yaml                 # OpenAPI Specification for the Inventory Service (static copy)
└── README.md                    # This document
```

## 🚀 Setup and Local Run

Follow these steps to get both services up and running on your local machine.

### Prerequisites

- Python 3.9+ (recommended)
- Git
- `curl` (or Postman/Insomnia for API testing)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Xorinat-internship-task.git
cd Xorinat-internship-task
```

### 2. Set Up Inventory Web Service

```bash
cd inventory-service

# Create and activate a Python virtual environment
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows (Command Prompt):
# venv\Scripts\activate.bat

# On Windows (PowerShell):
# .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the Inventory Service
uvicorn main:app --reload --port 8000
```

The Inventory Service will now be running at http://127.0.0.1:8000. You can access its interactive API documentation (Swagger UI) at http://127.0.0.1:8000/docs.

### 3. Set Up MCP Server

Open a new terminal window and follow these steps:

```bash
cd Xorinat-internship-task/mcp-server

# Create and activate a Python virtual environment
python -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows (Command Prompt):
# venv\Scripts\activate.bat
# On Windows (PowerShell):
# .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### Set Google API Key

The MCP Server requires a Google API Key to access the Gemini model.

1. Obtain a Google API Key with access to the Gemini API (https://ai.google.dev/gemini-api/docs).
2. Create a file named `.env` in the `mcp-server/` directory (at the same level as `main.py`).
3. Add your API key to this file:

```bash
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```

**Important:** The `.env` file is excluded from Git via `.gitignore` for security.

#### Run the MCP Server

**Set Environment Variables**:
   ```bash
   export INVENTORY_SERVICE_URL="http://127.0.0.1:8000"
   export GOOGLE_API_KEY="your-google-api-key"
   ```
   Or create a `.env` file:
   ```env
   INVENTORY_SERVICE_URL=http://127.0.0.1:8000
   GOOGLE_API_KEY=your-google-api-key
   ```
**Note**: The default `INVENTORY_SERVICE_URL` (`http://127.0.0.1:8000`) is for local development. For non-local setups (e.g., Docker, cloud), set `INVENTORY_SERVICE_URL` to the Inventory Service’s host and port (e.g., `http://inventory-service:8000`). Verify the port is not in use by another service. Ensure `GOOGLE_API_KEY` is set for the LLM.

#### Ensure your virtual environment is active and .env file is set up
uvicorn main:app --reload --port 8001
The MCP Server will now be running at http://127.0.0.1:8001 OR INVENTORY_SERVICE_URL. You can access its interactive API documentation (Swagger UI) at http://YOUR_URL/docs.

Ensure both services (Inventory on 8000 and MCP on 8001) are running simultaneously for the MCP Server to function correctly.

## 🧪 API Endpoints and Examples

You can interact with both services using curl (BASH/Linux/macOS syntax shown below, adjust for PowerShell if needed), Postman/Insomnia, or Swagger UI.

### Inventory Web Service (http://127.0.0.1:8000)

This service manages inventory for 'tshirts' (initial: 20) and 'pants' (initial: 15).

- **Get Inventory**:
     ```bash
     curl -X GET "http://127.0.0.1:8000/inventory"
     ```
     Response: `{"tshirts": 20, "pants": 15}`
   - **Update Inventory (Success)**:
     ```bash
     curl -X POST "http://127.0.0.1:8000/inventory" -H "Content-Type: application/json" -d '{"item": "tshirts", "change": 5}'
     ```
     Response: `{"tshirts": 25, "pants": 15}`
   - **Negative Inventory (400)**:
     ```bash
     curl -X POST "http://127.0.0.1:8000/inventory" -H "Content-Type: application/json" -d '{"item": "tshirts", "change": -21}'
     ```
     Response: `{"detail": "Cannot reduce tshirts count below zero. Current: 20, Attempted change: -21"}`
   - **Invalid Item (422)**:
     ```bash
     curl -X POST "http://127.0.0.1:8000/inventory" -H "Content-Type: application/json" -d '{"item": "pantis", "change": 5}'
     ```
     Response: `{"detail": [{"loc": ["body", "item"], "msg": "value is not a valid enumeration member; permitted: 'tshirts', 'pants'", "type": "value_error.enum"}]}`
   - **Large Quantity (if limits enabled)**:
     ```bash
     curl -X POST "http://127.0.0.1:8000/inventory" -H "Content-Type: application/json" -d '{"item": "tshirts", "change": 10001}'
     ```
     Response (if limits enabled): `{"detail": [{"loc": ["body", "change"], "msg": "value must be less than or equal to 10000", "type": "value_error.number.too_large"}]}`



## MCP Server (http://127.0.0.1:8001)

This service converts natural language queries into API calls to the Inventory Service.



**Request Body Sample Test Cases:** `{"query": "I sold 3 t shirts"}`

#### 1. POST /process_query

Accepts a natural language string and returns a GenAI-generated response.

**Request Body Sample Test Cases:** `{"query": "I sold 3 t shirts"}`

- Test query endpoint:
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"add one tshirt"}'
     ```
     Response: `{"response":"Added 1 tshirt. Inventory: 21 tshirts, 15 pants."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"sell 5 T-shirt"}'
     ```
     Response: `{"response":"Sold 5 tshirts. Inventory: 15 tshirts, 15 pants."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"clear all pants"}'
     ```
     Response (assuming 15 pants): `{"response":"Cleared all pants. Inventory: 20 tshirts, 0 pants."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"sell 2.5 tshirts"}'
     ```
     Response: `{"response":"Only whole numbers are supported. Please specify an exact number."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"sell half of pants"}'
     ```
     Response: `{"response":"Please provide an exact number for updates."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"add 20 shirts"}'
     ```
     Response: `{"response":"Shirts is not supported. Valid items: ['tshirts', 'pants']."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"add 5 pantis"}'
     ```
     Response: `{"response":"Pantis is not supported. Valid items: ['tshirts', 'pants']."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"sell 3 tshit"}'
     ```
     Response: `{"response":"Tshits is not supported. Valid items: ['tshirts', 'pants']."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"add 20 pantis and 30 shirts"}'
     ```
     Response: `{"response":"Pantis and shirts are not supported. Valid items: ['tshirts', 'pants']."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"add 5 tshirts and 10 pantis"}'
     ```
     Response: `{"response":"Added 5 tshirts. Pantis is not supported. Inventory: 25 tshirts, 15 pants. Valid items: ['tshirts', 'pants']."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"sell 3 tshirts and 2 hats"}'
     ```
     Response: `{"response":"Sold 3 tshirts. Hats is not supported. Inventory: 17 tshirts, 15 pants. Valid items: ['tshirts', 'pants']."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"add 5"}'
     ```
     Response: `{"response":"Please specify which item(s) to update."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"buy 20000000 tshirts"}'
     ```
     Response: `{"response":"The update failed because the requested change (20000000) exceeds the maximum allowed value of 10000. Please specify a smaller amount."}`

     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" \
     -H "Content-Type: application/json" -d '{"query":"add 5 jackets"}'
     ```
     Response (if `openapi.json` includes `"jackets"`): `{"response":"Added 5 jackets. Inventory: 5 jackets, 20 tshirts, 15 pants."}`
     Response (if `"jackets"` not in `openapi.json`): `{"response":"Jackets is not supported. Valid items: ['tshirts', 'pants']."}`

## 🧠 Design and Approach

This solution focuses on building a clear, modular, and robust system that effectively integrates traditional backend services with GenAI capabilities.

### 1. Inventory Web Service (inventory-service/)

### Design Choices
- **FastAPI**: Chosen for its simplicity, rapid development, automatic OpenAPI schema generation, and async support. The `/openapi.json` endpoint provides the `enum` of valid items, enabling the MCP Server to dynamically fetch `valid_items` for Task 2 (item normalization), reducing manual configuration and ensuring scalability.
- **Pydantic**: Enforces strict validation of item names (via `Literal`) and integer quantities, generating structured 400/422 error responses for the MCP Server’s LLM to interpret, supporting Tasks 1 (quantity processing) and 2.
- **In-Memory Storage**: A dictionary (`inventory_db`) ensures simplicity, as persistent storage isn’t required. It supports fast updates and retrieval for Tasks 3 (multi-item updates) and 4 (inventory summarization). **Limitation**: The in-memory store is expected to initialize with non-negative item counts (e.g., `{"tshirts": 20, "pants": 15}`). Negative counts at initialization are not handled, as the system assumes valid starting quantities. To address this, validation could be added in `inventory_service/main.py` to check for non-negative counts during initialization, raising an error if violated.
- **Inventory Expansion**: To add new items (e.g., “jackets”), update `InventoryUpdateRequest.item` and `inventory_db` in `inventory_service/main.py`. Both the Inventory Service and MCP Server must be restarted to reflect changes, as `valid_items` are fetched from `openapi.json` at MCP Server startup. The rule-based system prompt in `mcp_server/main.py` is designed to handle dynamic inventory updates by incorporating `valid_items`, ensuring seamless processing of new items without prompt modifications.
- **Validation**: The `Literal["tshirts", "pants"]` in `InventoryUpdateRequest` generates an `enum` in `openapi.json`, ensuring only valid items are processed. Business logic prevents negative inventory (400 errors), aligning with Task 1.
- **Error Handling**: Structured 400 (negative inventory) and 422 (validation) errors provide clear feedback to the MCP Server, enabling user-friendly responses (e.g., “Cannot reduce tshirts below zero”).
- **Dynamic Item Support**: The `openapi.json` `enum` allows new items (e.g., `"jackets"`) to be added by updating `InventoryUpdateRequest`, supporting scalability without MCP Server code changes.

### Limitations
- In-memory store resets on restart, and negative item counts at initialization are not handled.
- No authentication, suitable for prototyping.


## 2. MCP (Model Control Plane) Server (mcp-server/)

The MCP Server acts as the intelligent bridge between natural language and the Inventory Service API.

### Design Choices
- **LangChain and LangGraph**: LangChain’s tool-binding enables `gemini-2.0-flash` to process natural language queries, while LangGraph’s stateful workflow handles multi-step tasks (e.g., “clear all pants” requiring `get_inventory_tool` then `update_inventory_tool`), supporting Tasks 1 and 3. The workflow ensures robust tool execution and response formatting.
- **LLM-Driven Processing**: The rule-based system prompt (`MCP_SYSTEM_PROMPT` in `main.py`) defines rules for quantity handling (Task 1), item normalization (Task 2), multi-item processing (Task 3), and inventory summarization (Task 4). The LLM interprets errors, reducing coded logic.
- **InventoryClient**: Uses `requests` in `inventory_client.py` for lightweight HTTP communication with the Inventory Service. The default `base_url` (`http://127.0.0.1:8000`) is for local development, configurable via `INVENTORY_SERVICE_URL` for non-local setups (e.g., Docker, cloud). Structured error responses support LLM interpretation.
- **MCP Tools**: Two LangChain tools (`get_inventory_tool`, `update_inventory_tool`) in `mcp_tools.py` map to Inventory Service endpoints, minimizing complexity. `update_inventory_tool` uses a Pydantic schema to ensure valid inputs, mirroring the Inventory Service’s `InventoryUpdateRequest`. Logging aids debugging.
- **LLMAgent**: Integrates the LLM, tools, and system prompt in `main.py` to process queries. Fetches `valid_items` from `openapi.json` at initialization for dynamic item support (Task 2). The LangGraph workflow handles tool calls and responses, ensuring stateful query processing (e.g., for “clear all pants”).
- **FastAPI**: Provides a RESTful `/process_query` endpoint in `main.py` for natural language queries, with Pydantic for input validation. Handles errors gracefully, supporting robust user interactions.
- **OpenAPI Integration**: Fetches `valid_items` from `openapi.json` at startup, ensuring new items (e.g., `"jackets"`) are supported without code changes. The rule-based prompt dynamically incorporates `valid_items`, enabling effective inventory updates.
- **Error Handling**: Passes 400/422 errors to the LLM for user-friendly responses (e.g., “Pantis is not supported”). Network errors (503) inform users to check the Inventory Service. FastAPI handles endpoint errors (400/500) for robustness.

### Features
- **Compound Queries**: The system supports complex queries (e.g., “add 5 tshirts and 10 pants”, “sell 3 tshirts and 2 hats”) by processing multiple items via separate `update_inventory_tool` calls, combining results and errors (Task 3). The LangGraph workflow in `main.py` ensures sequential tool execution for multi-step queries (e.g., “clear all pants”).
- **Rule-Based Prompt**: The `MCP_SYSTEM_PROMPT` in `main.py` enforces strict rules for quantity handling (e.g., integers only), item normalization (e.g., “T-shirt” → “tshirts”), multi-item processing, and response formatting. This ensures all actions align with the system’s requirements, providing consistent and accurate responses across all four tasks.
- **Dynamic Item Verification**: The `LLMAgent` in `main.py` dynamically parses `openapi.json` at startup to fetch `valid_items`, enabling validation of item names (Task 2). This supports new items (e.g., “jackets”) without modifying the MCP Server code, as the prompt adapts to the updated `valid_items`.

### Limitations
- **In-Memory Store**: Resets on restart and assumes non-negative initial counts, as noted in the Inventory Service section.
- **MCP Server**: Relies on the LLM for query parsing and response formatting, which may introduce variability for edge cases. The `openapi.json` is fetched only at MCP Server startup in `LLMAgent._get_valid_inventory_items`. If the Inventory Service’s schema changes (e.g., new items added), both servers must be restarted to update `valid_items`. This is because the `valid_items` list is cached at initialization to avoid repeated HTTP requests during runtime, ensuring performance but requiring manual restarts for schema updates.
- **InventoryClient**: Minimal validation in `inventory_client.py` shifts responsibility to the Inventory Service and MCP Server, ensuring simplicity but relying on their correctness.
- **MCP Tools**: Limited to two tools in `mcp_tools.py` to cover all operations, relying on the LLM for complex query parsing (e.g., multi-item updates).
- **LLMAgent**: Depends on `GOOGLE_API_KEY` for LLM initialization. Zero temperature ensures deterministic responses but may limit creativity for edge cases.

## Alignment with Tasks
The system addresses four key tasks:
1. **Quantity Processing**: The `MCP_SYSTEM_PROMPT` enforces exact integer quantities, with `update_inventory_tool` handling positive/negative changes. `get_inventory_tool` supports “clear all” queries by fetching counts for negative changes (Task 1).
2. **Item Normalization**: The `LLMAgent` fetches `valid_items` from `openapi.json`, and the system prompt defines normalization rules (e.g., `"tshirt"` → `"tshirts"`, `"pantis"` → `"pantis"`). Invalid items trigger error messages (Task 2).
3. **Multi-Item Handling**: The system prompt and LangGraph workflow support multiple `update_inventory_tool` calls for valid items, with combined error messages for invalid items (Task 3).
4. **Inventory Summarization**: `get_inventory_tool` fetches current counts, and `update_inventory_tool` returns updated counts for HTTP 200 responses, formatted by the LLM (Task 4).
