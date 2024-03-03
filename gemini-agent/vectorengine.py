# create a separate vector engine for each collection?
import json
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
import dotenv
import pandas as pd
from dotenv import load_dotenv
from termcolor import colored  
import wget
from utils import clean_string
import os
import ast
import chromadb
from ast import literal_eval
#GPT_MODEL = "gpt-4-1106-preview"
GPT_MODEL = "gpt-3.5-turbo-0125"
EMBEDDING_MODEL = "text-embedding-3-small"
from vertexai.language_models import TextEmbeddingModel
from chromadb import Documents, EmbeddingFunction, Embeddings
import numpy as np
from searcharray import SearchArray
from vertexai.preview.generative_models import (
    GenerativeModel
)
from ast import literal_eval

# custom vertex ai embedding function to pass to chroma
class VertexEmbeddingFunction(EmbeddingFunction[Documents]):
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

# each query engine takes one folder path and convert it to a query-able engine
class VectorEngine:
    """
    only for md files for now
    """
    def __init__(self, folder_path, collection_name) -> None:
        self.folder_path = folder_path # folder path of md docs
        self.doc_df = pd.DataFrame()
        self.collection_name = collection_name
        self.articles_df = self.mdtodf() # md files converted to df with embeddings
        self.collection = self.create_chroma_collection(collection_name)
        
    @staticmethod
    def generate_vertex_embedding(text) -> list:
        """
        Generates an embedding vector string for the given text
        """
        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
        embeddings = model.get_embeddings([text])[0]
        # for embedding in embeddings:
        vector = embeddings.values

        return vector 

    # give columns which need embeddings
    # access only when index does not exist?
    # save df as csv with the collection name?
    def mdtodf(self) -> pd.DataFrame:
        """
        Processes all markdown files in the given folder and compiles them into a DataFrame with their
        vector embeddings.
        
        :param folder_path: Path to the folder containing MD files.
        :return: A DataFrame with the columns id, file_path, title, text, title_vector, content_vector, vector_id.
        """
        data = []

        file_path = f'data/{self.collection_name}.csv'

        if not os.path.exists(file_path): # if csv with collection name doesn't exist
            for idx, filename in enumerate(os.listdir(self.folder_path)):
                if filename.endswith(".md"):
                    file_path = os.path.join(self.folder_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        title = os.path.splitext(filename)[0]
                        #if augment_keywords:
                        keywords = self.get_keywords(f"{title}\n{content}")
                        # title_vector = self.generate_vertex_embedding(title)
                        content_vector = self.generate_vertex_embedding(content)
                        # keyword_vector = self.generate_vertex_embedding(keywords)

                        # Append to dict list
                        data.append({
                            "id": idx + 1,
                            "file_path": file_path,
                            "title": title,
                            "content": content,
                            # "title_vector": title_vector,
                            "content_vector": content_vector,
                            "keywords": keywords,
                            # 'keyword_vector': keyword_vector,
                            "vector_id": idx  # Assuming vector_id starts from 0
                        })

            articles_df = pd.DataFrame(data)
            articles_df['vector_id'] = articles_df['vector_id'].apply(str)
            articles_df.to_csv(f"data/{self.collection_name}.csv", index=False)
        else:
            articles_df = pd.read_csv(file_path)
            articles_df['id'] = articles_df['id'].astype(str)
            articles_df['vector_id'] = articles_df['vector_id'].astype(str)
            articles_df['content_vector'] = articles_df['content_vector'].apply(lambda x: ast.literal_eval(x))

        self.doc_df = articles_df
        return articles_df
    
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
    
    # add possibility of multiple vector collections    
    def create_chroma_collection(self, collection_name):
        chroma_client = chromadb.PersistentClient("index")
        embedding_function = VertexEmbeddingFunction()

        # embedding function defined here is used for search
        collection = chroma_client.get_or_create_collection(name=collection_name, embedding_function=embedding_function)
        # sop_title_collection = chroma_client.create_collection(name='sop_titles', embedding_function=embedding_function)

        file_path = 'index'

        #if not os.path.exists(file_path):
        collection.add(
            ids=self.articles_df.vector_id.tolist(),
            embeddings=self.articles_df.content_vector.tolist(),
        )
        #else:
        #    pass

        return collection

    def search_df(self, query, max_results) -> pd.DataFrame:
        results = self.collection.query(query_texts=query, n_results=max_results, include=['distances']) 
        dataframe = self.articles_df
        search_df = pd.DataFrame({
                    'id':results['ids'][0], 
                    'score':results['distances'][0],
                    'title': dataframe[dataframe.vector_id.isin(results['ids'][0])]['title'],
                    'content': dataframe[dataframe.vector_id.isin(results['ids'][0])]['content'],
                    'keywords': dataframe[dataframe.vector_id.isin(results['ids'][0])]['keywords'],
                    })
        
        df_sorted = search_df.sort_values(by='score', ascending=False)
        return df_sorted
    
    def bm25_rank(self, query, search_df, k) -> pd.DataFrame:
        split_words = query.split()
        print(type(split_words))
        print(split_words)
        lower_split = [item.lower() for item in split_words]
        search_df['clean_content'] = search_df['content'].apply(clean_string)
        search_df['bm25_tokenized'] = SearchArray.index(search_df['clean_content'])
        search_df['bm25_score'] = search_df['bm25_tokenized'].array.score(lower_split)  # need to change this up a but - for each word and then add?
        sorted_df = search_df.sort_values('bm25_score', ascending=False) # sort by score
        final_df = sorted_df.iloc[:k] # return top k columns

        return final_df
    
    def rank_fusion(self, query, dense_k, fusion_k) -> pd.DataFrame:
        # Obtain the dense and bm25 rankings
        dense_df = self.search_df(query=query, max_results=dense_k)
        bm25_df = self.bm25_rank(query, self.doc_df, k=dense_k)

        # Set a default rank for documents not present in the DataFrames
        default_dense_rank = dense_k + 1
        default_bm25_rank = dense_k + 1

        # Assign rankings based on index position (row number) + 1, because index is zero-based
        dense_df['dense_ranking'] = dense_df.reset_index().index + 1
        bm25_df['bm25_ranking'] = bm25_df.reset_index().index + 1

        # Perform an outer join on the two DataFrames based on the 'id' column
        merged_df = pd.merge(bm25_df, dense_df, on='id', how='outer', suffixes=('_bm25', '_dense'))

        # Fill NaN values for documents that appear in one DataFrame but not the other
        merged_df['bm25_ranking'].fillna(default_bm25_rank, inplace=True)
        merged_df['dense_ranking'].fillna(default_dense_rank, inplace=True)

        # Fill NaN values for documents that appear in one DataFrame but not the other
        merged_df['bm25_ranking'].fillna(default_bm25_rank, inplace=True)
        merged_df['dense_ranking'].fillna(default_dense_rank, inplace=True)

        # Calculate the rank scores as the harmonic mean of the rankings
        merged_df['rank_score'] = 2 / (1 / merged_df['bm25_ranking'] + 1 / merged_df['dense_ranking'])

        # Sort by rank_score in descending order and select the top fusion_k documents
        merged_df = merged_df.sort_values(by='rank_score', ascending=False).head(fusion_k)

        return merged_df
 
    # Function to create the desired string from a DataFrame
    def query(self, query, max_results, clearing_house="na", market="na") -> str:
        search_df = self.search_df(
        query=query,
        max_results=max_results,
        )

        result_string = ""
    
        for index, row in search_df.iterrows(): # iterate over each row in the DataFrame
            result_string += f"Start of document.\nDocument Title:\n{row['title']}\n\nContent:\n{row['content']}\nEnd of document."
        
        return result_string.strip()  # Use strip() to remove the last newline character