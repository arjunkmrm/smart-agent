# goal is to eventually abstract out the knowledge functions
# add func router here also?

from vertexai.preview.generative_models import (
    GenerativeModel
)
from vectorengine import VectorEngine

# Constants
EUROCLEAR_ASSISTANT = "euroclear_assistant"
CMU_QUERY = "cmu_query"
EMAIL_QUERY = "email_query"
TRADE_QUERY = "trade_query"

# Function handlers dict
FUNCTION_HANDLERS = {
    EUROCLEAR_ASSISTANT: "handle_ec_knowledge",
    CMU_QUERY: "handle_cmu_query",
    EMAIL_QUERY: "handle_email_query",
    TRADE_QUERY: "handle_trade_query",
}

# Function texts
FUNCTION_TEXT = {
    EUROCLEAR_ASSISTANT: "Searching euroclear knowledge...",
    EMAIL_QUERY: "Searching through emails...",
    TRADE_QUERY: "Searching bond trades"
}

# functions to get function call from model and return answer

# get respone and answer
class KnowledgeStores:
    def __init__(self, k = 3) -> None:
        self.ec_store = VectorEngine("docs/sop-docs/euroclear", "ec_sop")
        self.k = k

    def euroclear_assistant(self, response):
        """
        This is basically a simple RAG function which generates answer based on
        given user query.
        """
        # get function arguments
        model = GenerativeModel("gemini-pro")
        function_args = response.candidates[0].content.parts[0].function_call.args
        # get query
        # add error handling
        # if argument not found value error or something, return here and retry once? else
        # ask user to try again later
        query = function_args["query"]
        # search ec store
        search_result = self.ec_store.query(query, self.k)
        # print(search_result)

        # pre-prompt
        pre_inst = f"Use only the given source of information to answer the user's question: {query}"
        # post-prompt
        post_inst = """\nTips:\n1. Make the most of the information provided to give a detailed, succinct and concise answer to the user \n
        2. If you need more clarification from the user, please ask\n
        3. DO NOT MAKE UP OWN ANSWERS, strictly answer from the given source of information
        4. Output in neat markdown format with web links if present in the document"""
        # full prompt
        prompt = f"{pre_inst}\n{search_result}\n{post_inst}"

        # instruct the model to generate content using the Tool that you just created:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0}
        )
        # model answer
        answer = response.text
        print(answer)
        return answer


def handle_email_query(response):
    function_args = response.candidates[0].content.parts[0].function_call.args
    reference = function_args["reference"]
    content = f"Hi Team, we are facing EC 92415 for the deal {reference}. Please confirm if it's right."

    return (EMAIL_QUERY, content)


def handle_trade_query(response):
    function_args = response.candidates[0].content.parts[0].function_call.args
    reference = function_args["reference"]
    content = f"{reference}, place of settlement: EC 92416."

    return (TRADE_QUERY, content)
