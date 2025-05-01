import numpy as np
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from collections import Counter
import logging
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor

class TextSummarizer:
    def __init__(self):
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))
        self._vectorizer = TfidfVectorizer(stop_words='english')
        self._lock = threading.Lock()
        
    @lru_cache(maxsize=1000)
    def _preprocess_text(self, text):
        """Cache preprocessed text to avoid redundant processing."""
        sentences = sent_tokenize(text)
        clean_sentences = []
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            clean_words = [w for w in words if w not in self.stop_words]
            clean_sentences.append(' '.join(clean_words))
        return clean_sentences
    
    def _create_similarity_matrix(self, vectors):
        """Create similarity matrix using parallel processing."""
        n_sentences = len(vectors)
        sim_mat = np.zeros([n_sentences, n_sentences])
        
        def process_chunk(start_idx):
            chunk_size = 100
            end_idx = min(start_idx + chunk_size, n_sentences)
            for i in range(start_idx, end_idx):
                for j in range(n_sentences):
                    if i != j:
                        sim_mat[i][j] = cosine_similarity(
                            vectors[i].reshape(1,100),
                            vectors[j].reshape(1,100)
                        )[0,0]
        
        with ThreadPoolExecutor() as executor:
            chunk_starts = range(0, n_sentences, 100)
            executor.map(process_chunk, chunk_starts)
        
        return sim_mat
    
    def extractive_summarize(self, text, n_sentences=5, algorithm='textrank'):
        """Summarize text using specified algorithm with optimizations."""
        try:
            sentences = sent_tokenize(text)
            clean_sentences = self._preprocess_text(text)
            
            if algorithm == 'textrank':
                return self._textrank_summarize(clean_sentences, sentences, n_sentences)
            elif algorithm == 'tfidf':
                return self._tfidf_summarize(clean_sentences, sentences, n_sentences)
            elif algorithm == 'frequency':
                return self._frequency_summarize(clean_sentences, sentences, n_sentences)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")
        except Exception as e:
            logging.error(f"Error in summarization: {str(e)}")
            raise
    
    def _textrank_summarize(self, clean_sentences, original_sentences, n_sentences):
        """Optimized TextRank algorithm implementation."""
        with self._lock:
            sentence_vectors = self._vectorizer.fit_transform(clean_sentences)
        
        similarity_matrix = self._create_similarity_matrix(sentence_vectors.toarray())
        nx_graph = nx.from_numpy_array(similarity_matrix)
        scores = nx.pagerank(nx_graph)
        
        ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(original_sentences)), reverse=True)
        summary = [s for _, s in ranked_sentences[:n_sentences]]
        
        return ' '.join(summary)
    
    def _tfidf_summarize(self, clean_sentences, original_sentences, n_sentences):
        """Optimized TF-IDF based summarization."""
        with self._lock:
            tfidf_matrix = self._vectorizer.fit_transform(clean_sentences)
        
        sentence_scores = []
        for i in range(len(clean_sentences)):
            score = np.sum(tfidf_matrix[i].toarray())
            sentence_scores.append((score, original_sentences[i]))
        
        sentence_scores.sort(reverse=True)
        summary = [s for _, s in sentence_scores[:n_sentences]]
        
        return ' '.join(summary)
    
    def _frequency_summarize(self, clean_sentences, original_sentences, n_sentences):
        """Optimized frequency-based summarization."""
        word_frequencies = Counter()
        for sentence in clean_sentences:
            words = sentence.split()
            word_frequencies.update(words)
        
        sentence_scores = []
        for i, sentence in enumerate(clean_sentences):
            words = sentence.split()
            score = sum(word_frequencies[w] for w in words)
            sentence_scores.append((score, original_sentences[i]))
        
        sentence_scores.sort(reverse=True)
        summary = [s for _, s in sentence_scores[:n_sentences]]
        
        return ' '.join(summary) 