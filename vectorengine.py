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
    """
    only for md files now
    """
    def __init__(self, folder_path, collection_name) -> None:
        self.folder_path = folder_path # folder path of md docs
        self.articles_df = self.md_to_df() # md files converted to df with embeddings
        self.collection = self.create_chroma_collection(collection_name)
        #print(self.articles_df)

    # Placeholder function for generating embeddings using OpenAI
    @staticmethod
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

    # give columns which need embeddings
    def md_to_df(self) -> pd.DataFrame:
        """
        Processes all markdown files in the given folder and compiles them into a DataFrame with their
        vector embeddings.
        
        :param folder_path: Path to the folder containing MD files.
        :return: A DataFrame with the columns id, file_path, title, text, title_vector, content_vector, vector_id.
        """
        data = []
        
        for idx, filename in enumerate(os.listdir(self.folder_path)):
            if filename.endswith(".md"):
                file_path = os.path.join(self.folder_path, filename)
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
        articles_df = pd.DataFrame(data)
        articles_df['vector_id'] = articles_df['vector_id'].apply(str)
        return articles_df
    
    # add possibility of multiple vector collections    
    def create_chroma_collection(self, collection_name):
        chroma_client = chromadb.EphemeralClient() # Equivalent to chromadb.Client(), ephemeral.
        # Uncomment for persistent client
        # chroma_client = chromadb.PersistentClient()

        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        embedding_function = OpenAIEmbeddingFunction(api_key=os.getenv("OPENAI_API_KEY"), model_name=EMBEDDING_MODEL)

        # embedding function defined here is used for search
        collection = chroma_client.create_collection(name=collection_name, embedding_function=embedding_function)
        # sop_title_collection = chroma_client.create_collection(name='sop_titles', embedding_function=embedding_function)

        # Add the content vectors
        collection.add(
            ids=self.articles_df.vector_id.tolist(),
            embeddings=self.articles_df.content_vector.tolist(),
        )
        return collection

    def search_df(self, query, max_results) -> pd.DataFrame:
        results = self.collection.query(query_texts=query, n_results=max_results, include=['distances']) 
        dataframe = self.articles_df
        search_df = pd.DataFrame({
                    'id':results['ids'][0], 
                    'score':results['distances'][0],
                    'title': dataframe[dataframe.vector_id.isin(results['ids'][0])]['title'],
                    'content': dataframe[dataframe.vector_id.isin(results['ids'][0])]['text'],
                    })
        
        return search_df
    
    # Function to create the desired string from a DataFrame
    def query(self, query, max_results, clearing_house="na", market="na") -> str:
        search_df = self.search_df(
        query=query,
        max_results=max_results,
        )

        # Initialize an empty string
        result_string = ""
        
        # Iterate over each row in the DataFrame
        for index, row in search_df.iterrows():
            # Append the title and content to the result string, followed by a newline character
            result_string += f"title:\n{row['title']}\n\ncontent:\n{row['content']}\n"
        
        return result_string.strip()  # Use strip() to remove the last newline character