# from ada_genai.vertexai import (
#     Content,
#     FunctionDeclaration,
#     GenerativeModel,
#     Part,
#     Tool,
# )
# from ada_genai.vertexai import TextEmbeddingModel
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerativeModel,
    Part,
    Tool,
)
from vertexai.language_models import TextEmbeddingModel
import re
import sqlite3
import pandas as pd
import os
import ast
from stop_words import STOP_WORDS
from dotenv import load_dotenv
import textract
load_dotenv()
from prompts import GENERATE_SQL_PROMPT
SQL_INVALID_RESPONSE = "sql_invalid"
EMPTY_TABLE = "empty_table"

euroclear_assistant_func = FunctionDeclaration(
    name="euroclear_assistant",
    description="an assistant who answers your questions about euroclear (ec)",
    parameters={
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "user query"
        },
    },
         "required": [
            "query"
      ]
  },
)

sop_assistant_func = FunctionDeclaration(
    name="sop_assistant",
    description="an assistant who answers your questions about standard operating procedures (sops)",
    parameters={
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "user query"
        },
    },
         "required": [
            "query"
      ]
  },
)

portions_assistant_func = FunctionDeclaration(
    name="portions_assistant",
    description="an assistant who answers your questions about making magical portions",
    parameters={
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "user query"
        },
    },
         "required": [
            "query"
      ]
  },
)

trade_query_func = FunctionDeclaration(
    name="trade_query_assistant",
    description="an assistant who answers your questions about the current bond trades and their details", # can add more
    parameters={
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "user query"
        },
    },
         "required": [
            "query"
      ]
  },
)

draft_email_func = FunctionDeclaration(
    name="email_assistant",
    description="an assistant who helps you draft emails", # can add more
    parameters={
    "type": "object",
    "properties": {
        "subject": {
            "type": "string",
            "description": "subject for the email"
        },
        "body": {
            "type": "string",
            "description": "mail body for the email"
        },
        "to_recipients": {
            "type": "string",
            "description": "the to receipients of the email"
        },
    },
         "required": [
            "subject",
            "body",
            "to_recipients",
      ]
  },
)

convert_sgt_func = FunctionDeclaration(
    name="sgt_assistant",
    description="an assistant to help you convert time from other market time zones to sgt", # can add more
    parameters={
    "type": "object",
    "properties": {
        "market": {
            "type": "string",
            "description": "market code. Note for euroclear it is CEST e.g. CEST, NYSE, HSE"
        },
        "time": {
            "type": "string",
            "description": "the time that has to be converted in the format: %H:%M"
        },
    },
         "required": [
            "market",
            "time",
      ]
  },
)

# add trade query to agent tools
# clean up model response before passing, maybe simple regex to very sql-ness, if not regen?
master_tools = Tool(
  function_declarations=[euroclear_assistant_func, sop_assistant_func, portions_assistant_func, trade_query_func, draft_email_func, convert_sgt_func],
)

knowledge_tools = Tool( 
    function_declarations=[euroclear_assistant_func],
)

from openai import OpenAI
client = OpenAI()

def chat_openai(prompt):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are an assistant who help answer user's question based on given inormation."},
        {"role": "user", "content": f"{prompt}"}
    ]
    )

    return completion.choices[0].message.content

def df_to_str(search_df):
    result_string = ""
    for idx, row in enumerate(search_df.iterrows()):  
        # Access row data correctly
        doc_title = row[1]['title']
        doc_content = row[1]['content']
        # Append document number and details to the result string
        result_string += f"\nDocument Number: {idx + 1}\nDocument Title: {doc_title}\n\nContent:\n{doc_content}\nEnd of document.\n"

    return result_string

def generate_vertex_embedding(text) -> list:
    """
    Generates an embedding vector string for the given text
    """
    model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
    embeddings = model.get_embeddings([text])[0]
    # for embedding in embeddings:
    vector = embeddings.values

    return vector 

def get_sql_query(response):
    # get function arguments
    model = GenerativeModel("gemini-pro")
    function_args = response.candidates[0].content.parts[0].function_call.args
    user_query = function_args["query"]

    # full prompt
    pre_prompt = f"{GENERATE_SQL_PROMPT}"
    post_prompt = f"""\n
    Now let's attend to the user query.\n
    user query: "{user_query}"\n
    sql query:
    """
    prompt = pre_prompt + post_prompt
    # instruct the model to generate content using the Tool that you just created:
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0}
    )
    # model answer
    answer = response.text
    print(answer)
    return answer

def verify_sql(text):
    # Attempt to find a SQL command within the text
    match = re.search(r"(SELECT|INSERT|UPDATE|DELETE)\s", text, re.IGNORECASE)
    if match:
        # Extract the SQL query starting from the found command
        start_pos = match.start()
        extracted_query = text[start_pos:]

        # You might want to apply further cleaning/validation on `extracted_query`
        # For example, removing comments (as done in the previous example)
        clean_query = re.sub(r"--.*?\n", "", extracted_query)  # Removes single-line comments
        clean_query = re.sub(r"/\*.*?\*/", "", clean_query, flags=re.DOTALL)  # Removes block comments

        return clean_query
    else:
        return SQL_INVALID_RESPONSE
        # raise ValueError("No valid SQL command found in text.")

def get_keywords(self, document, asynchronous = False) -> str:
    """ given a document, extract keywords sync or across chunks async"""
    model = GenerativeModel("gemini-pro")
    # pre-prompt
    pre_inst = f"You are a helpful assistant who extracts all relevant keywords from a given document. Make sure to not miss out any keyword."
    # post-prompt
    post_inst = """Do not give any comment. Just directly output the keywords from the document. \n Keywords:"""

    # full prompt
    prompt = f"{pre_inst}\n{document}\n{post_inst}"

    # instruct the model to generate content using the Tool that you just created:
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0}
    )
    # model answer
    answer = response.text
    return answer


def tokenise(text_list):
    # re-check this one - keep numbers, certain numbers
    """
    Tokenizes and cleans the provided list of text documents.
    """
    return [[word for word in re.sub(r'\W+|\d+', ' ', text.lower()).split() if word not in STOP_WORDS] for text in text_list]


def docstodf(folder_path, collection_name):
    """
    Takes markdown (.md) and Word documents (.docx, .doc) in a given folder path
    and creates a dataframe with columns - file_path, content, title (from file name).
    Note: if csv file already exists in path with collection name, that file is used instead.
    """
    data = []
    script_path = os.path.abspath(__file__)  # Make sure this script is part of a file for __file__ to work
    script_directory = os.path.dirname(script_path)
    csv_path = os.path.join(script_directory, 'data', f'{collection_name}.csv')
    print(csv_path)

    if not os.path.exists(csv_path):
        print("creating csv")
        for idx, filename in enumerate(os.listdir(folder_path)):
            if filename.endswith((".md", ".docx", ".doc")):  # Check if file ends with any of the document formats
                file_path = os.path.join(folder_path, filename)
                # Use textract to read file content
                try:
                    content = textract.process(file_path).decode('utf-8')
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
                    continue  # Skip this file if there's an error processing it

                title = os.path.splitext(filename)[0]

                # Append to the data list
                data.append({
                    "id": idx + 1,
                    "file_path": file_path,
                    "title": title,
                    "content": content,
                    # "vector_id": idx  
                })

        # Create a DataFrame and save to CSV
        articles_df = pd.DataFrame(data)
        articles_df['id'] = articles_df['id'].apply(str)
        articles_df.to_csv(csv_path, index=False)
        print(f"{collection_name}.csv created and saved")
    else:
        print(f"{collection_name}.csv already present")
        # Load DataFrame from CSV
        articles_df = pd.read_csv(csv_path)
        articles_df['id'] = articles_df['id'].astype(str)
        # Optional processing if 'content_vector' exists
        # if 'content_vector' in articles_df.columns:
        #     articles_df['content_vector'] = articles_df['content_vector'].apply(ast.literal_eval)

    return articles_df


def sql_to_df(sql_query, db_name="C:\\Users\\arjunkumarm\\OneDrive - DBS Bank Ltd\\Documents\\Fixed-Income-Products\\llm-experiments\\gemini-agent\\data\\trade_report.db"):
    # i could also just get the sql query and then pass it back, to convert to df and showing later in the chat directly
    # Connect to the SQLite database

    conn = sqlite3.connect(db_name)
    
    # Execute the query and convert the results to a DataFrame
    df = pd.read_sql_query(sql_query, conn)
    
    # Close the connection
    conn.close()

    
    return df

def get_function_name(response) -> str:
    """
    simple functon to get function name from gemini response
    """
    function_name = response.candidates[0].content.parts[0].function_call.name
    return function_name

def get_function_args(response) -> str:
    """
    simple functon to get function name from gemini response
    """
    function_args = response.candidates[0].content.parts[0].function_call.args
    return function_args


# for fuzzy search
def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]
