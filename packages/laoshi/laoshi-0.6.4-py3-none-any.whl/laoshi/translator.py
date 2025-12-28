"""Module for the Translator classes"""

from googletrans import Translator as GTranslator
import asyncio


class Translator:  # pylint: disable=too-few-public-methods
    """Translator class"""

    def __init__(self):
        """Initiliazer for Translator"""
        self.translator = GTranslator()

    async def translate_async(self, text: str, dest: str = "en") -> str:
        """Translate a text into english (by default)"""
        result = await self.translator.translate(text, dest=dest)
        return result.text

    def translate(self, text: str, dest: str = "en") -> str:
        return asyncio.run(self.translate_async(text, dest))
