from agent_uno import AgentUno
from utils import knowledge_tools
from agent_tools import KnowledgeStores
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerativeModel,
    Part,
    Tool,
)
from tool_definitions import euroclear_assistant_func, sop_assistant_func, portions_assistant_func

# knowledge sub-agent
# function names
EUROCLEAR_ASSISTANT = 'euroclear_assistant'
PPORTIONS_ASSISTANT = 'portions_assistant'
SOP_ASSISTANT = 'sop_assistant'

# funtion init
euroclear_store = KnowledgeStores("/Users/arjun/Documents/github/smart-agent/docs/sop-docs/euroclear", "ec_docs") # euroclear stuff
portions_store = KnowledgeStores("/Users/arjun/Documents/github/smart-agent/docs/sop-docs/portions_sop", "portions_docs") # magical portions
sop_store = KnowledgeStores("/Users/arjun/Documents/github/smart-agent/docs/sop-docs/euroclear", "sop_docs") # acu sop docs

# function mapping
KNOWLEDGE_FUNCTION_DICT = {
            EUROCLEAR_ASSISTANT: euroclear_store.knowledge_assistant,
            PPORTIONS_ASSISTANT: portions_store.knowledge_assistant,
            SOP_ASSISTANT: sop_store.knowledge_assistant,
        }

knowledge_tools = Tool(function_declarations=[euroclear_assistant_func, sop_assistant_func, portions_assistant_func])
knowledge_agent = AgentUno(KNOWLEDGE_FUNCTION_DICT, knowledge_tools)
# can now map search knowledge in func dict to knowledge_agent.execute_task -> chooses from multiple knowledge bases to find answer