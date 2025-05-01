from flask import Flask, render_template, request, jsonify
from summarization_algorithms import TextSummarizer
import logging

app = Flask(__name__)
summarizer = TextSummarizer()

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
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        summary = summarizer.extractive_summarize(text, n_sentences, algorithm)
        return jsonify({'summary': summary})
        
    except Exception as e:
        logging.error(f"Error in summarization: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 