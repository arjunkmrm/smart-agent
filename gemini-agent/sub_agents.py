from agent_uno import AgentUno
from utils import knowledge_tools
from agent_functions import KnowledgeStores
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerativeModel,
    Part,
    Tool,
)

# function names
EUROCLEAR_ASSISTANT = 'euroclear_assistant'
#CMU_ASSISTANT = 'cmu_assistant'
SOP_ASSISTANT = 'sop_assistant'

# funtion init
euroclear_store = KnowledgeStores("/Users/arjun/Documents/github/smart-agent/gemini-agent/data/ec_sop.csv", "ec_sop") # send args
# cmu_store = KnowledgeStores()
sop_store = KnowledgeStores("/Users/arjun/Documents/github/smart-agent/gemini-agent/data/sop_docs.csv", "sop_docs")

# function mapping
KNOWLEDGE_FUNCTION_DICT = {
            EUROCLEAR_ASSISTANT: euroclear_store.knowledge_assistant,
            # CMU_ASSISTANT: cmu_store.knowledge_assistant,
            SOP_ASSISTANT: sop_store.knowledge_assistant,
        }

euroclear_assistant_func = FunctionDeclaration(
    name="euroclear_assistant",
    description="an assistant who answers your questions about euroclear (ec)",
    parameters={
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "user query"
        },
    },
         "required": [
            "query"
      ]
  },
)

cmu_assistant_func = FunctionDeclaration(
    name="cmu_assistant",
    description="an assistant who answers your questions about the central money market unit (cmu)", # can add more
    parameters={
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "user query"
        },
    },
         "required": [
            "query"
      ]
  },
)

sop_assistant_func = FunctionDeclaration(
    name="sop_assistant",
    description="an assistant who answers your questions about the standard operating procedures of the bonds team", # can add more
    parameters={
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "user query"
        },
    },
         "required": [
            "query"
      ]
  },
)

knowledge_tools = Tool(function_declarations=[euroclear_assistant_func, sop_assistant_func])
knowledge_agent = AgentUno(KNOWLEDGE_FUNCTION_DICT, knowledge_tools)

#  can create as many agents as you want

# can now map search knowledge in func dict to knowledge_agent.execute_task -> chooses from multiple knowledge bases to find answer