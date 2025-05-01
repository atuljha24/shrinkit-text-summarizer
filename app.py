from flask import Flask, render_template, request, jsonify, send_from_directory
from summarization_algorithms import TextSummarizer
from multilingual_summarizer import MultilingualSummarizer
from monitoring import metrics
import logging
from flask_swagger_ui import get_swaggerui_blueprint
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import time

app = Flask(__name__)
summarizer = TextSummarizer()
multilingual_summarizer = MultilingualSummarizer()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.yml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "ShrinkIt Text Summarizer API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Configure caching
cache_config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300
}
app.config.from_mapping(cache_config)
cache = Cache(app)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per minute"]
)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/')
@metrics.track_duration('home_page_load')
def home():
    return render_template('index.html')

def generate_cache_key():
    """Generate a cache key from the request data."""
    data = request.get_json()
    return f"{data.get('text', '')}:{data.get('algorithm', '')}:{data.get('num_sentences', '')}:{data.get('language', '')}"

@app.route('/summarize', methods=['POST'])
@limiter.limit("10 per minute")
@cache.cached(timeout=300, key_prefix=generate_cache_key)
@metrics.track_duration('summarize_request')
def summarize():
    try:
        start_time = time.time()
        data = request.get_json()
        
        if not data or 'text' not in data:
            metrics.track_event('summarize_error', {'error': 'No text provided'})
            return jsonify({'error': 'No text provided'}), 400
            
        text = data['text']
        algorithm = data.get('algorithm', 'textrank')
        num_sentences = int(data.get('num_sentences', 5))
        language = data.get('language', 'english')
        
        metrics.track_event('summarize_params', {
            'algorithm': algorithm,
            'num_sentences': num_sentences,
            'language': language,
            'text_length': len(text)
        })
        
        if language != 'english':
            summary = multilingual_summarizer.summarize(
                text=text,
                source_lang=language,
                n_sentences=num_sentences,
                algorithm=algorithm
            )
        else:
            summary = summarizer.extractive_summarize(
                text=text,
                n_sentences=num_sentences,
                algorithm=algorithm
            )
            
        processing_time = time.time() - start_time
        logger.info(f"Summarization completed in {processing_time:.2f} seconds")
        
        metrics.track_event('summarize_success', {
            'processing_time': processing_time,
            'summary_length': len(summary)
        })
        
        return jsonify({
            'summary': summary,
            'processing_time': processing_time,
            'algorithm': algorithm,
            'language': language
        })
        
    except Exception as e:
        logger.error(f"Error in summarization: {str(e)}")
        metrics.track_event('summarize_error', {'error': str(e)})
        return jsonify({'error': str(e)}), 500

@app.route('/languages', methods=['GET'])
@cache.cached(timeout=3600)
@metrics.track_duration('languages_request')
def get_languages():
    """Return list of supported languages."""
    languages = {
        'english': 'English',
        'spanish': 'Spanish',
        'french': 'French',
        'german': 'German',
        'italian': 'Italian',
        'portuguese': 'Portuguese'
    }
    return jsonify(languages)

@app.route('/metrics', methods=['GET'])
@metrics.track_duration('metrics_request')
def get_metrics():
    """Get current metrics summary."""
    try:
        summary = metrics.get_metrics_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    metrics.track_event('rate_limit_exceeded', {'description': str(e.description)})
    return jsonify({
        'error': 'Rate limit exceeded',
        'description': str(e.description)
    }), 429

if __name__ == '__main__':
    app.run(debug=True) 