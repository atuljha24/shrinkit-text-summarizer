import unittest
from summarization_algorithms import TextSummarizer

class TestTextSummarizer(unittest.TestCase):
    def setUp(self):
        self.summarizer = TextSummarizer()
        self.sample_text = """
        Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language.
        It is used to apply machine learning algorithms to text and speech.
        For example, we can use NLP to create systems like speech recognition, document summarization, machine translation, spam detection, named entity recognition, question answering, autocomplete, predictive typing and so on.
        NLP is a way for computers to analyze, understand, and derive meaning from human language in a smart and useful way.
        By utilizing NLP and its components, one can organize the massive chunks of text data, perform numerous automated tasks and solve a wide range of problems such as – automatic summarization, machine translation, named entity recognition, relationship extraction, sentiment analysis, speech recognition, and topic segmentation etc.
        """

    def test_textrank_summarization(self):
        summary = self.summarizer.extractive_summarize(self.sample_text, algorithm='textrank')
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)

    def test_tfidf_summarization(self):
        summary = self.summarizer.extractive_summarize(self.sample_text, algorithm='tfidf')
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)

    def test_frequency_summarization(self):
        summary = self.summarizer.extractive_summarize(self.sample_text, algorithm='frequency')
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)

    def test_invalid_algorithm(self):
        with self.assertRaises(ValueError):
            self.summarizer.extractive_summarize(self.sample_text, algorithm='invalid')

    def test_summary_length(self):
        n_sentences = 3
        summary = self.summarizer.extractive_summarize(self.sample_text, n_sentences=n_sentences)
        summary_sentences = summary.split('.')
        self.assertLessEqual(len(summary_sentences), n_sentences + 1)  # +1 for potential trailing period

if __name__ == '__main__':
    unittest.main() 