from fastapi import APIRouter

from ..db import supabase
from ..models import AttemptSummary

router = APIRouter(prefix="/api/dictations", tags=["attempts"])


@router.get("/{dictation_id}/attempts", response_model=list[AttemptSummary])
def list_attempts(dictation_id: str):
    rows = (
        supabase.table("attempts")
        .select(
            "id, accuracy, total_words, correct, wrong, missed, extra,"
            " time_taken_seconds, word_diff, created_at"
        )
        .eq("dictation_id", dictation_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    return rows
