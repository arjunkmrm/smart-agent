from gemini_agent import SmartAgent
from utils import knowledge_tools

FUNCTION_DICT = ""
# mapping between function names and actual function

knowledge_agent = SmartAgent(FUNCTION_DICT, knowledge_tools)
#  can create as many agents as you want

# can now map search knowledge in func dict to knowledge_agent.execute_task -> chooses from multiple knowledge bases to find answer