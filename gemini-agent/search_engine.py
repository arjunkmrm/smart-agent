# goals:
# make this vector embedding agnostic
# add fuzzy search
from tenacity import retry, wait_random_exponential, stop_after_attempt
import dotenv
import pandas as pd
from dotenv import load_dotenv
import os
import ast
import chromadb
from ast import literal_eval
# from ada_genai.vertexai import TextEmbeddingModel
from vertexai.language_models import TextEmbeddingModel
from chromadb import Documents, EmbeddingFunction, Embeddings
import numpy as np
# from ada_genai.vertexai import GenerativeModel
import numpy as np
import pandas as pd
from typing import List, Union
from utils import tokenise
import math
import re
from stop_words import STOP_WORDS
from utils import levenshtein_distance, docstodf, generate_vertex_embedding, df_to_str
import numpy as np
import re
from collections import Counter
from vertexai.generative_models import GenerativeModel

# custom vertex ai embedding function to pass to chroma
class VertexEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self) -> None:
        pass

    # try without this
    def normalize_l2(self, x):
        x = np.array(x)
        return x
    
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
            response = model.get_embeddings([text])[0]

            embeddings_data = response
            if embeddings_data:
                embeddings.append(response.values)
            #cut_dim = embeddings[:768]
            #norm_dim = self.normalize_l2(cut_dim)

        return embeddings


# fix this
class FusionEngine:
    """
    abstraction over the individual search engines + rank fusion.
    temperarilly set to run on bm25 - need to figure a better implementation for toggling
    params:
    folder_path: folder containing .md knowledge files
    collection_name: identifier for this set of knowledge docs
    """
    def __init__(self, doc_df, collection_name) -> None:
        """ initialise dense and sparse search engines """
        self.doc_df = doc_df
        self.collection_name = collection_name
        self.vector_engine = VectorEngine(self.doc_df, self.collection_name) # already init with df
        self.bm25_engine = BM25(self.doc_df)
        self.bm25_engine.fit()

    def search(self, query, max_results = 3):
        search_result = pd.DataFrame()
        bm25_search = self.bm25_engine.search(query, max_results)
        dense_search = self.vector_engine.search(query, max_results)

        # rank the results from both searches
        bm25_search['bm25_ranking'] = bm25_search.reset_index().index + 1
        dense_search['dense_ranking'] = dense_search.reset_index().index + 1

        # merge the search results on the 'id' column
        merged_search = pd.merge(bm25_search, dense_search, how='outer', on=['id', 'title', 'content'], suffixes=('_bm', '_ve'))

        # Calculate the fusion score as the sum of reciprocal ranks
        merged_search['fusion_score'] = merged_search.apply(lambda row: (1 / row['bm25_ranking'] if not pd.isnull(row['bm25_ranking']) else 0) + 
                                                            (1 / row['dense_ranking'] if not pd.isnull(row['dense_ranking']) else 0), axis=1)

        # sort the results by fusion score in descending order
        search_result = merged_search.sort_values(by='fusion_score', ascending=False)

        return search_result

    # function to create the desired string from a DataFrame
    def query(self, query, max_results=3, search_type="bm25") -> str:
        search_df = self.search(query, search_type=search_type).head(max_results)  # Limit results to max_results
        result = df_to_str(search_df)

        return result

class VectorEngine:
    """
    dense search engine
    params:
    document_df: dataframe of minimal schema - id, title, content. Can be created from file path using doctodf function from utils
    collection_name: chroma collection name
    """
    def __init__(self, document_df, collection_name) -> None:
        self.document_df = document_df
        self.collection_name = collection_name
        self.collection = self._create_chroma_collection()
        
    def _create_chroma_collection(self):
        # Check if 'content_vector' column exists and if any of its values are non-null/non-empty
        # add content vector and update
        if 'content_vector' not in self.document_df.columns or self.document_df['content_vector'].isnull().all():
            self.document_df['content_vector'] = self.document_df['content'].apply(generate_vertex_embedding)
            script_path = os.path.abspath(__file__)
            script_directory = os.path.dirname(script_path)
            csv_path = os.path.join(script_directory, 'data', f'{self.collection_name}.csv')
            self.document_df.to_csv(csv_path, index=False)
        else:
            pass
        
        # get absolute path of script - append
        chroma_client = chromadb.PersistentClient("index")
        embedding_function = VertexEmbeddingFunction()

        # embedding function defined here is used for search
        collection = chroma_client.get_or_create_collection(name=self.collection_name, embedding_function=embedding_function)
        # sop_title_collection = chroma_client.create_collection(name='sop_titles', embedding_function=embedding_function)

        # a more efficient method for this?
        collection.add(
            ids=self.document_df.id.tolist(),
            embeddings=self.document_df.content_vector.tolist(),
        )
        return collection

    def search(self, query, max_results=3) -> pd.DataFrame:
        """
        returns dataframe of contents scored against query
        """
        results = self.collection.query(query_texts=query, n_results=max_results, include=['distances']) 
        #print(results)
        dataframe = self.document_df
        search_result = pd.DataFrame({
                    'id':results['ids'][0], 
                    'title': dataframe[dataframe.id.isin(results['ids'][0])]['title'], # vector id and result id are zeri indexed, hence matching on them
                    'content': dataframe[dataframe.id.isin(results['ids'][0])]['content'],
                    'score':results['distances'][0],
                    #'keywords': dataframe[dataframe.vector_id.isin(results['ids'][0])]['keywords'],
                    })
        
        sorted_result = search_result.sort_values(by='score', ascending=False)
        return sorted_result
    
    def query(self, query, max_results=3) -> str:
        """
        returns sting of content for llm to answer
        """
        search_df = self.search(query, max_results)  # limit results to max_results
        result = df_to_str(search_df)
        return result
    
# add lemma, fuzzy search
class BM25:
    """
    okapi bm25 implementation
    """

    def __init__(self, document_df, k1=1.5, b=0.75):
        """
        Initialize with document DataFrame, tuning parameters k1 and b.
        """
        self.b = b
        self.k1 = k1
        self.document_df = document_df

    def fit(self):
        """
        Fits the model to the corpus by calculating necessary statistics.
        """
        texts = self.document_df['content'].tolist()
        self.corpus_ = tokenise(texts)
        self.corpus_size_ = len(self.corpus_)
        self.tf_ = []
        self.df_ = {}
        self.idf_ = {}
        self.doc_len_ = []

        for document in self.corpus_:
            self.doc_len_.append(len(document))
            frequencies = {}
            for term in document:
                frequencies[term] = frequencies.get(term, 0) + 1

            self.tf_.append(frequencies)
            for term in frequencies:
                self.df_[term] = self.df_.get(term, 0) + 1

        for term, freq in self.df_.items():
            self.idf_[term] = math.log(1 + (self.corpus_size_ - freq + 0.5) / (freq + 0.5))

        self.avg_doc_len_ = sum(self.doc_len_) / self.corpus_size_
        pass

    def _score(self, query, index):
        # re-check scoring against okapi b25
        """
        Calculates BM25 score for a single document against a query.
        """
        score = 0.0
        doc_len = self.doc_len_[index]
        frequencies = self.tf_[index]
        for term in query:  # Ensure query is also tokenized
            if term not in frequencies:
                continue

            freq = frequencies[term]
            numerator = self.idf_[term] * freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len_)
            score += numerator / denominator

        return score
    
    def search(self, query, max_results=3):
        """
        Returns sorted search results for a given query based on BM25 score.
        """
        query = [word for word in query.lower().split() if word not in STOP_WORDS] # tokenise instead? tokenise should take string and convert to list of tokens or string
        scores = [self._score(query, index) for index in range(self.corpus_size_)]
        self.document_df['score'] = scores
        sorted_df = self.document_df.sort_values(by="score", ascending=False) # check this
        return sorted_df[:max_results]
    
    def query(self, query, max_results=3) -> str:
        search_df = self.search(query, max_results)  # Limit results to max_results
        result = df_to_str(search_df)
        return result