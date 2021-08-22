from unittest import TestCase

from app import Category


class CategoryTestCase(TestCase):
    def test_flatten_raw_json(self):
        categories = [
            {
                "name": "Track",
                "categoryItems": [{"name": "Python core and around"}],
            },
            {
                "name": "Level",
                "categoryItems": [{"name": "Intermediate"}],
            },
            {
                "name": "Language",
                "categoryItems": [{"name": "Japanese"}],
            },
            {
                "name": "発表資料の言語 / Language of presentation material",
                "categoryItems": [{"name": "Both"}],
            },
        ]
        expected = {
            "track": "Python core and around",
            "level": "Intermediate",
            "speaking_language": "Japanese",
            "slide_language": "Both",
        }

        actual = Category.flatten_raw_json(categories)

        self.assertEqual(actual, expected)
