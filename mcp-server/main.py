import os
import json
from typing import Dict, Any, List, TypedDict, Annotated
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from mcp_tools import get_inventory_tool, update_inventory_tool
from dotenv import load_dotenv

load_dotenv()

# --- Pydantic Model for Agent State ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# --- LLMAgent Class ---
class LLMAgent:
    # Accept LLM model, tools, and system prompt as arguments
    def __init__(self, model: ChatGoogleGenerativeAI, tools: List[BaseTool], system_prompt: str = ""):
        self.system_prompt_content = system_prompt # Store the system prompt
        self.tools_dict = {t.name: t for t in tools} # Store tools in a dict for easy lookup
        self.llm_with_tools = model.bind_tools(tools)
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt_content),
            ("placeholder", "{messages}")
        ])
        self.llm_chain = self.prompt | self.llm_with_tools

        workflow = StateGraph(AgentState)
        workflow.add_node("call_llm_node", self._call_llm_node)
        workflow.add_node("call_tool_node", self._call_tool_node)
        workflow.set_entry_point("call_llm_node")
        workflow.add_conditional_edges(
            "call_llm_node",
            self._route_agent,
            {
                True: "call_tool_node",
                False: END  
            }
        )
        workflow.add_edge('call_tool_node', 'call_llm_node')
        self.graph = workflow.compile()

    def _call_llm_node(self, state: AgentState):
        messages = state["messages"]
        response = self.llm_chain.invoke({"messages": messages})
        return {"messages": [response]}

    def _call_tool_node(self, state: AgentState):
        last_message = state["messages"][-1]
        tool_outputs = []

        for tool_call_item in last_message.tool_calls:
            tool_name = tool_call_item["name"]
            tool_args = tool_call_item["args"]
            tool_id_for_message = tool_call_item["id"] 

            try:
                output = self.tools_dict[tool_name].invoke(tool_args)
                print("The output type for the tool call is: ", type(output))
                content_for_tool_message = json.dumps(output) if isinstance(output, dict) else str(output)
                tool_outputs.append(ToolMessage(content=content_for_tool_message, tool_call_id=tool_id_for_message, name=tool_name)) 
                
            except KeyError as e: # Catch specifically if tool_name is not found (to avoid hallucination)
                error_msg = f"Error: Attempted to call an unknown tool '{tool_name}'. This tool is not defined. Original error: {e}"
                print(f"  Tool '{tool_name}' execution FAILED: {error_msg}")
                tool_outputs.append(ToolMessage(content=error_msg, tool_call_id=tool_id_for_message, name=tool_name))
            except Exception as e: # Catch other execution errors
                error_msg = f"Error executing tool '{tool_name}': {e}"
                print(f"  Tool '{tool_name}' execution FAILED: {error_msg}")
                tool_outputs.append(ToolMessage(content=error_msg, tool_call_id=tool_id_for_message, name=tool_name))

        return {"messages": tool_outputs}

    def _route_agent(self, state: AgentState):
        result = state["messages"][-1] # Access state as a dictionary
        # Ensure tool_calls attribute exists and is a non-empty list
        return hasattr(result, 'tool_calls') and len(result.tool_calls) > 0

    def run(self, query: str, recursion_limit: int = 10) -> Dict[str, Any]:
        initial_message = HumanMessage(content=query)
        final_state = self.graph.invoke({"messages": [initial_message]}, config={"recursion_limit": recursion_limit})
        response_content = final_state["messages"][-1].content
        return {"response": response_content}

# --- FastAPI App Setup ---
app = FastAPI(
    title="MCP (Model Control Plane) Server",
    description="A GenAI-powered interface to manage inventory via natural language.",
    version="1.0.0",
)

# 1. Define the System Prompt string
MCP_SYSTEM_PROMPT = (
    "You are an intelligent Inventory Management Assistant. "
    "Your primary goal is to help users manage inventory for 'tshirts' and 'pants'. "
    "You can answer questions about current stock and modify stock levels. "
    "Always prioritize using the available tools to fulfill user requests related to inventory. "
    "If a tool call returns an error, explain the error to the user in a helpful and concise manner.\n\n"

    "Inventory Management Rules:\n"
    "1. Quantity Sign:\n"
    "   - For increases (e.g., 'add 5', 'bought 5'), the 'change' should be positive.\n"
    "   - For decreases (e.g., 'sell 5', 'remove 5'), the 'change' should be negative.\n"
    "   - If a positive action verb ('bought', 'add') is combined with a negative quantity (e.g., 'bought -5'), "
    "     or a negative action verb ('sold', 'remove') with a positive quantity (e.g., 'sold 5' for -5 change), "
    "     the *explicit numerical sign takes precedence*. For 'bought -5', the change should be -5 (removal). "
    "     This implies 'buying a negative amount' is equivalent to selling. "
    "   - Focus on the final desired effect on inventory: positive for increase, negative for decrease.\n"

    "2. Item Name Strictness: You can only manage inventory for 'tshirts' and 'pants'. "
    "   - When the user mentions an item, you MUST use the EXACT STRING from their query for the 'item' argument "
    "     if the intent clearly matches one of these two. "
    "   - DO NOT attempt to correct, map, or infer synonyms (e.g., 'shirts' -> 'tshirts'). "
    "   - If the user provides an item name not *exactly* 'tshirts' or 'pants' (case-insensitive), or a direct plural form "
    "     that the service expects, you MUST pass that exact, uncorrected user-provided item name to the tool. "
    "     The underlying inventory service is responsible for strict item name validation (e.g., 'shirts' -> 'shirts', 'hats' -> 'hats').\n"

    "3. Handling Implicit or Relative Quantities (Percentages, 'All', 'Half', 'Remaining'):\n"
    "   - If the user asks to modify inventory using a relative or implicit quantity (e.g., 'sell 20% of the pants', 'buy 10% of tshirts', "
    "     'sell all items', 'sell half of the tshirts', 'buy the remaining pants', 'clear all stock', 'empty inventory'), "
    "     you MUST FIRST use the `get_inventory_tool` to determine the current stock levels of the relevant items. "
    "   - THEN, after obtaining the current stock, calculate the exact numerical quantity for *each affected item* based on the user's request. "
    "       - For percentages (e.g., 'X% of the [item]s', 'X% of inventory'), apply the percentage to the current count of each specified item (or all items if 'inventory' is mentioned generally). "
    "       - Remember that buying implies a positive change, and selling implies a negative change. "
    "   - CRUCIAL: If the calculated numerical quantity is a **fractional number** (e.g., 7.5 items from 'half of 15', or a direct input like '2.5'), "
    "     you MUST NOT proceed with the `update_inventory_tool`. "
    "     Instead, you MUST inform the user that only whole numbers are supported and ask them to specify the exact whole number they wish to add or remove. "
    "     For example: 'I cannot add 2.5 tshirts because I can only update inventory with whole numbers. Could you please specify the exact number of tshirts to add?'"
    "   - ONLY IF the calculated quantity is a whole number, or the user provides a clear whole number after clarification, should you use the `update_inventory_tool`. "
    "     You might need to call `update_inventory_tool` multiple times if multiple items are affected. "
    "   - Finally, after successful updates, provide a clear confirmation message to the user.\n"

    "4. Summarizing Tool Results: After executing any tool (especially after an update or getting inventory), "
    "   you MUST provide a concise, clear, and user-friendly summary of the outcome to the user. "
    "   If an update occurred, state the new quantity. If an error occurred, explain it clearly."
)

# 2. Initialize the LLM
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it in .env file.")
llm_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0)

# 3. Define the tools to be passed to the agent
mcp_tools_list = [get_inventory_tool, update_inventory_tool] # Collect tools into a list

# 4. Instantiate the LLMAgent
agent_instance = LLMAgent(
    model=llm_model,             # Pass the initialized LLM model
    tools=mcp_tools_list,        # Pass the list of tools
    system_prompt=MCP_SYSTEM_PROMPT # Pass the prompt string
)

# Pydantic model for the incoming natural language query
class QueryRequest(BaseModel):
    query: str

@app.post("/process_query")
async def process_query(request: QueryRequest) -> Dict[str, Any]:
    """
    Processes a natural language query related to inventory and returns the result.
    """
    try:
        return agent_instance.run(request.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"An unexpected error occurred in process_query: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing your request.")