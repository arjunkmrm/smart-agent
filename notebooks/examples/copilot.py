import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from examples.utils import PERSONA, AVAILABLE_FUNCTIONS, FUNCTIONS_SPEC, Smart_Agent, add_to_cache
import sys
import time
import random
import os
from pathlib import Path  
import json
with open('./user_profile.json') as f:
    user_profile = json.load(f)
functions = FUNCTIONS_SPEC.copy()
# functions[0]["parameters"]["properties"]["products"]["description"] = functions[0]["parameters"]["properties"]["products"]["description"].format(products=user_profile['products'])

agent = Smart_Agent(persona=PERSONA.format(username=user_profile['username']),functions_list=AVAILABLE_FUNCTIONS, functions_spec=functions, init_message=f"Hi {user_profile['username']}, this is Maya, technical specialist, what can I do for you?")

st.set_page_config(layout="wide",page_title="Enterprise Copilot- A demo of Copilot application using GPT")
styl = f"""
<style>
    .stTextInput {{
      position: fixed;
      bottom: 3rem;
    }}
</style>
"""
st.markdown(styl, unsafe_allow_html=True)


MAX_HIST= 5
# Sidebar contents
with st.sidebar:
    st.title('Tech Copilot')
    st.markdown('''
    This is a demo of Copilot Concept for Enterprise Networking Technical Support.

    ''')
    add_vertical_space(5)
    st.write('Created by James N')
    if st.button('Clear Chat'):

        if 'history' in st.session_state:
            st.session_state['history'] = []

    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'input' not in st.session_state:
        st.session_state['input'] = ""


user_input= st.chat_input("You:")

## Conditional display of AI generated responses as a function of user provided prompts
history = st.session_state['history']
      
if len(history) > 0:
    for message in history:
        message = dict(message)
        if message.get("role") != "system" and message.get("role") != "tool" and message.get("name") is None and len(message.get("content")) > 0:
            with st.chat_message(message["role"]):
                    st.markdown(message["content"])
else:
    history, agent_response = agent.run(user_input=None)
    with st.chat_message("assistant"):
        st.markdown(agent_response)
    user_history=[]
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    query_used, history, agent_response = agent.run(user_input=user_input, conversation=history)
    with st.chat_message("assistant"):
        st.markdown(agent_response)

st.session_state['history'] = history