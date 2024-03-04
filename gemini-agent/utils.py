from vertexai import generative_models
from vertexai.generative_models import GenerativeModel
from vertexai.preview.generative_models import FunctionDeclaration
import re
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

agent_tools = generative_models.Tool(
  function_declarations=[search_knowledge_func],
)

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

def clean_string(input_string):
    # Pattern to match strings that start with "https" and continue until a space or end of string
    https_pattern = r'https\S*'
    
    # Remove HTTPS links from the input string, converting the string to lowercase first
    string_without_links = re.sub(https_pattern, '', input_string.lower())
    
    # Pattern to match alphanumeric sequences and quotes
    # This allows words, numbers, single quotes, and double quotes
    alphanumeric_and_quotes_pattern = r"[A-Za-z0-9'\"\s]+"
    
    # Find all sequences that match our updated pattern in the lowercase string without links
    all_matches = re.findall(alphanumeric_and_quotes_pattern, string_without_links)
    
    # Filter out any empty matches and join the rest into a space-separated string
    filtered_matches = [s.strip() for s in all_matches if s.strip()]
    result = ' '.join(filtered_matches)

    stop_words = set(["the", "have", "what", "and", "a", "an", "in", "on", "with", "of", "at", "from", "into", "during",
                      "including", "until", "against", "among", "throughout", "despite", "towards", "upon",
                      "concerning", "to", "in", "for", "on", "by", "about", "like", "through", "over",
                      "before", "between", "after", "since", "without", "under", "within", "along", "following",
                      "across", "behind", "beyond", "plus", "except", "but", "up", "out", "around", "down", "off", "above", "near"])

    # Tokenize the string into words
    words = result.split()

    # Filter out stop words
    filtered_words = [word for word in words if word.lower() not in stop_words]

    # Reconstruct the string without stop words
    clean_output = ' '.join(filtered_words)
    
    return clean_output

