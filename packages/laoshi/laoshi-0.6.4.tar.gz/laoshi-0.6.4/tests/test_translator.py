import unittest
from laoshi.translator import Translator


class TranslatorTest(unittest.TestCase):
    def test_translate(self):
        self.assertEqual(Translator().translate("你好,世界!"), "Hello World!")
