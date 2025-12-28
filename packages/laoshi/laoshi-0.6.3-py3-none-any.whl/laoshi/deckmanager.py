"""Module for managing decks in Anki"""

import json
import logging
import random
import os
import requests
import genanki
from laoshi.flashcardgenerator import FlashCard

FIELDS_LIST = [
    {"name": "Simplified"},
    {"name": "Traditional"},
    {"name": "Pinyin"},
    {"name": "Translation"},
    {"name": "Sound"},
]

MODEL_CSS = """
.card {
    font-family: arial;
    font-size: 48px;
    text-align: center;
    color: black;
    background-color: white;
    line-height: 2em;
}
"""

ANSWER = '{{FrontSide}}<hr id="answer">{{Simplified}}<br>{{Traditional}} \
<br>{{Pinyin}}<br>{{Translation}}</div><br>{{Sound}}</div>'

CHINESE_TO_ENGLISH = genanki.Model(
    1459389108,
    "Chinese to English",
    fields=FIELDS_LIST,
    css=MODEL_CSS,
    templates=[
        {
            "name": "Card {{Simplified}} English to Chinese",
            "qfmt": '<div class="card">{{Simplified}}<br>{{Traditional}}',
            "afmt": ANSWER,
        },
    ],
)

ENGLISH_TO_CHINESE = genanki.Model(
    1313378830,
    "English to Chinese",
    fields=FIELDS_LIST,
    css=MODEL_CSS,
    templates=[
        {
            "name": "Card {{Simplified}} English to Chinese",
            "qfmt": '<div class="card">{{Translation}}',
            "afmt": ANSWER,
        },
    ],
)

AUDIO_ONLY = genanki.Model(
    1280077338,
    "Audio Only",
    fields=FIELDS_LIST,
    css=MODEL_CSS,
    templates=[
        {
            "name": "Card {{Simplified}} Audio",
            "qfmt": '<div class="card">{{Sound}}',
            "afmt": ANSWER,
        },
    ],
)

WRITE = genanki.Model(
    1599105327,
    "Write Card",
    fields=FIELDS_LIST,
    css=MODEL_CSS,
    templates=[
        {
            "name": "Card Write",
            "qfmt": '<div class="card">{{Pinyin}}<br>{{Translation}}',
            "afmt": ANSWER,
        }
    ],
)


JSON_FIELDS_LIST = [
    {"name": "Traditional"},
    {"name": "Pinyin"},
    {"name": "PartOfSpeech"},
    {"name": "Meaning"},
    {"name": "Examples"},
    {"name": "Sound"},
]

JSON_MODEL_CSS = """
.card {
    font-family: arial;
    font-size: 24px;
    text-align: center;
    color: black;
    background-color: white;
    line-height: 1.5em;
}
.hanzi {
    font-size: 48px;
}
"""

JSON_ANSWER = '{{FrontSide}}<hr id="answer">{{PartOfSpeech}}<br>{{Meaning}}<br><br>{{Examples}}<br>{{Sound}}'

JSON_CARD_MODEL = genanki.Model(
    1849389109,
    "JSON Card Model",
    fields=JSON_FIELDS_LIST,
    css=JSON_MODEL_CSS,
    templates=[
        {
            "name": "Card JSON",
            "qfmt": '<div class="card"><div class="hanzi">{{Traditional}}</div><br>{{Pinyin}}</div>',
            "afmt": JSON_ANSWER,
        },
    ],
)


def get_unique_id() -> int:
    """Creates a unique ID"""
    return random.randrange(1 << 30, 1 << 31)


class DeckManager:
    """Manages and creates Anki Decks"""

    def __init__(self, deck_name: str, base_url: str = "http://localhost:8765"):
        """Init method"""
        self.deck_name = deck_name
        self.base_url = base_url
        self._json_model_verified = False

    def create_deck(self, flashcard: FlashCard):
        """Creates a deck from one FlashCard"""
        deck = genanki.Deck(get_unique_id(), self.deck_name)
        package = genanki.Package(deck)
        output = f"{deck.name}.apkg"
        deck.add_note(
            genanki.Note(
                guid=get_unique_id(),
                model=CHINESE_TO_ENGLISH,
                fields=flashcard.get_fields(),
            )
        )
        deck.add_note(
            genanki.Note(
                guid=get_unique_id(),
                model=ENGLISH_TO_CHINESE,
                fields=flashcard.get_fields(),
            )
        )
        deck.add_note(
            genanki.Note(
                guid=get_unique_id(), model=AUDIO_ONLY, fields=flashcard.get_fields()
            )
        )
        deck.add_note(
            genanki.Note(
                guid=get_unique_id(), model=WRITE, fields=flashcard.get_fields()
            )
        )
        package.media_files = [flashcard.get_media_path()]
        package.write_to_file(output)

    def add_note(self, flashcard: FlashCard):
        """Adds a flashcard to the deck"""
        for model in [CHINESE_TO_ENGLISH, ENGLISH_TO_CHINESE, AUDIO_ONLY, WRITE]:
            fjson = self.create_json(flashcard, model.name).encode("utf8")
            result = requests.post(self.base_url, fjson, timeout=30)
            if result.status_code != 200:
                logging.warning(
                    f"Error creating note {flashcard.simplified}!" + f"{result.reason}"
                )

    def add_json_note(self, flashcard: FlashCard):
        """Adds a json flashcard to the deck"""
        if not self._json_model_verified:
            self._ensure_json_model()
            self._json_model_verified = True

        fjson = self.create_json(flashcard, JSON_CARD_MODEL.name).encode("utf8")
        response = requests.post(self.base_url, fjson, timeout=30)
        self._check_response(response, flashcard.traditional)

    def _ensure_json_model(self):
        """Ensures that the JSON model exists in Anki"""
        payload = {"action": "modelNames", "version": 6}
        try:
            res = requests.post(self.base_url, json=payload, timeout=30)
            data = res.json()
            if JSON_CARD_MODEL.name in data.get("result", []):
                return

            # Create model
            tmpls = []
            for t in JSON_CARD_MODEL.templates:
                tmpls.append(
                    {
                        "Name": t["name"],
                        "Front": t["qfmt"],
                        "Back": t["afmt"],
                    }
                )

            create_payload = {
                "action": "createModel",
                "version": 6,
                "params": {
                    "modelName": JSON_CARD_MODEL.name,
                    "inOrderFields": [f["name"] for f in JSON_CARD_MODEL.fields],
                    "css": JSON_CARD_MODEL.css,
                    "cardTemplates": tmpls,
                },
            }
            res = requests.post(self.base_url, json=create_payload, timeout=30)
            self._check_response(res, "Model Creation")
        except Exception as e:
            logging.warning(f"Error ensuring model: {e}")
            # We don't raise here, we let add_note fail if model is missing,
            # but usually this means Anki is not reachable.

    def _check_response(self, response, context):
        if response.status_code != 200:
            raise Exception(f"{context}: HTTP {response.status_code}")
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise Exception(f"{context}: Invalid JSON response")

        if data.get("error"):
            raise Exception(f"{context}: {data['error']}")

    def create_json(self, flashcard: FlashCard, model_name: str) -> str:
        """Creates a json from a flashcard object with the model name"""
        result = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": {
                    "deckName": self.deck_name,
                    "modelName": model_name,
                    "fields": self._get_fields_for_model(flashcard, model_name),
                    "options": {
                        "allowDuplicate": False,
                        "duplicateScope": "deck",
                        "duplicateScopeOptions": {
                            "deckName": "Default",
                            "checkChildren": False,
                            "checkAllModels": False,
                        },
                    },
                    "tags": [],
                    "audio": [
                        {
                            "path": flashcard.sound_path,
                            "filename": flashcard.sound_file,
                            "fields": ["Sound"],
                        }
                    ],
                }
            },
        }
        return json.dumps(result, ensure_ascii=False)

    def _get_fields_for_model(self, flashcard: FlashCard, model_name: str) -> dict:
        """Returns the fields dictionary based on the model name"""
        if model_name == JSON_CARD_MODEL.name:
            return {
                "Traditional": flashcard.traditional,
                "Pinyin": flashcard.pinyin,
                "PartOfSpeech": flashcard.part_of_speech,
                "Meaning": flashcard.translation,
                "Examples": "<br>".join(flashcard.example_sentences),
            }
        return {
            "Simplified": flashcard.simplified,
            "Traditional": flashcard.traditional,
            "Pinyin": flashcard.pinyin,
            "Translation": flashcard.translation,
        }

    def close(self):
        """Deletes the deck if needed"""
        output = f"{self.deck_name}.apkg"
        if os.path.exists(output):
            os.remove(output)
