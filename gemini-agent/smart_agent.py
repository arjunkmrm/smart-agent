# note: for the demo, i could probably send emails to myself and store in a folder to get into df 
from dotenv import load_dotenv
import streamlit as st
from utils import master_tools
from utils import sql_to_df
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
load_dotenv()

def get_function_name(response) -> str:
    """
    simple functon to get function name from gemini response
    """
    function_name = response.candidates[0].content.parts[0].function_call.name
    return function_name

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

class SmartAgent:
    def __init__(self, agent_tools, FUNCTION_DICT) -> None:
        self.chat_history = []
        self.sources = []
        self.FUNCTION_DICT = FUNCTION_DICT
        self.agent_tools = agent_tools

    def call_func(self, response, function_dict): # routes to different functions based on call
        """ route agent response to functions """
        agent_function_call = get_function_name(response) # get the name of agent function
        if agent_function_call: # get corresponding function to agent function call
            handler_function = function_dict.get(agent_function_call) #getattr(self, handler_method_name)
            function_outputs = handler_function(response)
            function_response = function_outputs[0]
            additional_response = function_outputs[1]
            model_response = self.push_response(agent_function_call, function_response)
            # also pass function response directly - this is useful for sql query to df......
            return (model_response, additional_response)  # dynamic function calling
        else:
            # get better exception handling
            st.error(f"Unknown function call: {agent_function_call}")
            return None
        
    def push_response(self, function_name, prompt):
        # could technically append prompt - "whenever you need to use tools, please call the action_planner first to get a plan for how to execute the task"
        # or i send the response to action planner util, whose response is appended 
        # specific trade action could be a function in itself
        if function_name == EUROCLEAR_ASSISTANT:
            prompt = prompt + f"""\n Note to sagebot assistant: if the provided answer does not contain enough information,
            please modify the query and search again. """ # append directly to func response
        elif function_name == TRADE_QUERY_ASSISTANT:
            prompt = prompt + f"""\nNOTE: If there are more than three trades, only three are shown. The other trades have been sent to the user's display directly.""" # append directly
        response = st.session_state.chat.send_message(
            Part.from_function_response(
                name=function_name,
                response={"content": prompt},
            ),
            tools=[self.agent_tools]
        )
        print(prompt)
        return response
    
    def get_func(self, user_query): # get the function which agent wants to call
        response = st.session_state.chat.send_message(f"{user_query}", tools=[self.agent_tools]) # send user message
        st.session_state.chat_history.append({"role":"human", "content":user_query}) # append user query to history
        function_call = response.candidates[0].content.parts[0].function_call.name # get function call
        if not function_call: # if not a function call, just append agent response
            pass
        return response
    
    def execute_task(self, task):
        response = self.get_func(task)
        function = get_function_name(response)
        while function:
            function_return = self.call_func(response, self.FUNCTION_DICT) # call the agent determined function using agent generated args
            response = function_return[0] # function output -> model ->
            additional_output = function_return[1]
            function = get_function_name(response)
        assistant_response = response.text

        return assistant_response
        
