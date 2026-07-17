from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user, require_admin
from ..db import supabase
from ..models import DictationRanking, RankingEntry

router = APIRouter(prefix="/api", tags=["rankings"])


def _sort_key(row: dict) -> tuple:
    time_taken = row["time_taken_seconds"]
    time_key = time_taken if time_taken is not None else float("inf")
    return (-row["accuracy"], time_key, row["created_at"])


def _best_attempt_per_user(rows: list[dict]) -> dict[str, dict]:
    best: dict[str, dict] = {}
    for row in rows:
        user_id = row["user_id"]
        current = best.get(user_id)
        if current is None or _sort_key(row) < _sort_key(current):
            best[user_id] = row
    return best


@router.get("/dictations/{dictation_id}/ranking", response_model=list[RankingEntry])
def get_dictation_ranking(
    dictation_id: str, user: dict = Depends(get_current_user)
):
    dictation_rows = (
        supabase.table("dictations")
        .select("id")
        .eq("id", dictation_id)
        .execute()
        .data
    )
    if not dictation_rows:
        raise HTTPException(status_code=404, detail="Dictation not found")

    attempt_rows = (
        supabase.table("attempts")
        .select("user_id, accuracy, time_taken_seconds, created_at")
        .eq("dictation_id", dictation_id)
        .execute()
        .data
    )
    user_rows = supabase.table("users").select("id, display_name").execute().data
    display_names = {row["id"]: row["display_name"] for row in user_rows}

    best_attempts = _best_attempt_per_user(attempt_rows)
    ranked = sorted(best_attempts.values(), key=_sort_key)

    return [
        RankingEntry(
            rank=index + 1,
            user_id=row["user_id"],
            display_name=display_names.get(row["user_id"], "Unknown"),
            accuracy=row["accuracy"],
            time_taken_seconds=row["time_taken_seconds"],
            achieved_at=row["created_at"],
        )
        for index, row in enumerate(ranked)
    ]


@router.get("/admin/rankings", response_model=list[DictationRanking])
def get_admin_rankings(user: dict = Depends(require_admin)):
    dictation_rows = (
        supabase.table("dictations")
        .select("id, title, created_at")
        .order("created_at", desc=True)
        .execute()
        .data
    )
    attempt_rows = (
        supabase.table("attempts")
        .select("dictation_id, user_id, accuracy")
        .execute()
        .data
    )
    user_rows = supabase.table("users").select("id, display_name").execute().data
    display_names = {row["id"]: row["display_name"] for row in user_rows}

    attempts_by_dictation: dict[str, list[dict]] = {}
    for row in attempt_rows:
        attempts_by_dictation.setdefault(row["dictation_id"], []).append(row)

    results = []
    for dictation in dictation_rows:
        rows = attempts_by_dictation.get(dictation["id"], [])
        best_by_user: dict[str, dict] = {}
        for row in rows:
            user_id = row["user_id"]
            current = best_by_user.get(user_id)
            if current is None or row["accuracy"] > current["accuracy"]:
                best_by_user[user_id] = row

        top_display_name = None
        top_accuracy = None
        if best_by_user:
            topper = max(best_by_user.values(), key=lambda row: row["accuracy"])
            top_display_name = display_names.get(topper["user_id"], "Unknown")
            top_accuracy = topper["accuracy"]

        results.append(
            DictationRanking(
                dictation_id=dictation["id"],
                title=dictation["title"],
                top_display_name=top_display_name,
                top_accuracy=top_accuracy,
                participant_count=len(best_by_user),
                attempt_count=len(rows),
            )
        )

    return results
