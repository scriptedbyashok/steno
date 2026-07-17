from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Dictation(BaseModel):
    id: UUID
    title: str
    audio_path: str
    transcript: str
    time_limit_seconds: int | None = None
    created_at: datetime


class DictationCard(BaseModel):
    """Dictation shape safe to send to the browser — excludes transcript."""

    id: UUID
    title: str
    time_limit_seconds: int | None = None
    created_at: datetime
    audio_duration_seconds: int | None = None
    attempt_count: int = 0
    best_accuracy: float | None = None
    last_attempt_at: datetime | None = None


class DictationDetail(DictationCard):
    """Single-dictation shape: card fields + a signed, time-limited audio URL."""

    audio_url: str


class WordDiffItem(BaseModel):
    word: str
    status: Literal["correct", "wrong", "missed", "extra"]
    typed: str | None = None


class Attempt(BaseModel):
    id: UUID
    dictation_id: UUID
    typed_text: str
    accuracy: float
    total_words: int | None = None
    correct: int | None = None
    wrong: int | None = None
    missed: int | None = None
    extra: int | None = None
    time_taken_seconds: int | None = None
    word_diff: list[WordDiffItem] | None = None
    created_at: datetime


class AttemptSummary(BaseModel):
    """Attempt history entry — omits typed_text (not needed for the list view)."""

    id: UUID
    accuracy: float
    total_words: int | None = None
    correct: int | None = None
    wrong: int | None = None
    missed: int | None = None
    extra: int | None = None
    time_taken_seconds: int | None = None
    word_diff: list[WordDiffItem] | None = None
    created_at: datetime


class SubmitRequest(BaseModel):
    typed_text: str
    time_taken_seconds: int | None = None


class SubmitResponse(BaseModel):
    accuracy: float
    total_words: int
    correct: int
    wrong: int
    missed: int
    extra: int
    word_diff: list[WordDiffItem]
