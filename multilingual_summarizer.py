from transformers import MarianMTModel, MarianTokenizer
import torch
from typing import List, Dict
import logging

class MultilingualSummarizer:
    def __init__(self):
        self.models: Dict[str, MarianMTModel] = {}
        self.tokenizers: Dict[str, MarianTokenizer] = {}
        self.supported_languages = {
            'es': 'Helsinki-NLP/opus-mt-es-en',  # Spanish
            'fr': 'Helsinki-NLP/opus-mt-fr-en',  # French
            'de': 'Helsinki-NLP/opus-mt-de-en',  # German
            'it': 'Helsinki-NLP/opus-mt-it-en',  # Italian
            'pt': 'Helsinki-NLP/opus-mt-pt-en',  # Portuguese
        }
        
        # Set up logging
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
    
    def load_model(self, lang_code: str):
        """Load translation model for a specific language."""
        try:
            if lang_code not in self.models:
                model_name = self.supported_languages.get(lang_code)
                if not model_name:
                    raise ValueError(f"Language code '{lang_code}' not supported")
                
                logging.info(f"Loading model for language: {lang_code}")
                self.tokenizers[lang_code] = MarianTokenizer.from_pretrained(model_name)
                self.models[lang_code] = MarianMTModel.from_pretrained(model_name)
                logging.info(f"Successfully loaded model for {lang_code}")
        except Exception as e:
            logging.error(f"Error loading model for {lang_code}: {str(e)}")
            raise
    
    def translate_to_english(self, text: str, source_lang: str) -> str:
        """Translate text to English."""
        try:
            if source_lang not in self.models:
                self.load_model(source_lang)
            
            tokenizer = self.tokenizers[source_lang]
            model = self.models[source_lang]
            
            # Tokenize and translate
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            translated = model.generate(**inputs)
            result = tokenizer.decode(translated[0], skip_special_tokens=True)
            
            return result
            
        except Exception as e:
            logging.error(f"Translation error: {str(e)}")
            raise
    
    def summarize_multilingual(self, text: str, source_lang: str, summarizer, n_sentences: int = 5) -> dict:
        """Summarize text in any supported language."""
        try:
            # Translate to English if not already in English
            if source_lang != 'en':
                english_text = self.translate_to_english(text, source_lang)
            else:
                english_text = text
            
            # Generate summary in English
            english_summary = summarizer.extractive_summarize(english_text, n_sentences)
            
            return {
                'original_text': text,
                'english_translation': english_text if source_lang != 'en' else None,
                'summary': english_summary
            }
            
        except Exception as e:
            logging.error(f"Summarization error: {str(e)}")
            raise 