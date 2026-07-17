import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..auth import require_admin
from ..db import supabase
from ..models import AdminDictationCard, AdminDictationDetail

router = APIRouter(prefix="/api/admin/dictations", tags=["admin"])

AUDIO_BUCKET = "dictation-audio"
MAX_AUDIO_BYTES = 25 * 1024 * 1024
CONTENT_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "m4a": "audio/mp4",
}


@router.post("", status_code=201)
async def create_dictation(
    audio: UploadFile = File(...),
    title: str = Form(...),
    transcript: str = Form(...),
    time_limit_seconds: int | None = Form(default=None),
    _admin=Depends(require_admin),
):
    ext = (audio.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Allowed: mp3, wav, m4a.",
        )

    content = await audio.read()
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=400, detail="Audio file exceeds 25 MB limit")

    audio_path = f"{uuid.uuid4()}.{ext}"
    supabase.storage.from_(AUDIO_BUCKET).upload(
        audio_path, content, {"content-type": CONTENT_TYPES[ext]}
    )

    row = (
        supabase.table("dictations")
        .insert(
            {
                "title": title,
                "audio_path": audio_path,
                "transcript": transcript,
                "time_limit_seconds": time_limit_seconds,
            }
        )
        .execute()
        .data[0]
    )
    return {
        "id": row["id"],
        "title": row["title"],
        "time_limit_seconds": row["time_limit_seconds"],
        "created_at": row["created_at"],
    }


@router.get("", response_model=list[AdminDictationCard])
def list_all_dictations(_admin=Depends(require_admin)):
    rows = (
        supabase.table("dictations")
        .select("id, title, time_limit_seconds, created_at, deleted_at, transcript")
        .order("created_at", desc=True)
        .execute()
        .data
    )
    attempt_rows = (
        supabase.table("attempts").select("dictation_id").execute().data
    )
    attempt_counts: dict[str, int] = {}
    for row in attempt_rows:
        did = row["dictation_id"]
        attempt_counts[did] = attempt_counts.get(did, 0) + 1

    return [
        AdminDictationCard(
            id=row["id"],
            title=row["title"],
            time_limit_seconds=row["time_limit_seconds"],
            created_at=row["created_at"],
            deleted_at=row["deleted_at"],
            word_count=len(row["transcript"].split()),
            attempt_count=attempt_counts.get(row["id"], 0),
        )
        for row in rows
    ]


@router.get("/{dictation_id}", response_model=AdminDictationDetail)
def get_admin_dictation(dictation_id: str, _admin=Depends(require_admin)):
    rows = (
        supabase.table("dictations")
        .select("id, title, transcript, time_limit_seconds, created_at, deleted_at")
        .eq("id", dictation_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Dictation not found")
    return AdminDictationDetail(**rows[0])


@router.patch("/{dictation_id}", response_model=AdminDictationDetail)
async def update_dictation(
    dictation_id: str,
    title: str | None = Form(default=None),
    transcript: str | None = Form(default=None),
    time_limit_seconds: int | None = Form(default=None),
    clear_time_limit: bool = Form(default=False),
    audio: UploadFile | None = File(default=None),
    _admin=Depends(require_admin),
):
    existing_rows = (
        supabase.table("dictations")
        .select("id, audio_path")
        .eq("id", dictation_id)
        .execute()
        .data
    )
    if not existing_rows:
        raise HTTPException(status_code=404, detail="Dictation not found")

    updates: dict = {}
    if title is not None:
        updates["title"] = title
    if transcript is not None:
        updates["transcript"] = transcript
    if clear_time_limit:
        updates["time_limit_seconds"] = None
    elif time_limit_seconds is not None:
        updates["time_limit_seconds"] = time_limit_seconds

    if audio is not None:
        ext = (audio.filename or "").rsplit(".", 1)[-1].lower()
        if ext not in CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Unsupported audio format. Allowed: mp3, wav, m4a.",
            )

        content = await audio.read()
        if len(content) > MAX_AUDIO_BYTES:
            raise HTTPException(
                status_code=400, detail="Audio file exceeds 25 MB limit"
            )

        new_audio_path = f"{uuid.uuid4()}.{ext}"
        supabase.storage.from_(AUDIO_BUCKET).upload(
            new_audio_path, content, {"content-type": CONTENT_TYPES[ext]}
        )
        supabase.storage.from_(AUDIO_BUCKET).remove(
            [existing_rows[0]["audio_path"]]
        )
        updates["audio_path"] = new_audio_path

    if updates:
        supabase.table("dictations").update(updates).eq("id", dictation_id).execute()

    row = (
        supabase.table("dictations")
        .select("id, title, transcript, time_limit_seconds, created_at, deleted_at")
        .eq("id", dictation_id)
        .execute()
        .data[0]
    )
    return AdminDictationDetail(**row)


@router.delete("/{dictation_id}", status_code=204)
def delete_dictation(
    dictation_id: str, permanent: bool = False, _admin=Depends(require_admin)
):
    rows = (
        supabase.table("dictations")
        .select("audio_path")
        .eq("id", dictation_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Dictation not found")

    if permanent:
        supabase.storage.from_(AUDIO_BUCKET).remove([rows[0]["audio_path"]])
        supabase.table("dictations").delete().eq("id", dictation_id).execute()
    else:
        supabase.table("dictations").update(
            {"deleted_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", dictation_id).execute()


@router.post("/{dictation_id}/restore", response_model=AdminDictationDetail)
def restore_dictation(dictation_id: str, _admin=Depends(require_admin)):
    existing = (
        supabase.table("dictations").select("id").eq("id", dictation_id).execute().data
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Dictation not found")

    supabase.table("dictations").update({"deleted_at": None}).eq(
        "id", dictation_id
    ).execute()

    row = (
        supabase.table("dictations")
        .select("id, title, transcript, time_limit_seconds, created_at, deleted_at")
        .eq("id", dictation_id)
        .execute()
        .data[0]
    )
    return AdminDictationDetail(**row)
