import numpy as np
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from collections import Counter
import logging

class TextSummarizer:
    def __init__(self):
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))
        
    def extractive_summarize(self, text, n_sentences=5, algorithm='textrank'):
        """Summarize text using specified algorithm.
        
        Args:
            text (str): Input text to summarize
            n_sentences (int): Number of sentences in summary
            algorithm (str): Algorithm to use ('textrank', 'tfidf', 'frequency')
            
        Returns:
            str: Generated summary
        """
        sentences = sent_tokenize(text)
        
        if algorithm == 'textrank':
            return self._textrank_summarize(sentences, n_sentences)
        elif algorithm == 'tfidf':
            return self._tfidf_summarize(sentences, n_sentences)
        elif algorithm == 'frequency':
            return self._frequency_summarize(sentences, n_sentences)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def _textrank_summarize(self, sentences, n_sentences):
        """TextRank algorithm implementation."""
        # Create sentence vectors using TF-IDF
        vectorizer = TfidfVectorizer(stop_words='english')
        sentence_vectors = vectorizer.fit_transform(sentences)
        
        # Create similarity matrix
        similarity_matrix = cosine_similarity(sentence_vectors)
        
        # Apply PageRank
        nx_graph = nx.from_numpy_array(similarity_matrix)
        scores = nx.pagerank(nx_graph)
        
        # Get top sentences
        ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
        summary = [s for _, s in ranked_sentences[:n_sentences]]
        
        return ' '.join(summary)
    
    def _tfidf_summarize(self, sentences, n_sentences):
        """TF-IDF based summarization."""
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(sentences)
        
        # Calculate sentence scores based on TF-IDF values
        sentence_scores = []
        for i in range(len(sentences)):
            score = np.sum(tfidf_matrix[i].toarray())
            sentence_scores.append((score, sentences[i]))
        
        # Get top sentences
        sentence_scores.sort(reverse=True)
        summary = [s for _, s in sentence_scores[:n_sentences]]
        
        return ' '.join(summary)
    
    def _frequency_summarize(self, sentences, n_sentences):
        """Frequency-based summarization."""
        # Tokenize and count word frequencies
        word_frequencies = Counter()
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            word_frequencies.update([w for w in words if w not in self.stop_words])
        
        # Calculate sentence scores
        sentence_scores = []
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            score = sum(word_frequencies[w] for w in words if w not in self.stop_words)
            sentence_scores.append((score, sentence))
        
        # Get top sentences
        sentence_scores.sort(reverse=True)
        summary = [s for _, s in sentence_scores[:n_sentences]]
        
        return ' '.join(summary) 