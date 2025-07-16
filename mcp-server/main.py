import os #To access environment variables (e.g., GOOGLE_API_KEY, INVENTORY_SERVICE_URL).
import json #To fetch valid_items from openapi.json and handle tool responses for the LLM.
import requests #To fetch the Inventory Service’s openapi.json.
from typing import Dict, Any, List, TypedDict, Annotated #To define precise type definitions (e.g., AgentState, tool return types).
from fastapi import FastAPI, HTTPException, status #To create the MCP Server API.
from pydantic import BaseModel #To define the QueryRequest schema.
from langchain_google_genai import ChatGoogleGenerativeAI #To initialize the Gemini-2.0-flash LLM.
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage #To define the LLM agent’s workflow.
from langgraph.graph import StateGraph, END #To define the LLM agent’s workflow.
from langgraph.graph.message import add_messages #To aggregate conversation messages in AgentState.
from langchain_core.prompts import ChatPromptTemplate #To structure the LLM’s prompt with system and user messages.
from langchain_core.tools import BaseTool #To type the tools list for the LLMAgent.
from mcp_tools import get_inventory_tool, update_inventory_tool #To interact with the Inventory Service.
from dotenv import load_dotenv #To load environment variables from a .env file.

load_dotenv() # Load environment variables from .env file at startup.
#This simplifies configuration for GOOGLE_API_KEY and INVENTORY_SERVICE_URL.

# --- Pydantic Model for Agent State ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
# Define AgentState to track the LLM’s conversation history.
# Uses Annotated[list, add_messages] to aggregate messages (HumanMessage, AIMessage, ToolMessage) across workflow steps.

# --- System Prompt ---
# Define the system prompt for the LLM to process inventory-related queries.
# Specifies rules for quantity handling (Task 1), item normalization (Task 2), multi-item processing (Task 3),
# and result formatting (Task 4). Uses {valid_items} placeholder for dynamic item support via openapi.json.
#A rule-based system prompt tailored for task-specific natural language processing, designed to guide the gemini-2.0-flash LLM
MCP_SYSTEM_PROMPT = (
    "You are an Inventory Management Assistant. Use `get_inventory_tool` and `update_inventory_tool` to manage inventory based on user queries. "
    "Follow these rules:\n\n"

    "1. **Quantities**\n"
    "- Process only exact integer quantities (e.g., 'add 5 tshirts', 'sell 3 pants').\n"
    "- Use positive `change` for 'add'/'buy', negative for 'sell'/'remove'/'clear'.\n"
    "- If quantity sign conflicts with verb (e.g., 'buy -5', 'sell 5'), the numerical sign takes precedence.\n"
    "- For 'clear all [item]', use `get_inventory_tool` to get the current count, then set `change` to its negative.\n"
    "- Reject non-integer quantities (e.g., 'sell 2.5 tshirts') with: 'Only whole numbers are supported. Please specify an exact number.'\n"
    "- Reject relative quantities (e.g., 'sell half') with: 'Please provide an exact number for updates.'\n\n"

    "2. **Item Names**\n"
    "- Normalize item names before tool calls:\n"
    "  - Known items: 'tshirt', 'Tshirt', 't-shirts', 'T-shirt', 't shirts', 'tshirts' → 'tshirts'; "
    "'pant', 'Pant', 'PANTS', 'pants' → 'pants' (lowercase, plural).\n"
    "  - Unrecognized items: lowercase, pluralize if applicable (e.g., 'shirt', 'Shirt' → 'shirts'; 'hat', 'HAT' → 'hats'; "
    "'pantis' → 'pantis'; 'tshit' → 'tshits'). Do not correct typos.\n"
    "- Check normalized name against valid items: {valid_items}.\n"
    "- If in {valid_items}, call `update_inventory_tool` with the normalized name.\n"
    "- If not in {valid_items}, collect for error reporting without tool calls.\n\n"

    "3. **Multiple Items**\n"
    "- For queries with multiple items (e.g., 'sell 5 tshirts and 3 hats'), call `update_inventory_tool` for each valid item separately.\n"
    "- For invalid items, combine into a single error message (e.g., 'Pantis and shirts are not supported.').\n"
    "- List valid items only once at the end of the error message (e.g., 'Valid items: {valid_items}.').\n"
    "- For ambiguous queries (e.g., 'add 5'), respond: 'Please specify which item(s) to update.'\n\n"

    "4. **Results**\n"
    "- For successful (HTTP 200) tool calls, include updated inventory (e.g., 'Added 5 tshirts. Inventory: 10 tshirts, 15 pants.').\n"
    "- For errors (400/422), explain the issue without an inventory summary (e.g., 'Cannot reduce tshirts below zero.' or 'Invalid item name 'pantis'.').\n"
    "- For multiple invalid items, combine into one sentence (e.g., 'Pantis and shirts are not supported. Valid items: {valid_items}.').\n\n"

    "**Examples**\n"
    "- 'Add 5 tshirts': Call `update_inventory_tool(item='tshirts', change=5)`. Response: 'Added 5 tshirts. Inventory: [updated].'\n"
    "- 'Sell one T-shirt': Normalize to 'tshirts', call `update_inventory_tool(item='tshirts', change=-1)`. Response: 'Sold 1 tshirt. Inventory: [updated].'\n"
    "- 'Clear all pants': Call `get_inventory_tool`, then `update_inventory_tool(item='pants', change=-count)`. Response: 'Cleared all pants. Inventory: [updated].'\n"
    "- 'Add 5 pantis': Normalize to 'pantis', not in {valid_items}. Response: 'Pantis is not supported. Valid items: {valid_items}.'\n"
    "- 'Sell 3 tshit': Normalize to 'tshits', not in {valid_items}. Response: 'Tshits is not supported. Valid items: {valid_items}.'\n"
    "- 'Add 20 pantis and 30 shirts': Normalize to 'pantis', 'shirts', not in {valid_items}. Response: 'Pantis and shirts are not supported. Valid items: {valid_items}.'\n"
    "- 'Add 5 tshirts and 10 pantis': Call `update_inventory_tool(item='tshirts', change=5)`, 'pantis' not in {valid_items}. Response: 'Added 5 tshirts. Pantis is not supported. Inventory: [updated]. Valid items: {valid_items}.'\n"
    "- 'Sell 2.5 tshirts': Respond: 'Only whole numbers are supported. Please specify an exact number.'\n"
    "- 'Add 5': Respond: 'Please specify which item(s) to update.'"
)


# --- LLMAgent Class ---
class LLMAgent:
    def __init__(self, model: ChatGoogleGenerativeAI, tools: List[BaseTool], inventory_service_url: str, system_prompt_template: str = ""):
        """
        Initialize the LLM agent with model, tools, inventory service URL, and system prompt template.
        
        Args:
            model (ChatGoogleGenerativeAI): The LLM model (gemini-2.0-flash) for query processing.
            tools (List[BaseTool]): List of tools (get_inventory_tool, update_inventory_tool) for inventory operations.
            inventory_service_url (str): URL of the Inventory Service for fetching valid_items.
            system_prompt_template (str): Template for the system prompt with {valid_items} placeholder.
        
        Sets up the LLM with tools and a workflow to handle queries, supporting all four tasks.
        Fetches valid_items from openapi.json for dynamic item validation (Task 2).
        """
        self.inventory_service_url = inventory_service_url
        self.valid_items = self._get_valid_inventory_items(inventory_service_url)
        self.system_prompt_content = system_prompt_template.format(valid_items=self.valid_items)
        self.tools_dict = {t.name: t for t in tools}
        self.llm_with_tools = model.bind_tools(tools)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt_content),
            ("placeholder", "{messages}")
        ]) # Define the prompt structure with system prompt and user messages, guiding the LLM’s query processing.
        self.llm_chain = self.prompt | self.llm_with_tools # Create a LangChain chain combining the prompt and LLM with 
                                                           # tools for streamlined query execution.
        # Initialize a LangGraph workflow to manage stateful interactions between LLM and tool calls.
        workflow = StateGraph(AgentState)
        # Add a node to invoke the LLM for query processing and tool call decisions.
        workflow.add_node("call_llm_node", self._call_llm_node)
        # Add a node to execute tools based on LLM’s tool call requests.
        workflow.add_node("call_tool_node", self._call_tool_node)
        # Start the workflow with the LLM node to process the user query.
        workflow.set_entry_point("call_llm_node")
        # Route to tool node if the LLM requests tool calls, else end the workflow.
        workflow.add_conditional_edges(
            "call_llm_node",
            self._route_agent,
            {True: "call_tool_node", False: END}
        )
        # Return to LLM node after tool execution to process tool outputs and generate a final response.
        workflow.add_edge('call_tool_node', 'call_llm_node')
        # Compile the workflow into an executable graph for query processing.
        self.graph = workflow.compile()

    def _get_valid_inventory_items(self, url: str) -> List[str]:
        """
        Fetch valid item names from the Inventory Service’s openapi.json.

        Args:
            url (str): The Inventory Service URL (e.g., http://127.0.0.1:8000).

        Returns:
            List[str]: List of valid item names (e.g., ["tshirts", "pants"]) or default ["tshirts", "pants"] if fetch fails.
        """
        try:
            response = requests.get(f"{url}/openapi.json")
            response.raise_for_status()
            openapi_spec = response.json()
            inventory_item_schema = openapi_spec.get("components", {}).get("schemas", {}).get("InventoryItem", {})
            item_enum = inventory_item_schema.get("enum", [])
            if not item_enum:
                print(f"Warning: Could not find 'enum' for 'item' in InventoryUpdateRequest schema at {url}/openapi.json. \
                      Defaulting to ['tshirts', 'pants'].")
             # Extract valid item names from openapi.json, enabling dynamic item support (e.g., adding "jackets").
            return item_enum or ["tshirts", "pants"] # Default to ["tshirts", "pants"] if no valid items are found.
        except Exception as e:
            print(f"Error fetching OpenAPI spec from {url}: {e}. Defaulting to ['tshirts', 'pants'].")
             # Fallback to default items to ensure system functionality if the Inventory Service is unavailable
            return ["tshirts", "pants"]

    def _call_llm_node(self, state: AgentState):
        """
        Invoke the LLM to process the current state’s messages and decide on tool calls.

        Args:
            state (AgentState): Current conversation state with messages.

        Returns:
            Dict: Updated state with the LLM’s response (AIMessage with potential tool_calls).
        """
        messages = state["messages"]
        response = self.llm_chain.invoke({"messages": messages})
        # Return the LLM’s response, which may include tool calls or a final response.
        return {"messages": [response]}

    def _call_tool_node(self, state: AgentState):
        """
        Execute tool calls requested by the LLM and return ToolMessage responses.

        Args:
            state (AgentState): Current conversation state with LLM’s tool call requests.

        Returns:
            Dict: Updated state with ToolMessage responses from tool executions.
        """
        last_message = state["messages"][-1]
        tool_outputs = []

        for tool_call_item in last_message.tool_calls:
            tool_name = tool_call_item["name"]
            tool_args = tool_call_item["args"]
            tool_id_for_message = tool_call_item["id"]

            try:
                # Execute the tool and format output as JSON for LLM consistency.
                output = self.tools_dict[tool_name].invoke(tool_args)
                content = json.dumps(output) if isinstance(output, dict) else str(output)
                tool_outputs.append(ToolMessage(content=content, tool_call_id=tool_id_for_message, name=tool_name))
            except Exception as e:
                # Handle tool execution errors, ensuring the LLM receives structured error messages.
                error_msg = f"Error executing tool '{tool_name}': {e}"
                print(f"Tool '{tool_name}' execution FAILED: {error_msg}")
                tool_outputs.append(ToolMessage(content=error_msg, tool_call_id=tool_id_for_message, name=tool_name))

        # Return tool outputs for the LLM to process into a user-friendly response.
        return {"messages": tool_outputs}

    def _route_agent(self, state: AgentState):
        """
        Route the workflow based on whether the LLM requested tool calls.

        Args:
            state (AgentState): Current conversation state.

        Returns:
            bool: True if tool calls are present, False otherwise.
        """
        result = state["messages"][-1]
        # Check for tool calls to decide the next workflow step.
        return hasattr(result, 'tool_calls') and len(result.tool_calls) > 0

    def run(self, query: str, recursion_limit: int = 10) -> Dict[str, Any]:
        """
        Process a natural language query through the LLM and return the response.

        Args:
            query (str): User’s natural language query (e.g., “add 5 tshirts”).
            recursion_limit (int): Maximum workflow iterations to prevent infinite loops.

        Returns:
            Dict[str, Any]: Final response with the LLM’s formatted output.
        """
        initial_message = HumanMessage(content=query)
        # Process the query through the workflow and return the LLM’s final response.
        final_state = self.graph.invoke({"messages": [initial_message]}, config={"recursion_limit": recursion_limit})
        response_content = final_state["messages"][-1].content
        return {"response": response_content}

# --- FastAPI App Setup ---
app = FastAPI(
    title="MCP (Model Control Plane) Server",
    description="A GenAI-powered interface to manage inventory via natural language.",
    version="1.0.0",
)

# Validate GOOGLE_API_KEY to ensure the LLM can be initialized, critical for query processing.
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it in .env file.")

# Initialize the Gemini-2.0-flash LLM with zero temperature for deterministic responses.
# This ensures consistent query processing and tool call decisions.
llm_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0)

# Define the list of tools for the LLM agent, covering all inventory operations.
# get_inventory_tool supports Task 4 (summarization) and Task 1 (e.g., “clear all pants”).
# update_inventory_tool supports Tasks 1 (quantity processing) and 3 (multi-item updates).
mcp_tools_list = [get_inventory_tool, update_inventory_tool]

# Initialize the LLMAgent with the LLM, tools, Inventory Service URL, and system prompt.
# Configures the agent to process queries and fetch valid_items for dynamic item support (Task 2).
agent_instance = LLMAgent(
    model=llm_model,
    tools=mcp_tools_list,
    inventory_service_url=os.getenv("INVENTORY_SERVICE_URL", "http://127.0.0.1:8000"),
    system_prompt_template=MCP_SYSTEM_PROMPT
)

# Pydantic model for the incoming query
class QueryRequest(BaseModel):
    query: str

@app.post("/process_query")
async def process_query(request: QueryRequest) -> Dict[str, Any]:
    """
    Processes a natural language query related to inventory and returns the result.

    Args:
        request (QueryRequest): Pydantic model containing the user’s query string.

    Returns:
        Dict[str, Any]: Response with the LLM’s formatted output or an error message.
    
    Handles queries via the LLMAgent, supporting all four tasks and returning user-friendly responses.
    Raises HTTP exceptions for validation (400) or unexpected errors (500).
    """
    try:
        # Process the query through the LLMAgent and return the response.
        return agent_instance.run(request.query)
    except ValueError as e:
        # Handle validation errors (e.g., missing GOOGLE_API_KEY) with a 400 status.
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected errors with a 500 status and log for debugging.
        import traceback
        traceback.print_exc()
        print(f"An unexpected error occurred in process_query: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing your request.")