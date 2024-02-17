# create a separate vector engine for each collection?

import json
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
import dotenv
import pandas as pd
from dotenv import load_dotenv
from termcolor import colored  
import wget
import os
import chromadb
from ast import literal_eval
#GPT_MODEL = "gpt-4-1106-preview"
GPT_MODEL = "gpt-3.5-turbo-0125"
EMBEDDING_MODEL = "text-embedding-3-small"
load_dotenv() 
client = OpenAI()


class VectorEngine:
    def __init__(self) -> None:
        pass

    # Placeholder function for generating embeddings using OpenAI
    def generate_openai_embedding(text) -> str:
        """
        Generates an embedding vector string for the given text using OpenAI's embedding API.
        Replace this with an actual call to openai.Embedding.create() in your code.
        """
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL
        )

        return response.data[0].embedding  # Assuming embedding size is 768

    def md_to_df(self, folder_path) -> pd.DataFrame:
        """
        Processes all markdown files in the given folder and compiles them into a DataFrame.
        
        :param folder_path: Path to the folder containing MD files.
        :return: A DataFrame with the columns id, file_path, title, text, title_vector, content_vector, vector_id.
        """
        data = []
        
        for idx, filename in enumerate(os.listdir(folder_path)):
            if filename.endswith(".md"):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    title = os.path.splitext(filename)[0]
                    title_vector = self.generate_openai_embedding(title)
                    content_vector = self.generate_openai_embedding(content)
                    
                    # Append to data list
                    data.append({
                        "id": idx + 1,
                        "file_path": file_path,
                        "title": title,
                        "text": content,
                        "title_vector": title_vector,
                        "content_vector": content_vector,
                        "vector_id": idx  # Assuming vector_id starts from 0
                    })
        
        # Convert list to DataFrame
        df = pd.DataFrame(data)
        return df
    
    # add possibility of multiple vector collections    
    def create_collection(self, article_df, collection_name):

        chroma_client = chromadb.EphemeralClient() # Equivalent to chromadb.Client(), ephemeral.
        # Uncomment for persistent client
        # chroma_client = chromadb.PersistentClient()

        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        embedding_function = OpenAIEmbeddingFunction(api_key=os.getenv("OPENAI_API_KEY"), model_name=EMBEDDING_MODEL)

        # embedding function defined here is used for search
        self.collection = chroma_client.create_collection(name=collection_name, embedding_function=embedding_function)
        # sop_title_collection = chroma_client.create_collection(name='sop_titles', embedding_function=embedding_function)

        # Add the content vectors
        self.collection.add(
            ids=article_df.vector_id.tolist(),
            embeddings=article_df.content_vector.tolist(),
        )

        # Add the title vectors
        # sop_title_collection.add(
        #     ids=article_df.vector_id.tolist(),
        #     embeddings=article_df.title_vector.tolist(),
        # )
    
    @staticmethod
    def search_df(collection, query, max_results, dataframe) -> pd.DataFrame:
        results = collection.query(query_texts=query, n_results=max_results, include=['distances']) 
        df = pd.DataFrame({
                    'id':results['ids'][0], 
                    'score':results['distances'][0],
                    'title': dataframe[dataframe.vector_id.isin(results['ids'][0])]['title'],
                    'content': dataframe[dataframe.vector_id.isin(results['ids'][0])]['text'],
                    })
        
        return df
    
    # Function to create the desired string from a DataFrame
    def search_knowledge(self, query, articles, n, clearing_house="na", market="na") -> str:
        df = self.search_df(
        collection=self.collection,
        query=query,
        max_results=n,
        dataframe=articles
        )
        # Initialize an empty string
        result_string = ""
        
        # Iterate over each row in the DataFrame
        for index, row in df.iterrows():
            # Append the title and content to the result string, followed by a newline character
            result_string += f"{row['title']}\n{row['content']}\n"
        
        return result_string.strip()  # Use strip() to remove the last newline character