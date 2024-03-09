from dotenv import load_dotenv
import streamlit as st
from utils import master_tools
from utils import sql_to_df
from utils import get_function_name
from prompts import GENERAL_ASSISTANT
from agent_functions import trade_query_assistant, email_assistant
import copy
from agent_functions import KnowledgeStores
# from ada_genai.vertexai import (
#     GenerativeModel,
#     Part
# )
from vertexai import (
    GenerativeModel,
    Part
)
from utils import EMPTY_TABLE
import win32com.client as win32
from smart_agent import SmartAgent
load_dotenv()

# Constants
EUROCLEAR_ASSISTANT = "euroclear_assistant"
TRADE_QUERY_ASSISTANT = "trade_query_assistant"
EMAIL_ASSISTANT = "email_assistant"

FUNCTION_TEXT = {
    EUROCLEAR_ASSISTANT: "Searching euroclear knowledge",
    TRADE_QUERY_ASSISTANT: "Searching trades",
    EMAIL_ASSISTANT: "Drafting email",
}
EUROCLEAR_PATH = "docs\\euroclear_md"
EUROCLEAR_COLLECTION = "ec_sop"
EMAIL_PATH = ""
EMAIL_COLLECTION = ""


def main():
    st.title("SageBot")

    # dict mapping function names to functions
    FUNCTION_DICT = {
        EUROCLEAR_ASSISTANT: st.session_state.euroclear_store.knowledge_assistant,
        TRADE_QUERY_ASSISTANT: trade_query_assistant,
        #EMAIL_ASSISTANT: st.session_state.email_store.knowledge_assistant
    }
    
    # itialise sagebot stae on first run
    if "chat" not in st.session_state:
        # could technically create a start chat method within smart agent to abstractly link different models
        model = GenerativeModel("gemini-pro") # initialise model
        st.session_state.chat = model.start_chat(response_validation=False)
        st.session_state.chat.send_message(f"{GENERAL_ASSISTANT}")
        st.session_state.sagebot = SmartAgent(FUNCTION_DICT, master_tools) # init agent
        st.session_state.euroclear_store = KnowledgeStores(EUROCLEAR_PATH, EUROCLEAR_COLLECTION, k=3) # init stores
        # st.session_state.email_store = KnowledgeStores(EMAIL_PATH, EMAIL_COLLECTION, k=3) # replace with emails
        # add other knowledge paths but link to fnc dict
        st.session_state.chat_history = [] # chat history for display
    st.session_state.sources = []

    # deep copy was for testing. display chat history on refresh
    chat_messages = copy.deepcopy(st.session_state.chat_history)
    for message in chat_messages:
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
            function_args = response.candidates[0].content.parts[0].function_call.args
            values = []
            for arg in function_args:
                values.append(function_args[arg])
            query_string = ', '.join(values) # function args to string for display

            # function execution happens here
            with st.spinner(f'{FUNCTION_TEXT.get(function)}: {query_string}'): # get function queries
                function_return = st.session_state.sagebot.call_func(response, FUNCTION_DICT) # call the agent determined function using agent generated args
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
                    st.session_state.chat_history.append({"role":"assistant", "content":"(*trade details)"})
                    st.dataframe(df)
            else:
                with st.chat_message("assistant"):
                    st.session_state.chat_history.append({"role":"assistant", "content":assistant_response})
                    st.markdown(assistant_response)
        else: # direct response without function call
            with st.chat_message("assistant"):
                st.session_state.chat_history.append({"role":"assistant", "content":assistant_response})
                st.markdown(assistant_response)

if __name__ == "__main__":
    main()
