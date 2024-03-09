# goal is to eventually abstract out the knowledge functions
# add func router here also?
import sqlite3
import pandas as pd
# import win32com.client as win32
# from ada_genai.vertexai import (
#     GenerativeModel,
# )
from vertexai.generative_models import (
    GenerativeModel,
)
from datetime import datetime
import pytz
from search_engine import BM25
from prompts import GENERATE_SQL_PROMPT
from utils import get_sql_query, get_function_args
from utils import verify_sql
from typing import Tuple
from utils import SQL_INVALID_RESPONSE
from utils import EMPTY_TABLE
from utils import docstodf, chat_openai
from dotenv import load_dotenv
load_dotenv()
# extra

# for each function - return two outs - one direct string and another optional out?
# functions to get function call from model and return answer

# what if each knowledge store is just an instance of this class? likewise for structured query?
# get respone and answer
class KnowledgeStores:
    """
    a class which can be used to initialise knowledge agents
    """
    def __init__(self, document_path, collection_name, k = 3) -> None:
        self.document_df = docstodf(document_path, collection_name)
        self.ec_store = BM25(self.document_df)
        self.ec_store.fit()
        self.k = k

    def knowledge_assistant(self, response: str) -> Tuple:
        """
        This is basically a simple RAG function which generates answer based on
        given user query.
        """
        # get function arguments
        model = GenerativeModel("gemini-pro")
        function_args = response.candidates[0].content.parts[0].function_call.args
        query = function_args["query"]
        # search ec store
        search_result = self.ec_store.query(query, self.k)
        print(search_result[:15])

        # pre-prompt
        # pre_inst = f"Use only the given source of information to answer the user's question: {query}"
        pre_inst = f"Use the given source of information to answer the user's question: {query}"
        # post-prompt
        post_inst = """\nTips:\n1. Make the most of the information provided to give a detailed, succinct and concise answer to the user \n
        2. If you need more clarification from the user, please ask\n
        3. Output in neat markdown format with web links if present in the document"""
        # 3. DO NOT MAKE UP OWN ANSWERS, strictly answer from the given source of information

        # full prompt
        prompt = f"{pre_inst}\n{search_result}\n{post_inst}"

        # instruct the model to generate content using the Tool that you just created:
        # response = model.generate_content(
        #     prompt,
        #     generation_config={"temperature": 0}
        # )
        response = chat_openai(prompt)

        # model answer
        #answer = response.text # for gemini
        answer = response
        print(answer)
        return (answer, None)

# create a class for strutured queries like above **************** 
# this could be made gen purpose, just change prompt based on data, make this a class after experimentation
# structured data retriever
def trade_query_assistant(response: str, db_name="C:\\Users\\arjunkumarm\\OneDrive - DBS Bank Ltd\\Documents\\Fixed-Income-Products\\llm-experiments\\gemini-agent\\data\\trade_report.db"):
    query = get_sql_query(response)
    print(query)
    sql_query = verify_sql(query)
    print('verified')
    # Connect to the SQLite database
    print("connecting to db")
    conn = sqlite3.connect(db_name)

    if sql_query == SQL_INVALID_RESPONSE:
        return ("Sorry there's an error with the connection. Please try again later?", SQL_INVALID_RESPONSE)
    else:
        # Execute the query and convert the results to a DataFrame
        df = pd.read_sql_query(sql_query, conn)
        if df.empty:
            return (f"Here is the sql query I generated {sql_query}. Either the question is too generic or there is no data for the request", EMPTY_TABLE)
        else:
            conn.close()
            df = df[:3] # return only top 3 rows
            
            json_string = df.to_json(orient='records') # convert df to json string
            # add only top three to json string here only
            return (json_string, sql_query)


# draft email
# agent passes required stuff to mail assistant
# can try direct agent calling without llm -> llm -> output
def email_assistant(response):
    # Connect to Outlook
    function_args = response.candidates[0].content.parts[0].function_call.args
    subject = function_args['subject']
    body = function_args['body']
    to_recipients = function_args['to_recipients']

    # outlook = win32.Dispatch('outlook.application')
    # mail = outlook.CreateItem(0)  # 0 is the code for a mail item
    # subject, body, to_recipients
    # # Set the mail content
    # mail.Subject = subject
    # mail.Body = body
    # mail.To = to_recipients  # Recipient emails separated by ";"
    #mail.CC = cc_recipients  # CC emails separated by ";"
    
    # Save the email in the drafts folder
    # mail.Save()
    return("Email created in drafts.", None)


# convert times to sgt
def sgt_assistant(response):
    function_args = get_function_args(response)
    # Define the market time zones and Singapore time zone
    time = function_args["time"]
    market = function_args["market"]
    market_timezones = {
        'NYSE': 'US/Eastern',  # Adjusts for EST/EDT automatically
        'LSE': 'Europe/London',  # Adjusts for GMT/BST automatically
        'TSE': 'Asia/Tokyo',
        'HKEX': 'Asia/Hong_Kong',
        'CEST': 'Europe/Berlin',
    }
    singapore_timezone = pytz.timezone('Asia/Singapore')
    
    # Use the current date as a placeholder
    today = datetime.now().date()
    datetime_str = f"{today} {time}"  # Combine current date with the input time

    # Parse the combined date and time
    input_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
    
    # Convert to the market's timezone
    market_timezone = pytz.timezone(market_timezones[market])
    market_datetime = market_timezone.localize(input_datetime)
    
    # Convert to Singapore time
    sg_datetime = market_datetime.astimezone(singapore_timezone)
    time_out = sg_datetime.strftime('%H:%M')
    print(f"time converted: {time_out}")
    return (time_out, None)

def action_planner(response):
    """
    think step
    """
    # get function arguments
    model = GenerativeModel("gemini-pro")
    function_args = response.candidates[0].content.parts[0].function_call.args
    task = function_args["task"]

    pre_inst = f"Think crtitically and plan a course of action for this task: {task}"
    # post-prompt
    post_inst = """\n"""
    # full prompt
    prompt = f"{pre_inst}\n{post_inst}"

    # instruct the model to generate content using the Tool that you just created:
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0}
    )
    # model answer
    answer = response.text
    print(answer)
    return answer