import re
from collections import Counter
import streamlit as st
import requests
import os

class SpellCorrector:
    def __init__(self, corpus_path):
        self.words = self._load_corpus(corpus_path)
        self.word_counts = Counter(self.words)
        self.total_words = sum(self.word_counts.values())

    @st.cache_data
    def _load_corpus(_self, source):
        """Loads and tokenizes the corpus from a local path or URL."""
        try:
            if str(source).startswith(('http://', 'https://')):
                response = requests.get(source, stream=True)
                response.raise_for_status()
                # For 87MB, downloading and decoding is efficient in memory
                text = response.content.decode('utf-8').lower()
                return re.findall(r'\w+', text)
            else:
                with open(source, 'r', encoding='utf-8') as f:
                    return re.findall(r'\w+', f.read().lower())
        except Exception as e:
            st.error(f"Error loading corpus from {source}: {e}")
            return []

    def normalize_word(self, word):
        """Reduces sequences of 3 or more repeated characters to 2 (e.g., 'heelllooooo' -> 'helloo')."""
        return re.sub(r'(.)\1{2,}', r'\1\1', word)

    def P(self, word):
        """Probability of 'word'."""
        return self.word_counts[word] / self.total_words if self.total_words > 0 else 0

    def correction(self, word):
        """Most probable spelling correction for word."""
        return max(self.candidates(word), key=self.P)

    def candidates(self, word):
        """Generate possible spelling corrections for word."""
        return (self.known([word]) or self.known(self.edits1(word)) or self.known(self.edits2(word)) or [word])

    def known(self, words):
        """The subset of `words` that appear in the dictionary of word_counts."""
        return set(w for w in words if w in self.word_counts)

    def edits1(self, word):
        """All edits that are one edit away from `word`."""
        letters    = 'abcdefghijklmnopqrstuvwxyz'
        splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
        deletes    = [L + R[1:]               for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
        replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
        inserts    = [L + c + R               for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def edits2(self, word):
        """All edits that are two edits away from `word`."""
        return (e2 for e1 in self.edits1(word) for e2 in self.edits1(e1))

    def get_correction(self, word):
        """
        Returns (corrected_word, confidence, is_error)
        Always returns a tuple, never None.
        """
        try:
            word = word.lower()
            if word in self.word_counts:
                return word, 1.0, False
            
            # Apply normalization for unknown words with repeated characters
            normalized = self.normalize_word(word)
            if normalized != word:
                word = normalized
            
            candidates = self.candidates(word)
            if not candidates:
                return word, 0, False
                
            best_candidate = max(candidates, key=self.P)
            # Calculate simple confidence
            total_p = sum(self.P(c) for c in candidates)
            confidence = self.P(best_candidate) / total_p if total_p > 0 else 0
            
            return best_candidate, round(confidence, 4), True
        except Exception:
            # If anything fails, return original word
            return word, 0, False

    def correct(self, word):
        """Alias for correction() for compatibility."""
        return self.correction(word)
