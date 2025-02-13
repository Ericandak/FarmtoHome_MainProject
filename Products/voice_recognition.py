import speech_recognition as sr
from django.http import JsonResponse
import spacy
from django.conf import settings

class VoiceRecognitionService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.nlp = spacy.load('en_core_web_sm')

    def process_text(self, text):
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract relevant entities and keywords
        keywords = []
        
        # Get product-related entities
        for ent in doc.ents:
            if ent.label_ in ['PRODUCT', 'ORG', 'NORP']:
                keywords.append(ent.text)
        
        # Get nouns and adjectives
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN', 'ADJ']:
                keywords.append(token.text)
        
        return list(set(keywords))

    def recognize_speech(self, audio_data):
        try:
            text = self.recognizer.recognize_google(audio_data)
            keywords = self.process_text(text)
            
            return {
                'success': True,
                'text': text,
                'keywords': keywords
            }
        except sr.UnknownValueError:
            return {
                'success': False,
                'error': 'Could not understand audio'
            }
        except sr.RequestError as e:
            return {
                'success': False,
                'error': f'Error with the speech recognition service: {str(e)}'
            }