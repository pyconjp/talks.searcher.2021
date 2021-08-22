from __future__ import annotations

from dataclasses import dataclass


def get_single_choice_category_value(category: dict) -> str:
    """sessionizeのAPIの返り値から単一選択項目の選択値を返す"""
    return category["categoryItems"][0]["name"]


@dataclass
class Speaker:
    name: str


@dataclass
class Category:
    track: str
    level: str
    speaking_language: str
    slide_language: str

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

    @classmethod
    def from_raw_json(cls, categories):
        return cls(**cls.flatten_raw_json(categories))


class QuestionAnswer:
    @staticmethod
    def flatten_raw_json(question_answers: list[dict]) -> dict[str, str]:
        for qa in question_answers:
            if qa["question"] == "Elevator Pitch":
                elevator_pitch = qa["answer"]
                continue
            if qa["question"] == "オーディエンスに求める前提知識":
                audience_prior_knowledge = qa["answer"]
                continue
            if qa["question"] == "オーディエンスが持って帰れる具体的な知識やノウハウ":
                audience_take_away = qa["answer"]
                continue
        return {
            "elevator_pitch": elevator_pitch,
            "audience_prior_knowledge": audience_prior_knowledge,
            "audience_take_away": audience_take_away,
        }
