"""Direct Supabase Storage Textbook Sync and Streaming Module.

Fetches and streams NCERT / KCET textbook PDFs directly in-memory from
Supabase Storage ('vyasaprep-textbook' bucket) without creating local disk files.
"""

from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional, Tuple

from .store import _get_supabase_client

logger = logging.getLogger("smartkcet.rag.textbook_sync")

BUCKET_NAMES = ["vyasaprep-textbook", "vyasaprep-textbooks"]
SUBJECT_FOLDER_MAP = {
    "biology": "Biology",
    "chemistry": "Chemistry",
    "math": "Mathematics",
    "mathematics": "Mathematics",
    "physics": "Physics",
}


def stream_textbook_from_supabase(filename: str) -> Optional[Tuple[io.BytesIO, str, int]]:
    """Fetch PDF bytes in-memory directly from Supabase Storage without writing to disk.

    Returns:
        (BytesIO_stream, clean_filename, file_size_bytes) or None if not found.
    """
    client = _get_supabase_client()
    if client is None:
        logger.warning("Supabase client is not available for textbook streaming.")
        return None

    clean_name = filename.strip().lstrip("/")
    basename = clean_name.split("/")[-1]

    search_paths = [
        clean_name,
        basename,
        f"biology/{basename}",
        f"chemistry/{basename}",
        f"math/{basename}",
        f"physics/{basename}",
    ]

    for bucket_name in BUCKET_NAMES:
        for remote_path in search_paths:
            try:
                data = client.storage.from_(bucket_name).download(remote_path)
                if data and len(data) > 0:
                    logger.info(
                        "Streamed textbook %s (%d bytes) from Supabase bucket '%s', path '%s'",
                        basename, len(data), bucket_name, remote_path,
                    )
                    stream = io.BytesIO(data)
                    stream.seek(0)
                    return stream, basename, len(data)
            except Exception:
                continue

    logger.warning("Textbook %s not found in Supabase storage buckets.", filename)
    return None


def list_all_supabase_textbooks() -> Dict[str, List[Dict[str, Any]]]:
    """Scan Supabase Storage bucket 'vyasaprep-textbook' and return all 128 textbooks by subject.

    Returns:
        Dictionary mapping subject name -> list of textbook file info dicts.
    """
    client = _get_supabase_client()
    result: Dict[str, List[Dict[str, Any]]] = {
        "Biology": [],
        "Chemistry": [],
        "Mathematics": [],
        "Physics": [],
    }

    if client is None:
        return result

    bucket_name = "vyasaprep-textbook"
    subfolders = ["biology", "chemistry", "math", "physics"]

    for folder in subfolders:
        subject_title = SUBJECT_FOLDER_MAP.get(folder, folder.title())
        try:
            files = client.storage.from_(bucket_name).list(folder)
            for f in files:
                if not isinstance(f, dict):
                    continue
                name = f.get("name")
                if not name or name.startswith("."):
                    continue

                meta = f.get("metadata") or {}
                size = meta.get("size") or 0

                result.setdefault(subject_title, []).append({
                    "filename": name,
                    "subject": subject_title,
                    "size_bytes": size,
                    "remote_path": f"{folder}/{name}",
                    "download_url": f"/api/syllabus/textbook/{folder}/{name}",
                })
        except Exception as exc:
            logger.warning("Failed to list Supabase textbook folder '%s': %s", folder, exc)

    return result
