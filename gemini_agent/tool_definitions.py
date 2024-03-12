from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerativeModel,
    Part,
    Tool,
)
from vertexai.language_models import TextEmbeddingModel
import pandas as pd
from utilities.stop_words import STOP_WORDS
from dotenv import load_dotenv
# import textract
# from ada_genai.vertexai import (
#     Content,
#     FunctionDeclaration,
#     GenerativeModel,
#     Part,
#     Tool,
# )
# from ada_genai.vertexai import TextEmbeddingModel
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

swift_query_func = FunctionDeclaration(
    name="trade_query_assistant",
    description="an assistant who finds SWIFT trade message templates for you", # can add more
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

master_tools = Tool(
  function_declarations=[euroclear_assistant_func, sop_assistant_func, portions_assistant_func, trade_query_func, swift_query_func, draft_email_func, convert_sgt_func],
)