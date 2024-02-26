import os
import time
from dotenv import load_dotenv
import streamlit as st
import random
from vertexai.preview.generative_models import (
    Content,
    FunctionDeclaration,
    GenerativeModel,
    Part,
    Tool,
)
from vectorengine import VectorEngine
from utils import search_tool
from prompts import GENERAL_ASSISTANT
import copy
load_dotenv()

# Constants
SEARCH_KNOWLEDGE = "search_knowledge"
CMU_QUERY = "cmu_query"
EMAIL_QUERY = "email_query"
TRADE_QUERY = "trade_query"
FUNCTION_HANDLERS = {
    SEARCH_KNOWLEDGE: "handle_ec_knowledge",
    CMU_QUERY: "handle_cmu_query",
    EMAIL_QUERY: "handle_email_query",
    TRADE_QUERY: "handle_trade_query",
}

class SmartAgent:
    def __init__(self) -> None:
        self.ec_store = VectorEngine("docs/sop-docs/euroclear", "ec_sop")
        self.chat_history = []
        self.sources = []

    def func_router(self, response):
        function_call = response.candidates[0].content.parts[0].function_call.name
        handler_method_name = FUNCTION_HANDLERS.get(function_call)

        if handler_method_name:
            handler_method = getattr(self, handler_method_name)
            return handler_method(response)
        else:
            # Log or handle unknown function_call
            st.error(f"Unknown function call: {function_call}")
            return None

    def handle_ec_knowledge(self, response):
        # get function arguments
        function_args = response.candidates[0].content.parts[0].function_call.args
        # get query
        query = function_args["query"]
        # search ec store
        search_result = self.ec_store.query(query, 3)
        st.session_state.sources.append({"source": search_result})
        pre_inst = "Kindly use only the given source of information to answer the user's question:"
        post_inst = """Tips:\n 1. Please directly quote the specific part of text directly relevant to the user's question and answer. \n
        2. Thoroughly search the given source of information to answer the question before answering that the information is not found.\n
        3. If you need more information, you can use can make another query using the search function.\n
        4. DO NOT MAKE UP OWN ANSWERS, strictly answer from the given source of information"""
        prompt = f"{pre_inst}\n{search_result}\n{post_inst}"
        # send response
        return self._send_response(SEARCH_KNOWLEDGE, prompt)

    def handle_cmu_query(self, response):
        function_args = response.candidates[0].content.parts[0].function_call.args
        isin = function_args["isin"]
        content = {
            "cmu_isin": f"{isin}",
            "cmu_issuer_name": "CHINA DEVELOPMENT BANK",
            "cmu_issuer_description": "06 CHINA DEVELOPMENT BANK BOND 03",
            "issue_date": "2006-04-11",
            "maturity_date": "2026-04-11",
            "issue_cury": "CNY",
            "issue_size": "25000000000",
            "coupon_rate": "3.6",
            "coupon_frequency": "Semi-annually",
        }
        return self._send_response(CMU_QUERY, content)

    def handle_email_query(self, response):
        function_args = response.candidates[0].content.parts[0].function_call.args
        reference = function_args["reference"]
        content = f"Hi Team, we are facing EC 92415 for the deal {reference}. Please confirm if it's right."
        return self._send_response(EMAIL_QUERY, content)

    def handle_trade_query(self, response):
        function_args = response.candidates[0].content.parts[0].function_call.args
        reference = function_args["reference"]
        content = f"{reference}, place of settlement: EC 92416."
        return self._send_response(TRADE_QUERY, content)

    def _send_response(self, function_name, prompt):
        # This method assumes the existence of a properly initialized st.session_state.chat
        return st.session_state.chat.send_message(
            Part.from_function_response(
                name=function_name,
                response={"content": prompt},
            ),
            tools=[search_tool]
        )
    
    def get_func(self, user_query):
        # if "chat" not in st.session_state:
        #     # send general instructions to the agent
        #     st.session_state.chat.send_message(f"{GENERAL_ASSISTANT}")
        # send user query
        response = st.session_state.chat.send_message(f"{user_query}", tools=[search_tool])
        # append user query to history
        st.session_state.chat_history.append({"role":"human", "content":user_query})
        # get function call
        function_call = response.candidates[0].content.parts[0].function_call.name
        if not function_call:
            st.session_state.chat_history.append({"role":"assistant", "content":response.text})
        return (function_call, response)
    
    def tool_chat(self, response = None, function_call = None):
        #function_call = self.get_func(user_query)
        # if any function call 
        while function_call:
            # add func call to chat history
            # self.chat_history.append({"role":"assistant", "content":function_call})
            # route to appropriate function and get response
            response = self.func_router(response)
            if not response: break
            function_call = response.candidates[0].content.parts[0].function_call.name # see if there is an additional function call
        # add response to chat history
        st.session_state.chat_history.append({"role":"assistant", "content":response.text})
        return response


    # def agent_chat(self, user_query):
    #     # send general instructions to the agent
    #     # if "chat" not in st.session_state:
    #     #     st.session_state.chat.send_message(f"{GENERAL_ASSISTANT}")
    #     # send user query
    #     response = st.session_state.chat.send_message(f"{user_query}", tools=[search_tool])
    #     # append user query to history
    #     self.chat_history.append({"role":"human", "content":user_query})
    #     # get function call
    #     function_call = response.candidates[0].content.parts[0].function_call.name
        
    #     # if any function call 
    #     while function_call:
    #         # add func call to chat history
    #         self.chat_history.append({"role":"assistant", "content":function_call})
    #         # route to appropriate function and get response
    #         response = self.func_router(response)
    #         if not response: break
    #         function_call = response.candidates[0].content.parts[0].function_call.name # see if there is an additional function call
    #     # add response to chat history
    #     self.chat_history.append({"role":"assistant", "content":response.text})
    #     return response

# def response_generator(bot, query):
#     output = bot.agent_chat(query)
#     response = output.text
#     for word in response.split():
#         yield word + " "
#         time.sleep(0.05)

# def extract_messages():
#     chat_message = []
#     for message in st.session_state.chat.history:
#         try:
#             if message.parts[0].text:
#                 chat_message.append({'role':message.role, 'content':message.parts[0].text})
#         except AttributeError:
#             if message.parts[0].function_call.name:
#                 chat_message.append({'role': message.role, 'content':message.parts[0].function_call.name})
#     return chat_message
        
def main():
    st.title("SageBot")
    model = GenerativeModel("gemini-pro")
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(response_validation=False)
        st.session_state.chat.send_message(f"{GENERAL_ASSISTANT}", tools=[search_tool])
        st.session_state.sagebot = SmartAgent()
        st.session_state.chat_history = []
    st.session_state.sources = []

    # Display chat messages from history on app rerun
    #chat_messages = st.session_state.chat_history
    #st.write(st.session_state.chat_history)
    chat_messages = copy.deepcopy(st.session_state.chat_history)
    for message in chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # user input
    if prompt := st.chat_input("What is up?"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        #with st.spinner('Thinking...'):
        func_out = st.session_state.sagebot.get_func(prompt)
        function = func_out[0]
        response = func_out[1]
        if function:
            with st.spinner('Searching...'):
                output = st.session_state.sagebot.tool_chat(response, function)
            #st.success('Done!')
            assistant_response = output.text
        else:
            assistant_response = response.text

        with st.chat_message("assistant"):
            st.markdown(assistant_response)
    #st.write(st.session_state.sources)

if __name__ == "__main__":
    main()