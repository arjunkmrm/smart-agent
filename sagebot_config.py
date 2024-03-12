import os

# Constants
EUROCLEAR_ASSISTANT = "euroclear_assistant"
SOP_ASSISTANT = "sop_assistant"
TRADE_QUERY_ASSISTANT = "trade_query_assistant"
SWIFT_QUERY_ASSISTANT = "swift_query_assistant"
EMAIL_ASSISTANT = "email_assistant"
SGT_ASSISTANT = "sgt_assistant"
KNOWLEDGE_ASSISTANT = "knowledge_assistant"

# function loading texts
FUNCTION_TEXT = {
    EUROCLEAR_ASSISTANT: "Searching euroclear",
    SOP_ASSISTANT: "Searching SOPs",
    TRADE_QUERY_ASSISTANT: "Searching trades",
    SWIFT_QUERY_ASSISTANT: "Searching templates",
    EMAIL_ASSISTANT: "Drafting email",
    SGT_ASSISTANT: "Converting time",
    KNOWLEDGE_ASSISTANT: "Asking knowledge assistant"
}

# Get the absolute path to the directory containing your script
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
doc_path = os.path.join(parent_dir, 'docs\\sop-docs\\')

# these can be moved to config
# path for functions
EUROCLEAR_PATH = os.path.join(doc_path, "euroclear") # folder containing euroclear documents
EUROCLEAR_COLLECTION = "ec_docs"
SOP_PATH = os.path.join(doc_path, "bonds_docs") # bond sop documents
SOP_COLLECTION = "bonds_docs"
TRADE_REPORT_DB = os.path.join(script_dir, "utilities\\data\\trade_report.db") # trade report sql db
SWIFT_DB = os.path.join(script_dir, "utilities\\data\\swift_templates.db") # swift templates db