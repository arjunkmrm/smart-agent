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
from prompts import GENERATE_SQL_PROMPT
SQL_INVALID_RESPONSE = "sql_invalid"
EMPTY_TABLE = "empty_table"

search_knowledge_func = FunctionDeclaration(
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

email_draft_func = FunctionDeclaration(
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

# add trade query to agent tools
# clean up model response before passing, maybe simple regex to very sql-ness, if not regen?
master_tools = Tool(
  function_declarations=[search_knowledge_func, trade_query_func, email_draft_func],
)

knowledge_tools = Tool( 
    function_declarations=[search_knowledge_func],
)

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
    """ takes markdown (.md) files in a given folder path and creates a dataframe with columns - file_path, content, title (from file name) """
    data = []
    script_path = os.path.abspath(__file__)
    script_directory = os.path.dirname(script_path)
    csv_path = os.path.join(script_directory, 'data', f'{collection_name}.csv')
    print(csv_path)

    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        print("creating csv")
        # add word document reading < ----------------------------------------------------
        for idx, filename in enumerate(os.listdir(folder_path)):
            if filename.endswith(".md"):
                file_path = os.path.join(folder_path, filename)
                # Properly using 'with' to open files ensures they are closed correctly
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    title = os.path.splitext(filename)[0]

                    # Append to the data list
                    data.append({
                        "id": idx + 1,
                        "file_path": file_path,
                        "title": title,
                        "content": content,
                        #"vector_id": idx  
                    })

        # Create a DataFrame and save to CSV
        articles_df = pd.DataFrame(data)
        articles_df['id'] = articles_df['id'].apply(str)
        articles_df.to_csv(csv_path, index=False)
    else:
        print("csv present")
        # Load DataFrame from CSV
        articles_df = pd.read_csv(csv_path)
        articles_df['id'] = articles_df['id'].astype(str)
        # articles_df['vector_id'] = articles_df['vector_id'].apply(str)
        if 'content_vector' in articles_df.columns:
            articles_df['content_vector'] = articles_df['content_vector'].apply(ast.literal_eval)

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
