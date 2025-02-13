import google.generativeai as genai
from django.conf import settings

class ChatbotSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = FarmToHomeChatbot()
        return cls._instance

class FarmToHomeChatbot:
    def __init__(self):
        # Configure the API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Set up the model
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Define the context for the chatbot
        self.context = """You are a helpful assistant for the Farm to Home e-commerce platform.
        You help customers with:
        - Product information and availability
        - Order tracking and delivery status
        - Farming and produce questions
        - General customer service
        Always be polite, professional, and concise."""
        
        # Start a new chat
        self.chat = self.model.start_chat(history=[])

    def get_response(self, message):
        try:
            # Add context to the user's message
            prompt = f"{self.context}\n\nUser: {message}"
            
            # Get response from Gemini
            response = self.chat.send_message(prompt)
            
            return response.text
            
        except Exception as e:
            print(f"Error in Gemini API: {str(e)}")
            return "I apologize, but I'm having trouble processing your request. Please try again later."