from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..db import supabase
from ..diff import diff_words
from ..models import DictationCard, DictationDetail, SubmitRequest, SubmitResponse

router = APIRouter(prefix="/api/dictations", tags=["dictations"])

AUDIO_BUCKET = "dictation-audio"
SIGNED_URL_TTL_SECONDS = 3600


def _attempt_stats(user_id: str) -> dict[str, dict]:
    """Per-user attempt stats — each user only sees their own history."""
    rows = (
        supabase.table("attempts")
        .select("dictation_id, accuracy, created_at")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    stats: dict[str, dict] = {}
    for row in rows:
        did = row["dictation_id"]
        entry = stats.setdefault(
            did, {"count": 0, "best_accuracy": None, "last_attempt_at": None}
        )
        entry["count"] += 1
        if entry["best_accuracy"] is None or row["accuracy"] > entry["best_accuracy"]:
            entry["best_accuracy"] = row["accuracy"]
        if (
            entry["last_attempt_at"] is None
            or row["created_at"] > entry["last_attempt_at"]
        ):
            entry["last_attempt_at"] = row["created_at"]
    return stats


def _fetch_dictation_row(dictation_id: str) -> dict:
    rows = (
        supabase.table("dictations")
        .select("id, title, time_limit_seconds, created_at, audio_path, transcript")
        .eq("id", dictation_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Dictation not found")
    return rows[0]


@router.get("", response_model=list[DictationCard])
def list_dictations(user: dict = Depends(get_current_user)):
    rows = (
        supabase.table("dictations")
        .select("id, title, time_limit_seconds, created_at, transcript")
        .order("created_at", desc=True)
        .execute()
        .data
    )
    stats = _attempt_stats(user["id"])
    return [
        DictationCard(
            id=row["id"],
            title=row["title"],
            time_limit_seconds=row["time_limit_seconds"],
            created_at=row["created_at"],
            word_count=len(row["transcript"].split()),
            attempt_count=stats.get(row["id"], {}).get("count", 0),
            best_accuracy=stats.get(row["id"], {}).get("best_accuracy"),
            last_attempt_at=stats.get(row["id"], {}).get("last_attempt_at"),
        )
        for row in rows
    ]


@router.get("/{dictation_id}", response_model=DictationDetail)
def get_dictation(dictation_id: str, user: dict = Depends(get_current_user)):
    row = _fetch_dictation_row(dictation_id)

    signed = supabase.storage.from_(AUDIO_BUCKET).create_signed_url(
        row["audio_path"], SIGNED_URL_TTL_SECONDS
    )
    audio_url = signed.get("signedURL") or signed.get("signedUrl")
    if not audio_url:
        raise HTTPException(status_code=500, detail="Failed to sign audio URL")

    stats = _attempt_stats(user["id"]).get(row["id"], {})
    return DictationDetail(
        id=row["id"],
        title=row["title"],
        time_limit_seconds=row["time_limit_seconds"],
        created_at=row["created_at"],
        word_count=len(row["transcript"].split()),
        attempt_count=stats.get("count", 0),
        best_accuracy=stats.get("best_accuracy"),
        last_attempt_at=stats.get("last_attempt_at"),
        audio_url=audio_url,
    )


@router.post("/{dictation_id}/submit", response_model=SubmitResponse)
def submit_attempt(
    dictation_id: str, body: SubmitRequest, user: dict = Depends(get_current_user)
):
    rows = (
        supabase.table("dictations")
        .select("transcript")
        .eq("id", dictation_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Dictation not found")
    transcript = rows[0]["transcript"]

    result = diff_words(transcript, body.typed_text)

    supabase.table("attempts").insert(
        {
            "dictation_id": dictation_id,
            "user_id": user["id"],
            "typed_text": body.typed_text,
            "accuracy": result["accuracy"],
            "total_words": result["total_words"],
            "correct": result["correct"],
            "wrong": result["wrong"],
            "missed": result["missed"],
            "extra": result["extra"],
            "time_taken_seconds": body.time_taken_seconds,
            "word_diff": result["word_diff"],
        }
    ).execute()

    return SubmitResponse(**result)
