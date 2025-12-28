import unittest
from laoshi import flashcardgenerator


class FlashCardGeneratorTest(unittest.TestCase):
    def test_from_traditional(self):
        with flashcardgenerator.FlashCardGenerator() as generator:
            flashcard = generator.from_traditional("龍")
            self.assertEqual("龙", flashcard.simplified)
            self.assertNotEqual(None, flashcard.sound_path)

    def test_from_simplified(self):
        with flashcardgenerator.FlashCardGenerator() as generator:
            flashcard = generator.from_simplified("龙")
            self.assertEqual("龍", flashcard.traditional)
