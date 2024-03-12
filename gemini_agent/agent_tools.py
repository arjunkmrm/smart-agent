# goal is to eventually abstract out the knowledge functions
# add func router here also?
import sqlite3
import pandas as pd
from vertexai.generative_models import (
    GenerativeModel,
)
from datetime import datetime
import pytz
from utilities.search_engine import BM25
from prompts import GENERATE_SQL_PROMPT
from utilities.utils import (
    get_sql_query, 
    get_function_args, 
    verify_sql, 
    SQL_INVALID_RESPONSE, 
    EMPTY_TABLE, 
    docstodf, 
    chat_claude,
    #chat_openai
    )
from typing import Tuple
from dotenv import load_dotenv
# import win32com.client as win32
# import pythoncom
# from ada_genai.vertexai import (
#     GenerativeModel,
# )
load_dotenv()

# get respone and answer
class KnowledgeStores:
    """
    a class which can be used to initialise knowledge agents
    """
    def __init__(self, document_path, collection_name, k = 3) -> None:
        self.document_df = docstodf(document_path, collection_name)
        self.store = BM25(self.document_df)
        self.store.fit()
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
        search_result = self.store.query(query, self.k)
        #print(search_result[:15])

        # pre-prompt
        # pre_inst = f"Use only the given source of information to answer the user's question: {query}"
        pre_inst = f"Use the given source of information to answer the user's question: {query}"
        # post-prompt
        post_inst = """\nTips:\n1. Make the most of the information provided to give a detailed, concise and succinct answer to the user \n
        2. If you need more clarification from the user, please ask\n
        3. If there is not enough information to answer the question correctly, please say that you don't have enough information.
        4. Use lists and bullets whenever appropriate
        5. Output in neat markdown format with web links if present in the document"""
        # 3. DO NOT MAKE UP OWN ANSWERS, strictly answer from the given source of information

        # full prompt
        prompt = f"{pre_inst}\n{search_result}\n{post_inst}"

        # instruct the model to generate content using the Tool that you just created:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0}
        )
        # response = chat_openai(prompt)
        # response = chat_claude(prompt)

        # model answer
        answer = response.text # for gemini
        #answer = response
        #print(answer)
        return (answer, None)
    
    def omni_search(self, response: str) -> Tuple:
        # async call to all stores
        pass


class TableStores:
    def __init__(self, db_name, db_prompt) -> None:
        self.db_name = db_name
        self.db_prompt = db_prompt

    def sql_query_assistant(self, response: str):
        query = get_sql_query(response, self.db_prompt)
        print(f"SQL query: {query}")
        sql_query = verify_sql(query)
        print('SQL query verified')
        # Connect to the SQLite database
        print("connecting to db")
        conn = sqlite3.connect(self.db_name)

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
                json_string = json_string + """\nNOTE: If there are more than three trades, only three are shown. The other trades have been sent to the user's display directly.""" # append directly
                # add only top three to json string here only
                return (json_string, sql_query)


# create a class for strutured queries like above **************** 
# this could be made gen purpose, just change prompt based on data, make this a class after experimentation
# structured data retriever
def trade_query_assistant(response: str, db_name="C:\\Users\\arjunkumarm\\OneDrive - DBS Bank Ltd\\Documents\\Fixed-Income-Products\\llm-experiments\\gemini-agent\\data\\trade_report.db"):
    query = get_sql_query(response, GENERATE_SQL_PROMPT)
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
            json_string = json_string + """\nNOTE: If there are more than three trades, only three are shown. The other trades have been sent to the user's display directly.""" # append directly
            # add only top three to json string here only
            return (json_string, sql_query)


# draft email
# agent passes required stuff to mail assistant
# can try direct agent calling without llm -> llm -> output



def email_assistant(response):
    try:
        # Connect to Outlook
        # pythoncom.CoInitialize()
        function_args = response.candidates[0].content.parts[0].function_call.args
        subject = function_args['subject']
        body = function_args['body']
        to_recipients = function_args['to_recipients']

        # outlook = win32.Dispatch('outlook.application')
        # mail = outlook.CreateItem(0)  # 0 is the code for a mail item

        # # Set the mail content
        # mail.Subject = subject
        # mail.Body = body
        # mail.To = to_recipients  # Recipient emails separated by ";"
        # # Optional: Add CC recipients if needed
        # # mail.CC = cc_recipients

        # mail.Display()
        # # Send the email
        # #mail.Send()
        # # Uninitialize the COM library
        # pythoncom.CoUninitialize()
        return ("Email drafted.", None)
    except Exception as e:
        return (f"Failed to create email in drafts. {str(e)}", str(e))



# convert times to sgt
def sgt_assistant(response):
    try:
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
    except Exception as e:
        return (f"Failed to convert time. Error: {str(e)}", str(e))

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
