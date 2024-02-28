from vertexai import generative_models
from vertexai.generative_models import GenerativeModel
from vertexai.preview.generative_models import FunctionDeclaration
model = GenerativeModel("gemini-pro")

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

search_tool = generative_models.Tool(
  function_declarations=[search_knowledge_func],
)