from .translation_service import TranslationService

class TranslationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.translator = TranslationService()

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if hasattr(response, 'context_data'):
            current_language = request.LANGUAGE_CODE
            if current_language != 'en':
                # Translate messages if they exist
                if 'messages' in response.context_data:
                    for message in response.context_data['messages']:
                        message.message = self.translator.translate_text(
                            str(message.message),
                            current_language
                        )
        return response