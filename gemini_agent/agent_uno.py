# note: for the demo, i could probably send emails to myself and store in a folder to get into df 
# master agent for use with streamlit
from dotenv import load_dotenv
from utilities.utils import get_function_name
import streamlit as st
from prompts import GENERAL_ASSISTANT
from agent_tools import KnowledgeStores
from vertexai.generative_models import (
    GenerativeModel,
    Part
)
# import win32com.client as win32
# from ada_genai.vertexai import (
#     GenerativeModel,
#     Part
# )
load_dotenv()

class SmartAgent:
    def __init__(self, function_dict, agent_tools) -> None:
        # test cleaner abstract for agents 
        self.model = GenerativeModel("gemini-pro") # initialise model # set temperature!!!******************
        self.chat = self.model.start_chat(response_validation=False)
        self.chat_history = []
        self.sources = []
        self.function_dict = function_dict
        self.agent_tools = agent_tools

    def call_func(self, response): # routes to different functions based on call
        """ route agent response to functions """
        agent_function_call = get_function_name(response) # get the name of agent function
        print(agent_function_call)
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
        # self.chat_history.append({"role":"human", "content":user_query}) # append user query to history
        function_call = get_function_name(response) # get function call
        if not function_call: # if not a function call, just append agent response
            pass
        return response
    
    def execute_task(self, task):
        response = self.get_func(task)
        function = get_function_name(response)
        while function:
            function_return = self.call_func(response, self.function_dict) # call the agent determined function using agent generated args
            response = function_return[0] # function output -> model ->
            additional_output = function_return[1]
            function = get_function_name(response)
        assistant_response = response.text

        return assistant_response