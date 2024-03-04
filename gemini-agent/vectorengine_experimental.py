# create a separate vector engine for each collection?
import json
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
import dotenv
import pandas as pd
from dotenv import load_dotenv
# from termcolor import colored  
# import wget
from utils import clean_string
import os
import ast
import chromadb
from ast import literal_eval
from vertexai import TextEmbeddingModel
from chromadb import Documents, EmbeddingFunction, Embeddings
import numpy as np
#from searcharray import SearchArray
# from ada_genai.vertexai import (
#     GenerativeModel,
# )
from vertexai import (
    GenerativeModel,
)
from ast import literal_eval
import numpy as np
import pandas as pd
from typing import List, Union
import math
import re
from stop_words import STOP_WORDS
from utils import levenshtein_distance

# custom vertex ai embedding function to pass to chroma
class VertexEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self) -> None:
        pass

    def normalize_l2(self, x):
        x = np.array(x)
        return x
    
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
    
class SearchEngine:
    def __init__(self, folder_path, collection_name) -> None:
        self.folder_path = folder_path
        self.collection_name = collection_name
        self.doc_df = pd.DataFrame()
         # create simple df with title, content, file_path, id of docs
        # this df is then passed to the bm25 and vector engines
        self.vector_engine = VectorEngine(self.doc_df, self.collection_name)
        self.bm25_engine = BM25(self.doc_df, self.collection_name)

    def docstodf(self):
        data = []
        script_path = os.path.abspath(__file__)
        script_directory = os.path.dirname(script_path)
        file_path = f'{script_directory}/data/{self.collection_name}.csv'

        if not os.path.exists(file_path): # if csv with collection name doesn't exist
            for idx, filename in enumerate(os.listdir(self.folder_path)):
                if filename.endswith(".md"):
                    file_path = os.path.join(self.folder_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        title = os.path.splitext(filename)[0]

                        # Append to dict list
                        data.append({
                            "id": idx + 1,
                            "file_path": file_path,
                            "title": title,
                            "content": content,
                            #"vector_id": idx 
                        })

            articles_df = pd.DataFrame(data)
            articles_df['id'] = articles_df['id'].apply(str)
            articles_df.to_csv(file_path, index=False)
        else:
            articles_df = pd.read_csv(file_path)
            articles_df['id'] = articles_df['id'].astype(str)

        self.doc_df = articles_df
        pass

    def search(self, query, search_type = "fusion"):
        dense_search = self.vector_engine.search(query, self.doc_df, self.collection_name, 3)
        bm25_search = self.bm25_engine.search(query, self.doc_df, self.collection_name, max_reuslts=3) # to implement
        # fusion_search - call the rank fusion method within the class in: bm25 df, dense df -> fusion df
        pass # returns sorted df

    def query(self):
        # this method does the df to formatted string
        pass

# given array data, should get embeds and score against given query and return array scores - main func
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
    def _generate_vertex_embedding(text) -> list:
        """
        Generates an embedding vector string for the given text
        """
        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
        embeddings = model.get_embeddings([text])[0]
        # for embedding in embeddings:
        vector = embeddings.values

        return vector 
    
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
    
    def _init_dense_df(self):
        # init dense store
        script_path = os.path.abspath(__file__)
        script_directory = os.path.dirname(script_path)
        file_path = f'{script_directory}/data/{self.collection_name}.csv'
        if not os.path.exists(file_path):
            self.docstodf()
            self.doc_df['content_vector'] = self.doc_df['content'].apply(self.vector_engine.generate_vertex_embedding)
        else:
            self.doc_df = pd.read_csv(file_path)
            self.doc_df['id'] = self.doc_df['id'].astype(str)
        pass
        # create chroma collection
        self.collection = self.vector_engine.create_chroma_collection(self.doc_df, self.collection_name)
    
    # add possibility of multiple vector collections    
    def _create_chroma_collection(self, document_df, collection_name):
        chroma_client = chromadb.PersistentClient("index")
        embedding_function = VertexEmbeddingFunction()

        # embedding function defined here is used for search
        collection = chroma_client.get_or_create_collection(name=collection_name, embedding_function=embedding_function)
        # sop_title_collection = chroma_client.create_collection(name='sop_titles', embedding_function=embedding_function)

        file_path = 'index'

        #if not os.path.exists(file_path):
        collection.add(
            ids=document_df.id.tolist(),
            embeddings=document_df.content_vector.tolist(),
        )

        return collection

    def search(self, query, document_df, collection, max_results) -> pd.DataFrame:
        results = collection.query(query_texts=query, n_results=max_results, include=['distances']) 
        dataframe = document_df
        search_result = pd.DataFrame({
                    'id':results['ids'][0], 
                    'score':results['distances'][0],
                    'title': dataframe[dataframe.vector_id.isin(results['ids'][0])]['title'],
                    'content': dataframe[dataframe.vector_id.isin(results['ids'][0])]['content'],
                    'keywords': dataframe[dataframe.vector_id.isin(results['ids'][0])]['keywords'],
                    })
        
        sorted_result = search_result.sort_values(by='score', ascending=False)
        return sorted_result
    
 
    # function to create the desired string from a DataFrame
    def query(self, query, max_results, clearing_house="na", market="na") -> str:
        search_df = self.search_df(
        query=query,
        max_results=max_results,
        )

        result_string = ""
    
        for row in search_df.iterrows(): # iterate over each row in the DataFrame
            result_string += f"Start of document.\nDocument Title:\n{row['title']}\n\nContent:\n{row['content']}\nEnd of document."
        
        return result_string.strip()  # Use strip() to remove the last newline character

class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75, use_fuzzy: bool = False) -> None:
        self.k1: float = k1
        self.b: float = b
        self.use_fuzzy: bool = use_fuzzy  # Add this line
        self.idf_: dict = {}
        self.tf_: List[dict] = []
        self.doc_len_: np.ndarray = np.array([])
        self.avg_doc_len_: float = 0.0
        self.corpus_size_: int = 0
        self.corpus_: List[List[str]] = []

    def tokenize(self, series: pd.Series) -> List[List[str]]:
        """Tokenizes the text data in the pandas Series, with improvements."""
        
        # Convert to lowercase, remove punctuation/special characters, and split
        series_cleaned = series.str.lower().map(lambda x: re.sub(r'\W+', ' ', x))
        
        # Tokenize and remove stop words using the STOP_WORDS set
        tokens = series_cleaned.str.split().map(lambda x: [word for word in x if word not in STOP_WORDS]).tolist()
        
        return tokens

    def fit(self, corpus: Union[pd.Series, List[List[str]]]) -> 'BM25':
        """Fits the model to the given corpus."""
        if isinstance(corpus, pd.Series):
            corpus = self.tokenize(corpus)
        
        self.doc_len_ = np.array([len(doc) for doc in corpus])
        self.corpus_size_ = len(corpus)
        self.avg_doc_len_ = np.mean(self.doc_len_)
        
        flat_corpus = [term for doc in corpus for term in doc]
        unique_terms, counts = np.unique(flat_corpus, return_counts=True)
        df = dict(zip(unique_terms, counts))
        
        self.idf_ = {term: math.log((self.corpus_size_ - freq + 0.5) / (freq + 0.5) + 1) for term, freq in df.items()}
        self.corpus_ = corpus

        for doc in corpus:
            term_counts = dict(pd.Series(doc).value_counts())
            self.tf_.append(term_counts)

        return self

    def _score(self, query: List[str], index: int) -> float:
        score = 0.0
        doc_len = self.doc_len_[index]
        frequencies = self.tf_[index]
        
        if self.use_fuzzy:
            fuzzy_threshold = 2  # Maximum allowed edits
            for query_term in query:
                for term in frequencies:
                    # Use fuzzy matching if enabled
                    if levenshtein_distance(query_term, term) <= fuzzy_threshold:
                        freq = frequencies[term]
                        idf = self.idf_.get(term, 0)
                        numerator = idf * (freq * (self.k1 + 1))
                        denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len_)
                        score += numerator / denominator
        else:
            # Original exact match logic
            for term in query:
                if term in frequencies:
                    freq = frequencies[term]
                    idf = self.idf_.get(term, 0)
                    numerator = idf * (freq * (self.k1 + 1))
                    denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len_)
                    score += numerator / denominator

        return score

    def search(self, query: List[str]) -> np.ndarray:
        """Computes BM25 scores for all documents in the corpus against the query."""
        scores = np.array([self._score(query, i) for i in range(self.corpus_size_)])
        return scores
