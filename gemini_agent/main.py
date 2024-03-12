from dotenv import load_dotenv
import streamlit as st
from utilities.utils import (
    sql_to_df, 
    get_function_name, 
    get_function_args, 
    EMPTY_TABLE
    )
from tool_definitions import master_tools
from prompts import GENERAL_ASSISTANT, PLANNER_PROMPT, GENERATE_SQL_PROMPT, SWIFT_ASSISTANT_PROMPT
from agent_tools import trade_query_assistant, email_assistant, sgt_assistant
from agent_tools import KnowledgeStores, TableStores
from vertexai.generative_models import (
    GenerativeModel,
    Part
    )
from agent_uno import SmartAgent
import sys
import os
#from sub_agents import knowledge_agent
load_dotenv()
#import win32com.client as win32
# from ada_genai.vertexai import (
#     GenerativeModel,
#     Part
# )
# Add the parent directory to sys.path to allow importing from it
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from sagebot_config import EUROCLEAR_ASSISTANT, EUROCLEAR_COLLECTION, EUROCLEAR_PATH
from sagebot_config import SOP_ASSISTANT, SOP_COLLECTION, SOP_PATH
from sagebot_config import TRADE_QUERY_ASSISTANT, TRADE_REPORT_DB
from sagebot_config import SWIFT_QUERY_ASSISTANT, SWIFT_DB
from sagebot_config import SGT_ASSISTANT, EMAIL_ASSISTANT, KNOWLEDGE_ASSISTANT
from sagebot_config import FUNCTION_TEXT


# master_tools = Tool(
#   function_declarations=[euroclear_assistant_func, sop_assistant_func, portions_assistant_func, trade_query_func, draft_email_func, convert_sgt_func],
# )

# reset chat history after every n convos? ********************************** IMPORTANT
def main():
    st.title("SageBot")
    # add refresh button only for sagebot.chat
    # itialise sagebot stae on first run
    if "sagebot" not in st.session_state:
        # initialise agent functions
        # these can be abstracted - import the instantiation initialised directly
        st.session_state.euroclear_store = KnowledgeStores(EUROCLEAR_PATH, EUROCLEAR_COLLECTION, k=3) # init stores
        st.session_state.sop_store = KnowledgeStores(SOP_PATH, SOP_COLLECTION, k=3)
        st.session_state.trade_store = TableStores(TRADE_REPORT_DB, GENERATE_SQL_PROMPT)
        st.session_state.swift_store= TableStores(SWIFT_DB, SWIFT_ASSISTANT_PROMPT)

        # map function names to functions
        st.session_state.function_dict = {
            EUROCLEAR_ASSISTANT: st.session_state.euroclear_store.knowledge_assistant,
            SOP_ASSISTANT: st.session_state.sop_store.knowledge_assistant,
            # KNOWLEDGE_ASSISTANT: knowledge_agent,
            TRADE_QUERY_ASSISTANT: st.session_state.trade_store.sql_query_assistant,
            SWIFT_QUERY_ASSISTANT: st.session_state.swift_store.sql_query_assistant,
            SGT_ASSISTANT: sgt_assistant,
            EMAIL_ASSISTANT: email_assistant,
        }

        st.session_state.sagebot = SmartAgent(st.session_state.function_dict, master_tools) # init agent
        st.session_state.sagebot.chat_history = []
        st.session_state.sagebot.chat.send_message(f"{GENERAL_ASSISTANT}")
    st.session_state.sources = []

    # Add refresh button only for sagebot.chat
    if st.button('Refresh'):
        st.session_state.sagebot.chat_history = [] # can comment this for history persistence
        st.session_state.sagebot.chat = st.session_state.sagebot.model.start_chat(response_validation=False)

    # deep copy was for testing. display chat history on refresh
    for message in st.session_state.sagebot.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # user input
    if prompt := st.chat_input("What is up?"):
        with st.chat_message("user"): # display user message in chat message container
            st.markdown(prompt)
        planner_prompt = f"{PLANNER_PROMPT}\n{prompt}" # add planning prompt to trigger agentic behaviour (should i add to evry prompt or once every n?)
        response = st.session_state.sagebot.get_func(planner_prompt) # get agent response to query
        st.session_state.sagebot.chat_history.append({"role":"human", "content":prompt}) # append user query to history
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
