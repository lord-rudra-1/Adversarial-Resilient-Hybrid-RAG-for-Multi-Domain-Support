import os
import glob
import numpy as np
import pickle
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from typing import List, Dict

logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.documents = []
        self.doc_paths = []
        
        self.cache_dir = os.path.join(self.data_dir, ".cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.dense_cache_path = os.path.join(self.cache_dir, "dense_embeddings.npy")
        self.tfidf_cache_path = os.path.join(self.cache_dir, "tfidf_matrix.pkl")
        self.vectorizer_cache_path = os.path.join(self.cache_dir, "vectorizer.pkl")
        self.docs_cache_path = os.path.join(self.cache_dir, "docs_metadata.pkl")
        
        # Fast load from cache if exists, otherwise rebuild
        if self._load_from_cache():
            logger.info("HybridRetriever loaded from cache instantly.")
        else:
            logger.info("Building HybridRetriever index from scratch...")
            self._build_index()
            self._save_to_cache()
            
        # We always need the sentence transformer in memory for query encoding
        # This is fast since the model is small
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
    def _load_from_cache(self) -> bool:
        if not (os.path.exists(self.dense_cache_path) and 
                os.path.exists(self.tfidf_cache_path) and 
                os.path.exists(self.vectorizer_cache_path) and 
                os.path.exists(self.docs_cache_path)):
            return False
            
        try:
            self.dense_embeddings = np.load(self.dense_cache_path)
            
            with open(self.tfidf_cache_path, 'rb') as f:
                self.tfidf_matrix = pickle.load(f)
                
            with open(self.vectorizer_cache_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
                
            with open(self.docs_cache_path, 'rb') as f:
                metadata = pickle.load(f)
                self.documents = metadata['documents']
                self.doc_paths = metadata['doc_paths']
                
            return True
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}. Will rebuild.")
            return False
            
    def _save_to_cache(self):
        try:
            np.save(self.dense_cache_path, self.dense_embeddings)
            
            with open(self.tfidf_cache_path, 'wb') as f:
                pickle.dump(self.tfidf_matrix, f)
                
            with open(self.vectorizer_cache_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
                
            with open(self.docs_cache_path, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'doc_paths': self.doc_paths
                }, f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _build_index(self):
        pattern = os.path.join(self.data_dir, '**', '*.md')
        repo_root = os.path.dirname(self.data_dir)
        
        for filepath in glob.glob(pattern, recursive=True):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if content not in self.documents:
                    self.documents.append(content)
                    self.doc_paths.append(os.path.relpath(filepath, start=repo_root))
                    
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        if self.documents:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
            
        temp_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dense_embeddings = None
        if self.documents:
            self.dense_embeddings = temp_model.encode(self.documents, show_progress_bar=False)

    def retrieve(self, query: str, top_k: int = 3, alpha: float = 0.5) -> List[Dict[str, str]]:
        if not self.documents:
            return []
            
        # 1. Sparse scores (TF-IDF approximation of BM25)
        query_tfidf = self.vectorizer.transform([query])
        sparse_scores = (self.tfidf_matrix * query_tfidf.T).toarray().flatten()
        
        if sparse_scores.max() > 0:
            sparse_scores = sparse_scores / sparse_scores.max()
            
        # 2. Dense scores
        query_emb = self.embedding_model.encode([query])
        dense_scores = np.dot(self.dense_embeddings, query_emb.T).flatten()
        dense_norms = np.linalg.norm(self.dense_embeddings, axis=1) * np.linalg.norm(query_emb)
        dense_norms[dense_norms == 0] = 1
        dense_scores = dense_scores / dense_norms
        
        if dense_scores.max() > 0:
            dense_scores = dense_scores / dense_scores.max()
            
        # 3. Fusion
        hybrid_scores = alpha * dense_scores + (1 - alpha) * sparse_scores
        
        top_indices = hybrid_scores.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "path": self.doc_paths[idx],
                "content": self.documents[idx],
                "score": float(hybrid_scores[idx])
            })
            
        return results
