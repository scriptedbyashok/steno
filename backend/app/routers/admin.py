import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..auth import require_admin
from ..db import supabase

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


@router.delete("/{dictation_id}", status_code=204)
def delete_dictation(dictation_id: str, _admin=Depends(require_admin)):
    rows = (
        supabase.table("dictations")
        .select("audio_path")
        .eq("id", dictation_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Dictation not found")

    supabase.storage.from_(AUDIO_BUCKET).remove([rows[0]["audio_path"]])
    supabase.table("dictations").delete().eq("id", dictation_id).execute()
