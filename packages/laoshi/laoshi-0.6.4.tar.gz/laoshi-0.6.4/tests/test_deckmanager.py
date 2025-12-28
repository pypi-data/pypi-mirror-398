import unittest
from unittest.mock import patch
import os
from laoshi.flashcardgenerator import FlashCardGenerator
from laoshi import deckmanager


class DeckManagerTest(unittest.TestCase):
    def setUp(self):
        self.deck_manager = deckmanager.DeckManager("test")

    def tearDown(self):
        self.deck_manager.close()

    def test_create_deck(self):
        with FlashCardGenerator() as generator:
            self.deck_manager.create_deck(generator.from_simplified("龙"))
            output = f"{self.deck_manager.deck_name}.apkg"
            self.assertTrue(os.path.exists(output))

    @patch("laoshi.deckmanager.requests.post")
    def test_add_note(self, _post):
        with FlashCardGenerator() as generator:
            self.deck_manager.create_deck(generator.from_simplified("龙"))
            self.deck_manager.add_note(generator.from_simplified("咖啡"))

    def test_create_json(self):
        with FlashCardGenerator() as generator:
            r = self.deck_manager.create_json(
                generator.from_simplified("龙"), "CHINESE"
            )
            self.assertNotEqual(None, r)

    def test_unique_id(self):
        self.assertNotEqual(deckmanager.get_unique_id(), deckmanager.get_unique_id())
