from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.request import urlopen

import streamlit as st


def get_single_choice_category_value(category: dict) -> str:
    """sessionizeのAPIの返り値から単一選択項目の選択値を返す"""
    return category["categoryItems"][0]["name"]


# ---------- Definition of Custom classes ----------


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


@dataclass
class QuestionAnswer:
    elevator_pitch: str
    audience_prior_knowledge: str
    audience_take_away: str

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

    @classmethod
    def from_raw_json(cls, question_answers):
        return cls(**cls.flatten_raw_json(question_answers))


@dataclass
class Talk:
    id: int
    title: str
    description: str
    category: Category
    answer: QuestionAnswer
    speakers: list[Speaker]


@dataclass
class Talks(Sequence):
    talks: list[Talk]

    def __len__(self):
        return len(self.talks)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__class__(self.talks[key])
        return self.talks[key]

    @classmethod
    @st.cache
    def from_raw_json(cls, data):
        talks = []
        for session in data:
            speakers = [
                Speaker(speaker["name"]) for speaker in session["speakers"]
            ]
            category = Category.from_raw_json(session["categories"])
            question_answers = QuestionAnswer.from_raw_json(
                session["questionAnswers"]
            )
            talk = Talk(
                int(session["id"]),
                session["title"],
                session["description"],
                category,
                question_answers,
                speakers,
            )
            talks.append(talk)
        return cls(sorted(talks, key=lambda t: t.id))


# ---------- Functions to be used in Streamlit app ----------


@st.cache
def fetch_talks(url):
    with urlopen(url) as res:
        data = json.load(res)
    assert len(data) == 1, len(data)
    return data


# ---------- Streamlit app ----------

endpoint_id = st.secrets["ENDPOINT_ID"]
url = f"https://sessionize.com/api/v2/{endpoint_id}/view/Sessions"

st.title("May you find great talks.")

data_load_state = st.text("Loading Data...")
data = fetch_talks(url)
talks = Talks.from_raw_json(data[0]["sessions"])
data_load_state.text("Loading Data... Done!")

st.write("Found:", len(talks))
