# [missing-module-docstring]
import unittest
from laoshi import converter


class ConverterTest(unittest.TestCase):
    # [missing-class-docstring]
    def setUp(self):
        pass

    def test_to_traditional(self):  # [missing-function-docstring]
        self.assertEqual(converter.Converter.to_traditional("龙"), "龍")

    def test_to_simplified(self):  # [missing-function-docstring]
        self.assertEqual(converter.Converter.to_simplified("龍"), "龙")

    def test_to_pinyin(self):  # [missing-function-docstring]
        self.assertEqual(converter.Converter.to_pinyin("你好"), "nǐhǎo")
        self.assertEqual(converter.Converter.to_pinyin("你"), "nǐ")
