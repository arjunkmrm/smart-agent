from agent_uno import SmartAgent
from utilities.utils import knowledge_tools
from agent_tools import KnowledgeStores
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerativeModel,
    Part,
    Tool,
)
from tool_definitions import euroclear_assistant_func, sop_assistant_func
from sagebot_config import EUROCLEAR_ASSISTANT, EUROCLEAR_COLLECTION, EUROCLEAR_PATH
from sagebot_config import SOP_ASSISTANT, SOP_COLLECTION, SOP_PATH
# knowledge sub-agent
# function names
EUROCLEAR_ASSISTANT = 'euroclear_assistant'
PPORTIONS_ASSISTANT = 'portions_assistant'
SOP_ASSISTANT = 'sop_assistant'

# funtion init
euroclear_store = KnowledgeStores(EUROCLEAR_PATH, EUROCLEAR_COLLECTION) # euroclear stuff
sop_store = KnowledgeStores(SOP_PATH, SOP_COLLECTION) # acu sop docs

# function mapping
KNOWLEDGE_FUNCTION_DICT = {
            EUROCLEAR_ASSISTANT: euroclear_store.knowledge_assistant,
            SOP_ASSISTANT: sop_store.knowledge_assistant,
        }

knowledge_tools = Tool(function_declarations=[euroclear_assistant_func, sop_assistant_func])
knowledge_agent = SmartAgent(KNOWLEDGE_FUNCTION_DICT, knowledge_tools)
# can now map search knowledge in func dict to knowledge_agent.execute_task -> chooses from multiple knowledge bases to find answer