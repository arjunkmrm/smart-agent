# note: for the demo, i could probably send emails to myself and store in a folder to get into df 
from dotenv import load_dotenv
from utils import get_function_name, get_function_args
import streamlit as st
from utils import master_tools
from utils import sql_to_df
from agent_functions import trade_query_assistant, email_assistant
import copy
from agent_functions import KnowledgeStores
# from ada_genai.vertexai import (
#     GenerativeModel,
#     Part
# )
from vertexai.generative_models import (
    GenerativeModel,
    Part
)
from prompts import GENERAL_ASSISTANT
#import win32com.client as win32
load_dotenv()

class AgentUno:
    def __init__(self, function_dict, agent_tools) -> None:
        model = GenerativeModel("gemini-pro") # initialise model
        self.chat = model.start_chat(response_validation=False)
        self.chat.send_message(f"{GENERAL_ASSISTANT}")
        self.chat_history = []
        self.sources = []
        self.function_dict = function_dict
        self.agent_tools = agent_tools

    def call_func(self, response): # routes to different functions based on call
        """ route agent response to functions """
        agent_function_call = get_function_name(response) # get the name of agent function
        if agent_function_call: # get corresponding function to agent function call
            handler_function = self.function_dict.get(agent_function_call) #getattr(self, handler_method_name)
            function_outputs = handler_function(response)
            function_response = function_outputs[0]
            additional_response = function_outputs[1]
            model_response = self.push_response(agent_function_call, function_response)
            return (model_response, additional_response)  # dynamic function calling
        else:
            # get better exception handling
            #st.error(f"Unknown function call: {agent_function_call}")
            return None
        
    def push_response(self, function_name, prompt):
        # could technically append prompt - "whenever you need to use tools, please call the action_planner first to get a plan for how to execute the task"
        # or i send the response to action planner util, whose response is appended 
        # specific trade action could be a function in itself
        response = self.chat.send_message(
            Part.from_function_response(
                name=function_name,
                response={"content": prompt},
            ),
            tools=[self.agent_tools]
        )
        #print(prompt)
        return response
    
    def get_func(self, user_query): # get the function which agent wants to call
        response = self.chat.send_message(f"{user_query}", tools=[self.agent_tools]) # send user message
        self.chat_history.append({"role":"human", "content":user_query}) # append user query to history
        function_call = response.candidates[0].content.parts[0].function_call.name # get function call
        if not function_call: # if not a function call, just append agent response
            pass
        return response
    
    def execute_task(self, task):
        response = self.get_func(task)
        function = get_function_name(response)
        while function:
            print(f"calling {function}...")
            args = get_function_args(response)
            print(args['query'])
            function_return = self.call_func(response) # call the agent determined function using agent generated args
            response = function_return[0] # function output -> model ->
            additional_output = function_return[1]
            function = get_function_name(response)
        assistant_response = response.text

        return assistant_response
        
