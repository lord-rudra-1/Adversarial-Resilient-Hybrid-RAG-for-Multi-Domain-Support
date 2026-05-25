import os
import glob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class HybridRetriever:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.documents = []
        self.doc_paths = []
        
        # Load documents
        self._load_corpus()
        
        # BM25 / TF-IDF
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        if self.documents:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
            
        # Dense Embeddings
        # all-MiniLM-L6-v2 is fast and small enough to run without GPU easily
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dense_embeddings = None
        if self.documents:
            self.dense_embeddings = self.embedding_model.encode(self.documents, show_progress_bar=False)
            
    def _load_corpus(self):
        # Recursive glob to get all markdown and text files
        pattern = os.path.join(self.data_dir, '**', '*.md')
        repo_root = os.path.dirname(self.data_dir)
        
        for filepath in glob.glob(pattern, recursive=True):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Deduplication by exact match
                if content not in self.documents:
                    self.documents.append(content)
                    # Store relative path for attribution (e.g. data/devplatform/...)
                    self.doc_paths.append(os.path.relpath(filepath, start=repo_root))

    def retrieve(self, query: str, top_k: int = 3, alpha: float = 0.5) -> List[Dict[str, str]]:
        if not self.documents:
            return []
            
        # 1. Sparse scores (TF-IDF approximation of BM25)
        query_tfidf = self.vectorizer.transform([query])
        sparse_scores = (self.tfidf_matrix * query_tfidf.T).toarray().flatten()
        
        # Normalize sparse scores
        if sparse_scores.max() > 0:
            sparse_scores = sparse_scores / sparse_scores.max()
            
        # 2. Dense scores
        query_emb = self.embedding_model.encode([query])
        # Cosine similarity
        dense_scores = np.dot(self.dense_embeddings, query_emb.T).flatten()
        dense_norms = np.linalg.norm(self.dense_embeddings, axis=1) * np.linalg.norm(query_emb)
        # Avoid division by zero
        dense_norms[dense_norms == 0] = 1
        dense_scores = dense_scores / dense_norms
        
        # Normalize dense scores
        if dense_scores.max() > 0:
            dense_scores = dense_scores / dense_scores.max()
            
        # 3. Fusion
        hybrid_scores = alpha * dense_scores + (1 - alpha) * sparse_scores
        
        # Get top-k indices
        top_indices = hybrid_scores.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "path": self.doc_paths[idx],
                "content": self.documents[idx],
                "score": float(hybrid_scores[idx])
            })
            
        return results
