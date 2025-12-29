from deep_translator import GoogleTranslator

class Translator:
    """A simple translator tool using Google Translate.
    Args:
        source_lang (str): The source language code (default is 'auto' for auto-detection).
        target_lang (str): The target language code (default is 'en' for English).
    Returns:
        str: Translated text.
    Raises:
        Exception: If translation fails.
    """

    def __init__(self, source_lang: str = 'auto', target_lang: str = 'en'):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)
        self.description = "A tool for translating text from source language to target language."

    def run(self, text: str) -> str:
        try:
            translated_text = self.translator.translate(text)
            return translated_text
        except Exception as e:
            print(f"Translation error: {e}")
            return text