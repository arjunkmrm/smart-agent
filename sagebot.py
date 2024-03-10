from dotenv import load_dotenv
import streamlit as st
from gemini_agent.utilities.utils import (
    master_tools, 
    sql_to_df, 
    get_function_name, 
    get_function_args, 
    EMPTY_TABLE
    )
from gemini_agent.prompts import GENERAL_ASSISTANT
from gemini_agent.agent_tools import trade_query_assistant, email_assistant, sgt_assistant
from gemini_agent.agent_tools import KnowledgeStores
from vertexai.generative_models import (
    GenerativeModel,
    Part
    )
from gemini_agent.agent_uno import SmartAgent
from gemini_agent.sub_agents import knowledge_agent
load_dotenv()
#import win32com.client as win32
# from ada_genai.vertexai import (
#     GenerativeModel,
#     Part
# )

# Constants
EUROCLEAR_ASSISTANT = "euroclear_assistant"
SOP_ASSISTANT = "sop_assistant"
PORTIONS_ASSISTANT = "portions_assistant"
TRADE_QUERY_ASSISTANT = "trade_query_assistant"
EMAIL_ASSISTANT = "email_assistant"
SGT_ASSISTANT = "sgt_assistant"
KNOWLEDGE_ASSISTANT = "knowledge_assistant"

# function loading texts
FUNCTION_TEXT = {
    EUROCLEAR_ASSISTANT: "Searching euroclear",
    SOP_ASSISTANT: "Searching SOPs",
    PORTIONS_ASSISTANT: "Searching portions",
    TRADE_QUERY_ASSISTANT: "Searching trades",
    EMAIL_ASSISTANT: "Drafting email",
    SGT_ASSISTANT: "Converting time",
    KNOWLEDGE_ASSISTANT: "Asking knowledge assistant"
}

# these can be moved to config
# path for functions
EUROCLEAR_PATH = "/Users/arjun/Documents/github/smart-agent/docs/sop-docs/euroclear"
EUROCLEAR_COLLECTION = "ec_docs"
SOP_PATH = "/Users/arjun/Documents/github/smart-agent/docs/sop-docs/acu_sop"
SOP_COLLECTION = "sop_docs"
PORTIONS_PATH = "/Users/arjun/Documents/github/smart-agent/docs/sop-docs/portions_sop"
PORTIONS_COLLECTION = "portions_docs"
# EMAIL_PATH = ""
# EMAIL_COLLECTION = ""

# master_tools = Tool(
#   function_declarations=[euroclear_assistant_func, sop_assistant_func, portions_assistant_func, trade_query_func, draft_email_func, convert_sgt_func],
# )

# reset chat history after every n convos? *********
def main():
    st.title("SageBot")
    # itialise sagebot stae on first run
    if "sagebot" not in st.session_state:
        # these can be abstracted - import the instantiation initialised directly
        st.session_state.euroclear_store = KnowledgeStores(EUROCLEAR_PATH, EUROCLEAR_COLLECTION, k=3) # init stores
        st.session_state.sop_store = KnowledgeStores(SOP_PATH, SOP_COLLECTION, k=3)
        st.session_state.portions_store = KnowledgeStores(PORTIONS_PATH, PORTIONS_COLLECTION, k=3)
        st.session_state.function_dict = {
            EUROCLEAR_ASSISTANT: st.session_state.euroclear_store.knowledge_assistant,
            SOP_ASSISTANT: st.session_state.sop_store.knowledge_assistant,
            PORTIONS_ASSISTANT: st.session_state.portions_store.knowledge_assistant,
            # KNOWLEDGE_ASSISTANT: knowledge_agent,
            TRADE_QUERY_ASSISTANT: trade_query_assistant,
            SGT_ASSISTANT: sgt_assistant,
            EMAIL_ASSISTANT: email_assistant,
        }
        st.session_state.sagebot = SmartAgent(st.session_state.function_dict, master_tools) # init agent
        #st.session_state.chat = model.start_chat(response_validation=False) # can be removed
        # st.session_state.sagebot.chat.send_message(.....)
        st.session_state.sagebot.chat_history = []
        st.session_state.sagebot.chat.send_message(f"{GENERAL_ASSISTANT}")
    st.session_state.sources = []

    # deep copy was for testing. display chat history on refresh
    for message in st.session_state.sagebot.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # user input
    if prompt := st.chat_input("What is up?"):
        with st.chat_message("user"): # display user message in chat message container
            st.markdown(prompt)
        
        # step 1: based on user input, get function call if any
        response = st.session_state.sagebot.get_func(prompt) # get agent response to query
        function = get_function_name(response) # get function call if any
        function_store = None # an object to hold agent's n-1 function call, so it's not lost in the while loop
        
        while function: # loop for multiple function calling
            # get function args to display (for users to get what's happening under the hood)
            values = [] # to store function args for display
            function_args = get_function_args(response)
            values = []
            for arg in function_args:
                values.append(function_args[arg])
            query_string = ', '.join(values) # function args to string for display

            # function execution happens here
            with st.spinner(f'{FUNCTION_TEXT.get(function)}: {query_string}'): # get function queries
                function_return = st.session_state.sagebot.call_func(response) # call the agent determined function using agent generated args
                #st.success('Done!')
                response = function_return[0] # function output -> model ->
                additional_output = function_return[1] # additional function response to return optional objects
                if not response: break
                function_store = function
                function = get_function_name(response)
                # breaks out of loop when no more function to call
            
        assistant_response = response.text # get final response after function calls end
        
        if function_store: # function call right before agent responds
            if function_store == TRADE_QUERY_ASSISTANT and additional_output != EMPTY_TABLE:
                with st.chat_message("assistant"):
                    df = sql_to_df(additional_output)
                    st.session_state.sagebot.chat_history.append({"role":"assistant", "content":"(*trade details)"})
                    st.dataframe(df)
            else:
                with st.chat_message("assistant"):
                    st.session_state.sagebot.chat_history.append({"role":"assistant", "content":assistant_response})
                    st.markdown(assistant_response)
        else: # direct response without function call
            with st.chat_message("assistant"):
                st.session_state.sagebot.chat_history.append({"role":"assistant", "content":assistant_response})
                st.markdown(assistant_response)

if __name__ == "__main__":
    main()
