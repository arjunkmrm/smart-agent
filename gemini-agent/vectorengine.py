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
from vertexai.language_models import TextEmbeddingModel
from chromadb import Documents, EmbeddingFunction, Embeddings
import numpy as np
from ast import literal_eval

class VertexEmbeddingFunction(EmbeddingFunction[Documents]):
    # Follow API Quickstart for Google Vertex AI
    # https://cloud.google.com/vertex-ai/docs/generative-ai/start/quickstarts/api-quickstart
    # Information about the text embedding modules in Google Vertex AI
    # https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/get-text-embeddings
    def __init__(self) -> None:
        pass

    def normalize_l2(self, x):
        x = np.array(x)
        # if x.ndim == 1:
        #     norm = np.linalg.norm(x)
        #     if norm == 0:
        #         return x
        return x
        # else:
        #     norm = np.linalg.norm(x, 2, axis=1, keepdims=True)
        #     return np.where(norm == 0, x, x / norm)

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
            response = model.get_embeddings([text])[0]
            # Extracting the embeddings from the response
            embeddings_data = response
            if embeddings_data:
                embeddings.append(response.values)
            #cut_dim = embeddings[:768]
            #norm_dim = self.normalize_l2(cut_dim)

        return embeddings


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
    def generate_vertex_embedding(text) -> list:
        """
        Generates an embedding vector string for the given text using OpenAI's embedding API.
        Replace this with an actual call to openai.Embedding.create() in your code.
        """
        """Text embedding with a Large Language Model."""
        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
        embeddings = model.get_embeddings([text])[0]
        # for embedding in embeddings:
        vector = embeddings.values

        return vector # Assuming embedding size is 768

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
                    title_vector = self.generate_vertex_embedding(title)
                    content_vector = self.generate_vertex_embedding(content)
                    
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
        #articles_df['title_vector'] = articles_df.title_vector.apply(literal_eval)
        #articles_df['content_vector'] = articles_df.content_vector.apply(literal_eval)
        return articles_df
    
    # add possibility of multiple vector collections    
    def create_chroma_collection(self, collection_name):
        #chroma_client = chromadb.EphemeralClient() # Equivalent to chromadb.Client(), ephemeral.
        chroma_client = chromadb.PersistentClient("index")

        embedding_function = VertexEmbeddingFunction()

        # embedding function defined here is used for search
        collection = chroma_client.get_or_create_collection(name=collection_name, embedding_function=embedding_function)
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
        
        df_sorted = search_df.sort_values(by='score', ascending=False)
        return df_sorted
        
    
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