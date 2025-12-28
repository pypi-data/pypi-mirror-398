"""Text to speech module"""

from io import BytesIO
from gtts import gTTS


class Speech:
    """Result class from the text speech module"""

    def __init__(self, text: str, lang: str = "zh"):
        """Initializer method for Speech"""
        self.speech = gTTS(text, lang=lang)
        self.path = None
        self.name = None

    def save(self, name: str, path: str):
        """Save speech into an mp3"""
        self.speech.save(path)
        self.name = name
        self.path = path

    def get_sound(self) -> BytesIO:
        """Get sound as Bytes"""
        sound = BytesIO()
        self.speech.write_to_fp(sound)
        return sound


class Speaker:  # pylint: disable=too-few-public-methods
    """Main class for speaker module"""

    @staticmethod
    def text_to_speech(text: str) -> Speech:
        """Main function for speaker module"""
        return Speech(text)
