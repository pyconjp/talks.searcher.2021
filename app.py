from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.request import urlopen

import streamlit as st
import streamlit.components.v1 as components


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

    @st.cache
    def filter_by(self, request: dict) -> "Talks":
        talks = self.talks
        if request["tracks"]:
            talks = [t for t in talks if t.category.track in request["tracks"]]
        if request["levels"]:
            talks = [t for t in talks if t.category.level in request["levels"]]
        if request["keywords"]:
            # AND検索。case-insensitive。
            # タイトル・エレベータピッチ・前提知識・持ち帰れるものの部分文字列か（詳細は使っていない）
            for keyword in request["keywords"]:
                talks = [
                    t
                    for t in talks
                    if keyword
                    in "\n".join(
                        [
                            t.title,
                            t.answer.elevator_pitch,
                            t.answer.audience_prior_knowledge,
                            t.answer.audience_take_away,
                        ]
                    ).lower()
                ]
        if request["is_english_only"]:
            talks = [
                t
                for t in talks
                # speaking_language は Japanese / English
                if t.category.speaking_language == "English"
                # slide_language は Japanese only / English only / Both
                or t.category.slide_language != "Japanese only"
            ]
        return self.__class__(talks)


# ---------- Variables and functions to be used in Streamlit app ----------

TRACKS = (
    "Python core and around",
    "Machine learning",
    "Web programming",
    "Visual / Game / Music",
    "Outside of Python language",
    "Approaching to social problem",
    "Only for fun or try new technique",
    "Anything else basically which doesn’t fall into the types "
    "of topics above",
)
PYTHON_LEVELS = ("Beginner", "Intermediate", "Advanced", "Expert")


@st.cache
def fetch_talks(url):
    with urlopen(url) as res:
        data = json.load(res)
    assert len(data) == 1, len(data)
    return data


CARD_HTML_TEMPLATE = """
<div class="card p-3">
  <h5 class="card-title">{title} (by {speakers})</h5>
  <div class="p-2 bg-light">
    <h6 class="card-subtitle mb-2 text-muted">{elevator_pitch}</h6>
  </div>
  <div>
    <dl>
      <dt>Track</dt>
      <dd class="p-2">
        <span class="badge rounded-pill bg-info text-dark">{track}</span>
      </dd>
      <dt>Python knowledge of audience</dt>
      <dd class="p-2">{python_level}</dd>
      <dt>Language</dt>
      <dd class="p-2">
        {speaking_language} (Speak) / {slide_language} (Material)
      </dd>
      <dt>Prior knowledges speakers assume the audience to have / 前提知識</dt>
      <dd class="p-3 bg-light">{audience_prior_knowledge}</dd>
      <dt>Knowledges and know-how the audience can get from talk
      / 持ち帰れる知識・ノウハウ</dt>
      <dd class="p-3 bg-light">{audience_take_away}</dd>
    </dl>
  </div>

  <p>
    <a class="btn btn-primary" data-bs-toggle="collapse"
        href="#collapseDetail{i}" role="button" aria-expanded="false"
        aria-controls="collapseExample">
      Detail
    </a>
  </p>
  <div class="collapse" id="collapseDetail{i}">
    <div class="card card-body bg-light">
      {description}
    </div>
  </div>
</div>
"""


@st.cache
def cards_html_to_talks(talks):
    return "\n".join(
        CARD_HTML_TEMPLATE.format(
            i=i,
            title=talk.title,
            speakers=", ".join(speaker.name for speaker in talk.speakers),
            track=talk.category.track,
            python_level=talk.category.level,
            speaking_language=talk.category.speaking_language,
            slide_language=talk.category.slide_language,
            description=talk.description.replace("\r\n", "<br>"),
            elevator_pitch=talk.answer.elevator_pitch,
            audience_prior_knowledge=talk.answer.audience_prior_knowledge.replace(  # NOQA
                "\r\n", "<br>"
            ),
            audience_take_away=talk.answer.audience_take_away.replace(
                "\r\n", "<br>"
            ),
        )
        for i, talk in enumerate(talks)
    )


# ---------- Streamlit app ----------

endpoint_id = st.secrets["ENDPOINT_ID"]
url = f"https://sessionize.com/api/v2/{endpoint_id}/view/Sessions"

st.title("May you find great talks.")

data_load_state = st.text("Loading Data...")
data = fetch_talks(url)
talks = Talks.from_raw_json(data[0]["sessions"])
data_load_state.text("Loading Data... Done!")

selected_tracks = st.multiselect("Select track", TRACKS)
selected_levels = st.multiselect("Select audience Python level", PYTHON_LEVELS)
keyword_input = st.text_input("Keyword in title")
is_english_only = st.checkbox("Only English talks")

request = {
    "tracks": set(selected_tracks),
    "levels": set(selected_levels),
    "keywords": set(keyword_input.strip().lower().split()),
    "is_english_only": is_english_only,
}
talks = talks.filter_by(request)

st.write("Found:", len(talks))

cards_html = cards_html_to_talks(talks)
components.html(
    f"""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"
      rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js"
      integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>

    {cards_html}
    """,
    height=1000,
    scrolling=True,
)
