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

1. Obtain a Google API Key with access to the Gemini API (e.g., from Google AI Studio or Google Cloud Vertex AI).
2. Create a file named `.env` in the `mcp-server/` directory (at the same level as `main.py`).
3. Add your API key to this file:

```bash
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```

**Important:** The `.env` file is excluded from Git via `.gitignore` for security.

#### Run the MCP Server

```bash
# Ensure your virtual environment is active and .env file is set up
uvicorn main:app --reload --port 8001
The MCP Server will now be running at http://127.0.0.1:8001. You can access its interactive API documentation (Swagger UI) at http://127.0.0.1:8001/docs.

Ensure both services (Inventory on 8000 and MCP on 8001) are running simultaneously for the MCP Server to function correctly.

## 🧪 API Endpoints and Examples

You can interact with both services using curl (BASH/Linux/macOS syntax shown below, adjust for PowerShell if needed), Postman/Insomnia, or Swagger UI.

### Inventory Web Service (http://127.0.0.1:8000)

This service manages inventory for 'tshirts' (initial: 20) and 'pants' (initial: 15).

#### 1. GET /inventory

Returns the current inventory count.

```bash
# Example Request:
curl -X GET "http://127.0.0.1:8000/inventory" -H "accept: application/json"

# Example Expected Response:
# {"tshirts":20,"pants":15}
```

#### 2. POST /inventory

Modifies the count of an item.

**Request Body Example:** `{"item": "tshirts", "change": -5}`

```bash
# Example Request (Sell 5 tshirts):
curl -X POST "http://127.0.0.1:8000/inventory" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"item": "tshirts", "change": -5}'

#Response
{"tshirts":13,"pants":25}

# Example Request (Add 10 pants):
curl -X POST "http://127.0.0.1:8000/inventory" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"item": "pants", "change": 10}'

#Response
{"tshirts":13,"pants":35}
```

#### Error Handling Examples (Inventory Service Direct Interaction)

##### POST /inventory - Invalid Item Name (400 Bad Request)

```bash
# Example Request (Invalid item 'hats'):
curl -X POST "http://127.0.0.1:8000/inventory" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"item": "hats", "change": 1}'

# Response:
{"detail":"Item 'hats' not found. Only 'tshirts' and 'pants' are supported."}
```

##### POST /inventory - Reduce Below Zero (400 Bad Request)

```bash
# Example Request (Sell 1000 tshirts):
curl -X POST "http://127.0.0.1:8000/inventory" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"item": "tshirts", "change": -1000}'

#Response (counts may vary based on current stock):
{"detail":"Cannot reduce tshirts count below zero. Current: 13, Attempted change: -1000"}
```


### MCP Server (http://127.0.0.1:8001)

This service converts natural language queries into API calls to the Inventory Service.

#### 1. POST /process_query

Accepts a natural language string and returns a GenAI-generated response.

**Request Body Sample Test Cases:** `{"query": "I sold 3 t shirts"}`

```bash
# Example Request (Get current inventory):
curl -X POST "http://127.0.0.1:8001/process_query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many pants and shirts do I have?"}'

#Response:
{"response":"OK. Currently, there are 35 pants and 13 tshirts in stock."} # (Counts will vary)

# Example Request (Sell 3 tshirts):
curl -X POST "http://127.0.0.1:8001/process_query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"query": "I sold 3 tshirts"}'

#Response:
{"response":"OK. I've updated the inventory. There are now 10 tshirts in stock."} # (Counts will vary)

# Example Request (Add 5 pants):
curl -X POST "http://127.0.0.1:8001/process_query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"query": "Add five pants"}'

#Response:
{"response":"OK. I've added 5 pants to the inventory. There are now 40 pants and 10 tshirts in stock."} # (Counts will vary)

# Example Request (Sell half of the inventory - Multi-step logic): Agent will firt call get_inventory, calculate the half of the stock, and then use update_inventory to make updates: one item at a time. The behavior is handled by the prompt, aided by the tools and the graph constructed for the agent.

curl -X POST "http://127.0.0.1:8001/process_query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"query": "Sell half of the inventory"}'

# Response (will vary based on current stock):
{"response":"OK. I have sold half of the tshirts and half of the pants. The tshirts quantity is now 5 and the pants quantity is now 20."}

# Example Request (Invalid item name - LLM relays backend error):
curl -X POST "http://127.0.0.1:8001/process_query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"query": "Add 2 hats"}'

# Example Expected Response:
# {"response":"I'm sorry, I can only manage inventory for 'tshirts' and 'pants'. 'Hats' is not a supported item."}

# Example Request (Reduce below zero - LLM relays backend error):
curl -X POST "http://127.0.0.1:8001/process_query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"query": "Sell 1000 tshirts"}'

# Example Expected Response:
# {"response":"I am sorry, but selling 100 tshirts is not possible since there are only 5 tshirts in stock."}

# Example Request (Decimal input - LLM clarification):
curl -X POST "http://127.0.0.1:8001/process_query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"query": "Add 2.5 tshirts"}'

#Response:
{"response":"I cannot add 2.5 tshirts because I can only update inventory with whole numbers. Could you please specify the exact number of tshirts to add?"}
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