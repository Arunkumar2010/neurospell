import torch
from transformers import pipeline
import streamlit as st

class ContextCorrector:
    def __init__(self, model_name="distilbert-base-uncased"):
        self.model_name = model_name
        self.unmasker = self._load_model()

    @st.cache_resource
    def _load_model(_self):
        """Loads DistilBERT pipeline."""
        try:
            return pipeline("fill-mask", model=_self.model_name)
        except Exception as e:
            st.error(f"Error loading DistilBERT model: {e}")
            return None

    def check_context(self, words, index):
        """
        Masks the word at the given index and checks if it's correct.
        Returns (top_prediction, confidence, is_real_word_error)
        """
        if not self.unmasker:
            return words[index], 0.0, False
            
        original_word = words[index].lower()
        # Create masked sentence
        masked_sentence = " ".join([words[i] if i != index else "[MASK]" for i in range(len(words))])
        
        # Limit sentence length for model performance
        if len(masked_sentence.split()) > 100:
            return original_word, 1.0, False
            
        try:
            predictions = self.unmasker(masked_sentence)
            top_prediction = predictions[0]['token_str'].lower().strip()
            top_score = predictions[0]['score']
            
            # Find current word score in predictions
            current_score = next((p['score'] for p in predictions if p['token_str'].lower().strip() == original_word), 0)
            
            is_punctuation = not any(c.isalnum() for c in top_prediction)
            is_too_short = len(top_prediction) < 2
            
            # IMPROVED SENSITIVITY:
            # If the current word's probability is very low (< 5%) 
            # and the top predicted word is quite likely (> 40%)
            # and not the same word, flag as a real-word error.
            if current_score < 0.05 and top_score > 0.4 and top_prediction != original_word and not is_punctuation and not is_too_short:
                return top_prediction, round(top_score, 4), True
                
            return original_word, round(current_score, 4), False
        except Exception as e:
            st.warning(f"Neural Analysis Exception at index {index}: {e}")
            return original_word, 1.0, False

    def correct_text(self, text):
        """High-level call for full text analysis."""
        words = text.split()
        corrected_words = []
        for i in range(len(words)):
            pred, conf, is_err = self.check_context(words, i)
            corrected_words.append(pred if is_err else words[i])
        return " ".join(corrected_words)
