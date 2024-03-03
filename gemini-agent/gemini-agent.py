import os
import time
from dotenv import load_dotenv
import streamlit as st
import random
from vectorengine import VectorEngine
from utils import agent_tools
from prompts import GENERAL_ASSISTANT
import copy
from agentfunctions import KnowledgeStores
from vertexai.preview.generative_models import (
    Content,
    FunctionDeclaration,
    GenerativeModel,
    Part,
    Tool,
)

load_dotenv()
# Constants
EUROCLEAR_ASSISTANT = "euroclear_assistant"

FUNCTION_TEXT = {
    EUROCLEAR_ASSISTANT: "Searching euroclear knowledge"
}

class SmartAgent:
    def __init__(self) -> None:
        self.chat_history = []
        self.sources = []

    def call_func(self, response, function_dict): # routes to different functions based on call
        """ route agent response to functions """
        agent_function_call = response.candidates[0].content.parts[0].function_call.name # get the name of agent function
        if agent_function_call: # get corresponding function to agent function call
            handler_function = function_dict.get(agent_function_call) #getattr(self, handler_method_name)
            function_response = handler_function(response)
            next_response = self.push_response(agent_function_call, function_response)
            return next_response # dynamic function calling
        else:
            # Log or handle unknown function_call
            # better exception handling
            st.error(f"Unknown function call: {agent_function_call}")
            return None
        
    def push_response(self, function_name, prompt):
        if function_name == EUROCLEAR_ASSISTANT:
            prompt = prompt + f"\n PRO-TIP: if the answer is not sufficient do not give up. please call the {EUROCLEAR_ASSISTANT} function again, with a modified query"
        response = st.session_state.chat.send_message(
            Part.from_function_response(
                name=function_name,
                response={"content": prompt},
            ),
            tools=[agent_tools]
        )
        print(prompt)
        return response
    
    def get_func(self, user_query): # get the function which agent wants to call
        response = st.session_state.chat.send_message(f"{user_query}", tools=[agent_tools]) # send user message
        st.session_state.chat_history.append({"role":"human", "content":user_query}) # append user query to history
        function_call = response.candidates[0].content.parts[0].function_call.name # get function call
        if not function_call: # if not a function call, just append agent response
            pass
        return (function_call, response)
        
def main():
    st.title("SageBot")
    model = GenerativeModel("gemini-pro")

    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(response_validation=False)
        st.session_state.chat.send_message(f"{GENERAL_ASSISTANT}")
        st.session_state.sagebot = SmartAgent() # init agent
        st.session_state.knowledge_stores = KnowledgeStores(1) # init stores
        st.session_state.chat_history = [] # chat history for display
    st.session_state.sources = []

    FUNCTION_DICT = {
        EUROCLEAR_ASSISTANT: st.session_state.knowledge_stores.euroclear_assistant
    }

    #chat_messages = st.session_state.chat_history
    #st.write(st.session_state.chat_history)
    chat_messages = copy.deepcopy(st.session_state.chat_history)
    for message in chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # user input
    if prompt := st.chat_input("What is up?"):
        with st.chat_message("user"): # display user message in chat message container
            st.markdown(prompt)

        function_call = st.session_state.sagebot.get_func(prompt) # get the function call from agent
        function = function_call[0] # function to call
        response = function_call[1] # full response

        i = 0
        while function: # loop for multiple function calling
            values = []
            function_args = response.candidates[0].content.parts[0].function_call.args
            values = []
            for arg in function_args:
                values.append(function_args[arg])

            query_string = ', '.join(values)
            with st.spinner(f'{FUNCTION_TEXT.get(function)}: {query_string}'): # get function queries
                response = st.session_state.sagebot.call_func(response, FUNCTION_DICT) # call the right function
                if not response: break
                function = response.candidates[0].content.parts[0].function_call.name
        
        assistant_response = response.text # get final response after function calls end
        st.session_state.chat_history.append({"role":"assistant", "content":assistant_response})
        
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

if __name__ == "__main__":
    main()


