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

# Ensure your virtual environment is active and .env file is set up
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
```


### MCP Server (http://127.0.0.1:8001)

This service converts natural language queries into API calls to the Inventory Service.

#### 1. POST /process_query

Accepts a natural language string and returns a GenAI-generated response.

**Request Body Sample Test Cases:** `{"query": "I sold 3 t shirts"}`

- Test query endpoint:
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"add one tshirt"}'
     ```
     Response: `{"response":"Added 1 tshirt. Inventory: 21 tshirts, 15 pants."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"sell 5 T-shirt"}'
     ```
     Response: `{"response":"Sold 5 tshirts. Inventory: 15 tshirts, 15 pants."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"clear all pants"}'
     ```
     Response (assuming 15 pants): `{"response":"Cleared all pants. Inventory: 20 tshirts, 0 pants."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"sell 2.5 tshirts"}'
     ```
     Response: `{"response":"Only whole numbers are supported. Please specify an exact number."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"sell half of pants"}'
     ```
     Response: `{"response":"Please provide an exact number for updates."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"add 20 shirts"}'
     ```
     Response: `{"response":"Shirts is not supported. Valid items: ['tshirts', 'pants']."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"add 5 pantis"}'
     ```
     Response: `{"response":"Pantis is not supported. Valid items: ['tshirts', 'pants']."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"sell 3 tshit"}'
     ```
     Response: `{"response":"Tshits is not supported. Valid items: ['tshirts', 'pants']."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"add 20 pantis and 30 shirts"}'
     ```
     Response: `{"response":"Pantis and shirts are not supported. Valid items: ['tshirts', 'pants']."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"add 5 tshirts and 10 pantis"}'
     ```
     Response: `{"response":"Added 5 tshirts. Pantis is not supported. Inventory: 25 tshirts, 15 pants. Valid items: ['tshirts', 'pants']."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"sell 3 tshirts and 2 hats"}'
     ```
     Response: `{"response":"Sold 3 tshirts. Hats is not supported. Inventory: 17 tshirts, 15 pants. Valid items: ['tshirts', 'pants']."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"add 5"}'
     ```
     Response: `{"response":"Please specify which item(s) to update."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"buy 20000000 tshirts"}'
     ```
     Response: `{"response":"The update failed because the requested change (20000000) exceeds the maximum allowed value of 10000. Please specify a smaller amount."}`
     ```bash
     curl -X POST "http://localhost:8001/process_query" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query":"add 5 jackets"}'
     ```
     Response (if `openapi.json` includes `"jackets"`): `{"response":"Added 5 jackets. Inventory: 5 jackets, 20 tshirts, 15 pants."}`
     Response (if `"jackets"` not in `openapi.json`): `{"response":"Jackets is not supported. Valid items: ['tshirts', 'pants']."}`
```
## 🧠 Design and Approach

This solution focuses on building a clear, modular, and robust system that effectively integrates traditional backend services with GenAI capabilities.

### 1. Inventory Web Service (inventory-service/)

#### Clarity and Simplicity:

- **Choice of FastAPI:** FastAPI was chosen for its rapid development capabilities, excellent performance, and automatic generation of OpenAPI documentation. This allowed for quick setup of a clear RESTful API.

- **In-Memory Data Store:** An in-memory dictionary (inventory_db) was used as per the task requirements, prioritizing simplicity and focusing on core API logic rather than database complexities.

#### Correctness and Error Handling:

- **Pydantic for Validation:** Pydantic models (InventoryUpdateRequest, InventoryResponse) ensure strict validation of incoming request bodies and outgoing responses, guaranteeing data integrity.

- **Business Logic Validation (400 Bad Request):** The service explicitly raises HTTPException with 400 Bad Request for business rule violations, such as attempting to update a non-existent item (e.g., 'hats') or reducing inventory below zero. This clearly communicates application-specific constraints to clients.

### 2. MCP (Model Control Plane) Server (mcp-server/)

The MCP Server acts as the intelligent bridge between natural language and the Inventory Service API.

#### Architecture and Modularity:

- **Separate Server:** As required, the MCP runs as a distinct FastAPI server (http://127.0.0.1:8001), demonstrating a decoupled microservices architecture.

- **OOP (LLMAgent Class):** The core agent logic is encapsulated within an LLMAgent class. This adheres to Object-Oriented Programming (OOP) principles, promoting code readability, maintainability, and reusability. Dependencies like the LLM model, tools, and system prompt are injected into the LLMAgent's constructor, demonstrating a clean separation of concerns.

- **Dedicated Client (inventory_client.py):** A separate InventoryClient class handles all HTTP communication with the Inventory Service. This centralizes API interaction logic and error handling.

- **Dedicated Tools (mcp_tools.py):** LangChain Tool definitions are separated into their own module, clearly defining the actions the agent can perform.

#### GenAI Integration and Prompt Design (The "Brain" of the Agent):

- **LLM Choice (Gemini-Flash):** gemini-1.5-flash-latest was selected for its balance of performance, cost-effectiveness, and strong function-calling capabilities via Google's Generative AI API, integrated seamlessly with LangChain.

- **LangGraph for Agent Orchestration (ReAct Pattern):** LangGraph was utilized to build a robust, stateful agent workflow. The agent follows a ReAct (Reasoning and Acting) pattern:

  - **_call_llm_node (Reason):** The LLM processes the conversation history and decides on the next Action (tool call) or Response (final answer).

  - **_exists_action (Route):** A concise router function determines if the LLM's output contains tool calls, routing to _call_tool_node if true, or ending the conversation if false.

  - **_call_tool_node (Act):** Executes the tool(s) identified by the LLM via the InventoryClient.

  - **Loop Back to LLM:** After tool execution, the flow always returns to _call_llm_node, allowing the LLM to "Observe" the tool's result and Reason on it to formulate a final user-friendly Response.

#### Advanced Prompt Engineering (Core of Intelligence):

The MCP_SYSTEM_PROMPT is meticulously crafted using several advanced prompt engineering techniques:

- **Clear ReAct Instructions:** Explicitly guides the LLM to follow the "Thought, Action, Observation" loop.

- **Detailed Rules:** Provides precise, imperative rules for inventory operations, including quantity sign interpretation (e.g., "bought -5" means sell 5), item name strictness, and handling implicit/relative quantities.

- **Few-Shot Examples:** Crucially, detailed examples are included for various scenarios (successful GET/POST, multi-step calculations like "sell half", and error handling). These examples teach the LLM the desired behavior more effectively than abstract rules alone, significantly boosting consistency and accuracy.

- **Summarization Instruction:** Explicitly instructs the LLM to provide a concise, user-friendly summary after each tool execution or error, ensuring clear user feedback.

#### OpenAPI Specification Usage (Adherence to API Contract):

The MCP Server "uses" the OpenAPI spec from the Inventory Service by adhering to its contract. While not dynamically parsing the openapi.yaml at runtime, the LangChain Tool definitions (mcp_tools.py) were meticulously designed based on the precise endpoint paths, HTTP methods, request body schemas (e.g., item and change for POST /inventory), and response structures documented in the Inventory Service's OpenAPI specification. This ensures full compatibility and respect for the defined API contract.

#### Robust Layered Error Handling:

- **Client-Side Error Translation (inventory_client.py):** This client intercepts 4xx and 5xx HTTP responses from the Inventory Service. It translates generic API errors (e.g., raw 400 messages) into a structured format ({"error": {"translated_message": ...}}) for the LLM to consume. This centralizes error interpretation for the agent.

- **LLM Error Summarization:** The agent's prompt instructs the LLM to interpret these translated error messages and synthesize a human-friendly explanation for the end-user (e.g., "I cannot sell 1000 tshirts. There are only X in stock."). This ensures the user never sees raw API error codes.

### 3. What Makes This Solution Stand Out

- **Comprehensive Problem Solving:** Addresses all task requirements, including implicit quantitative queries and complex error flows.

- **Architectural Clarity:** Clean separation of concerns between services, OOP structure, and clear data flow.

- **Advanced GenAI Craftsmanship:** Demonstrates expertise in LangChain, LangGraph, ReAct prompting, and iterative prompt engineering for achieving highly consistent and intelligent agent behavior in complex scenarios.

- **Robustness:** Thoughtful error handling at multiple layers, from backend validation to LLM interpretation, ensuring a reliable user experience.

- **Attention to Detail:** From requirements.txt management to explicit OpenAPI contract adherence, the solution showcases best practices.

## ⚠️ Known Limitations

- **In-Memory Data Store:** The inventory data resets every time the inventory-service is restarted. For persistent storage, a database (e.g., SQLite, PostgreSQL) would be required.

- **Fixed Inventory Items:** Only 'tshirts' and 'pants' are supported. Extending to more items would require modifications in both services.

- **Single-Turn Conversation:** The MCP server currently processes each natural language query independently without maintaining long-term conversational memory across requests. For multi-turn dialogue, LangGraph's checkpointer or external session management would be needed.

- **No Authentication:** Neither service has user authentication or authorization implemented.

- **No Advanced Tooling:** The project focuses on core LLM agent capabilities; it does not include advanced features like RAG (Retrieval Augmented Generation) or custom fine-tuning of the LLM.
