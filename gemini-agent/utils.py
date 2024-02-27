from vertexai import generative_models
from vertexai.generative_models import GenerativeModel
from vertexai.preview.generative_models import FunctionDeclaration
model = GenerativeModel("gemini-pro")

search_knowledge_func = FunctionDeclaration(
    name="search_knowledge",
    description="to answer any question related to euroclear",
    parameters={
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "your rephrased search query to retrieve knowledge from a vector database"
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