from flask import Flask, render_template, request, jsonify
from summarization_algorithms import TextSummarizer
from multilingual_summarizer import MultilingualSummarizer
import logging

app = Flask(__name__)
summarizer = TextSummarizer()
multilingual_summarizer = MultilingualSummarizer()

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        data = request.get_json()
        text = data.get('text', '')
        algorithm = data.get('algorithm', 'textrank')
        n_sentences = int(data.get('n_sentences', 5))
        language = data.get('language', 'en')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if language == 'en':
            summary = summarizer.extractive_summarize(text, n_sentences, algorithm)
            result = {'summary': summary}
        else:
            result = multilingual_summarizer.summarize_multilingual(
                text=text,
                source_lang=language,
                summarizer=summarizer,
                n_sentences=n_sentences
            )
            
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error in summarization: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/languages')
def get_languages():
    """Get list of supported languages."""
    languages = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese'
    }
    return jsonify(languages)

if __name__ == '__main__':
    app.run(debug=True) 