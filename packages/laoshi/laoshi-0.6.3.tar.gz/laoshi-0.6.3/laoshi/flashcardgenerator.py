"""Module which provides the FlashCard generator class."""

import tempfile
import uuid
import os
import shutil
from laoshi.converter import Converter
from laoshi.translator import Translator
from laoshi.speaker import Speaker, Speech


class FlashCard:
    """Class which holds all the information needed for
    flashcards
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        simplified: str,
        traditional: str,
        pinyin: str,
        translation: str,
        sound_file: str,
        sound_path: str,
        part_of_speech: str = "",
        example_sentences: list[str] = None,
    ):
        self.simplified = simplified
        self.traditional = traditional
        self.pinyin = pinyin
        self.translation = translation
        self.sound_file = sound_file
        self.sound_path = sound_path
        self.part_of_speech = part_of_speech
        self.example_sentences = example_sentences if example_sentences else []

    def get_fields(self) -> list[str]:
        """Get fields from Flashcard except from sound files."""
        return [
            self.simplified,
            self.traditional,
            self.pinyin,
            self.translation,
            self.sound_file,
        ]

    def get_json_fields(self) -> list[str]:
        """Get fields for JSON model."""
        # Joining example sentences with <br> for display
        examples_str = "<br>".join(self.example_sentences)
        return [
            # Id field is not stored in flashcard, will be passed separately or generated
            # But the model expects: Id, Traditional, Pinyin, PartOfSpeech, Definition, ExampleSentences, Sound
            # Wait, DeckManager creates the Note.
            # Let's return the content fields.
            self.traditional,
            self.pinyin,
            self.part_of_speech,
            self.translation,  # Mapping 'english_definition' to 'translation'
            examples_str,
            self.sound_file,
        ]

    def get_media_path(self) -> str:
        """Get media path"""
        return self.sound_path


class FlashCardGenerator:
    """Generates flashcards"""

    def __init__(self, tempfolder: str = ""):
        """
        Parameters:
            self: The instantiated object
            tempfolder: Folder to use to save the audio files.
        """
        self.tempfolder = tempfolder

    def __enter__(self):
        """
        It creates the temporary folder when using it when the with statement
        """
        self.tempfolder = tempfile.mkdtemp()
        return self

    def create_sound(self, hanzitext: str) -> Speech:
        """
        Creates a sound in a temporal folder.
        Parameters:
            self (FlashCardGenerator): the instantiated object.
            hanzitext (str): Chinese text
        Returns:
            Speech: The saved speech object
        """
        speech: Speech = Speaker.text_to_speech(hanzitext)
        name = f"{str(uuid.uuid4())}.mp3"
        path = f"{self.tempfolder}/{name}"
        speech.save(f"[sound:{name}]", path)
        return speech

    def create_flashcard(self, character: str, hanzi: str) -> FlashCard:
        """Create FlashCard"""
        match character:
            case "simplified":
                return self.from_simplified(hanzi)
            case "traditional":
                return self.from_traditional(hanzi)

    def from_traditional(self, hanzi: str) -> FlashCard:
        """
        Creates a FlashCard from a traditional text
        Parameters:
            self: The object
            hanzi: Traditional chinese text
        Returns:
            FlashCard: Returns an instantiated FlashCard
        """
        speech: Speech = self.create_sound(hanzi)
        return FlashCard(
            simplified=Converter.to_simplified(hanzi),
            traditional=hanzi,
            pinyin=Converter.to_pinyin(hanzi),
            translation=Translator().translate(hanzi),
            sound_path=speech.path,
            sound_file=speech.name,
        )

    def from_simplified(self, hanzi: str) -> FlashCard:
        """
        Creates a FlashCard from a traditional text
        Parameters:
            self: The object
            hanzi: Simplified chinese text
        Returns:
            FlashCard: Returns an instantiated FlashCard
        """
        speech: Speech = self.create_sound(hanzi)
        return FlashCard(
            simplified=hanzi,
            traditional=Converter.to_traditional(hanzi),
            pinyin=Converter.to_pinyin(hanzi),
            translation=Translator().translate(hanzi),
            sound_path=speech.path,
            sound_file=speech.name,
        )

    def from_json_entry(self, entry: dict) -> FlashCard:
        """
        Creates a FlashCard from a JSON entry.
        Expected schema:
        {
            "id": int,
            "traditional_chinese": str,
            "pinyin": str,
            "part_of_speech": str,
            "english_definition": str,
            "example_sentences": [str]
        }
        """
        hanzi = entry.get("traditional_chinese", "")
        speech: Speech = self.create_sound(hanzi)
        return FlashCard(
            simplified="",  # Not used in this model explicitly
            traditional=hanzi,
            pinyin=entry.get("pinyin", ""),
            translation=entry.get("english_definition", ""),
            sound_path=speech.path,
            sound_file=speech.name,
            part_of_speech=entry.get("part_of_speech", ""),
            example_sentences=entry.get("example_sentences", []),
        )

    def __exit__(self, *_args):
        """
        Needed to delete the temporary folder when exiting a with statement.
        """
        if os.path.exists(self.tempfolder):
            shutil.rmtree(self.tempfolder)
