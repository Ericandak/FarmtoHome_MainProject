import requests
from django.core.cache import cache
from django.conf import settings
import hashlib

class TranslationService:
    def __init__(self):
        # You can change this URL to other public instances if needed
        self.API_URL = "https://libretranslate.de/translate"
        self.CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours cache

    def _get_cache_key(self, text, target_language):
        """Generate a cache key for the translation."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"trans_{target_language}_{text_hash}"

    def translate_text(self, text, target_language='ml', source_language='en', use_cache=True):
        """
        Translate text using LibreTranslate API
        """
        if not text or not text.strip():
            return text

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(text, target_language)
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result

        try:
            payload = {
                "q": text,
                "source": source_language,
                "target": target_language,
                "format": "text"
            }
            
            response = requests.post(self.API_URL, json=payload)
            response.raise_for_status()  # Raise exception for bad status codes
            
            result = response.json()
            translated_text = result.get('translatedText', text)

            # Cache the successful translation
            if use_cache and translated_text != text:
                cache.set(cache_key, translated_text, self.CACHE_TIMEOUT)

            return translated_text

        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails

    def translate_dict(self, data_dict, fields_to_translate, target_language='ml'):
        """
        Translate specific fields in a dictionary
        """
        translated_dict = data_dict.copy()
        for field in fields_to_translate:
            if field in data_dict and data_dict[field]:
                translated_dict[field] = self.translate_text(str(data_dict[field]), target_language)
        return translated_dict