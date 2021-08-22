from __future__ import annotations


def get_single_choice_category_value(category: dict) -> str:
    """sessionizeのAPIの返り値から単一選択項目の選択値を返す"""
    return category["categoryItems"][0]["name"]


class Category:
    @staticmethod
    def flatten_raw_json(categories: list[dict]) -> dict[str, str]:
        """sessionizeのAPIの返り値のうち、ネストしたcategoriesフィールドをパースして平坦にする"""
        for category in categories:
            if category["name"] == "Track":
                track = get_single_choice_category_value(category)
                continue
            if category["name"] == "Level":
                level = get_single_choice_category_value(category)
                continue
            if category["name"] == "Language":
                speaking_language = get_single_choice_category_value(category)
                continue
            if (
                category["name"]
                == "発表資料の言語 / Language of presentation material"
            ):
                slide_language = get_single_choice_category_value(category)
                continue
        return {
            "track": track,
            "level": level,
            "speaking_language": speaking_language,
            "slide_language": slide_language,
        }
