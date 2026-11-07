"""Onboarding to a persona. Two modes: quick-pick chips (no LLM) or a short chat (LLM extracts)."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

try:
    from . import llm
except ImportError:
    import llm

TAGS = ["revenge", "romance", "family drama", "thriller", "mystery", "comedy", "hidden identity", "rich-poor",
        "marriage", "betrayal", "action", "fantasy", "royal/historical", "mafia/crime", "saas-bahu", "office"]

QUESTIONS = {
    "hinglish": ["Aap kaun ho? (student, homemaker, job karte ho...)",
                 "Din mein kab free hote ho? (jaise subah 8 baje, raat 9 baje)",
                 "Kaisi kahaniyan pasand hain?",
                 "Kya bilkul nahi dekhna?",
                 "Akele dekhte ho ya family ke saath?"],
    "english": ["Who are you? (student, homemaker, working...)",
                "When are you free in the day? (e.g. 8 am, 9 pm)",
                "What kind of stories do you like?",
                "Anything you never want to watch?",
                "Do you watch alone or with family?"],
}


class Persona(BaseModel):
    who: str = "viewer"
    age_band: str = "unknown"
    city_tier: str = "unknown"
    language: Literal["hinglish", "english"] = "english"
    slots: list[str] = Field(default_factory=lambda: ["20:00"])
    likes: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    watch_with: Literal["alone", "family", "partner", "unknown"] = "unknown"
    minutes_per_day: int = 15
    summary: str = ""

    @field_validator("likes", "dislikes")
    @classmethod
    def known_tags(cls, v):
        return [t for t in v if t in TAGS]  # drop anything outside the shared vocabulary

    @field_validator("who", "age_band", "city_tier", "summary", mode="before")
    @classmethod
    def text(cls, v, info):
        return str(v)[:120] if isinstance(v, (str, int, float)) else cls.model_fields[info.field_name].default

    @field_validator("slots", "likes", "dislikes", mode="before")
    @classmethod
    def as_list(cls, v):
        return [str(x) for x in v] if isinstance(v, list) else ([v] if isinstance(v, str) else [])

    @field_validator("minutes_per_day", mode="before")
    @classmethod
    def minutes(cls, v):
        try:
            return max(5, min(120, int(v)))
        except (TypeError, ValueError):  # models answer "unknown" when the viewer did not say
            return 15

    @field_validator("watch_with", "language", mode="before")
    @classmethod
    def known_choice(cls, v, info):
        allowed = {"watch_with": ("alone", "family", "partner"), "language": ("hinglish", "english")}[info.field_name]
        v = str(v or "").lower()
        return v if v in allowed else ("unknown" if info.field_name == "watch_with" else "english")

    @model_validator(mode="after")
    def dislikes_win(self):
        self.likes = [t for t in self.likes if t not in self.dislikes]  # "I like revenge" + "I hate revenge": stay safe
        return self

    @field_validator("slots")
    @classmethod
    def hhmm(cls, v):
        ok = [s for s in v if len(s) == 5 and s[2] == ":" and s[:2].isdigit() and s[3:].isdigit() and int(s[:2]) < 24 and int(s[3:]) < 60]
        return ok[:2] or ["20:00"]


def quick(who, likes, dislikes=(), slots=("20:00",), language="english", watch_with="unknown"):
    return Persona(who=who, likes=list(likes), dislikes=list(dislikes), slots=list(slots),
                   language=language, watch_with=watch_with,
                   summary=f"{who} who likes {', '.join(likes) or 'anything'}")


SYSTEM = ("You turn a new viewer's onboarding answers into a profile for a microdrama app in India. "
          "Use only what they said; write 'unknown' when they did not say it. Return JSON only.")


def extract(answers: list, language="english") -> Persona:
    qa = "\n".join(f"Q: {q}\nA: {a}" for q, a in zip(QUESTIONS[language], answers))
    prompt = (f"{qa}\n\nReturn JSON with keys: who, age_band (18-24|25-34|35-50|50+|unknown), "
              f"city_tier (metro|tier2|tier3|unknown), slots (list of 24h 'HH:MM', max 2), "
              f"likes and dislikes (only from {TAGS}), watch_with (alone|family|partner|unknown), "
              f"minutes_per_day (int), summary (one line in {'Hinglish' if language == 'hinglish' else 'English'}).")
    data = llm.complete(prompt, system=SYSTEM, want_json=True, task="persona")
    data["language"] = language
    return Persona.model_validate(data)
