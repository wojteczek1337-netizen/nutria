# nutriapp/services/avatar_service.py
"""Awatary z publicznego bucketa Supabase Storage o nazwie kizo.

Nazwa pliku to poziom, nie id użytkownika. 1.png jest najlepszy,
a wyższy numer jest gorszy. Najlepszy poziom wymaga punktów z pół roku
przy maksymalnym wyniku dnia.
"""

from pathlib import PurePosixPath
from urllib.parse import quote

from sqlalchemy import text
from sqlalchemy.orm import Session

from nutriapp.data.database import database_url
from nutriapp.services.points_service import CALORIE_BANDS, FAT_BANDS, PROTEIN_BANDS

BUCKET_NAME = "kizo"
HALF_YEAR_DAYS = 183
MAX_DAILY_POINTS = CALORIE_BANDS[0][1] + PROTEIN_BANDS[0][1] + FAT_BANDS[0][1]
BEST_AVATAR_POINTS = HALF_YEAR_DAYS * MAX_DAILY_POINTS

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_SUFFIX_RANK = {
    ".png": 4,
    ".jpg": 3,
    ".jpeg": 3,
    ".webp": 2,
    ".gif": 1,
}


def load_avatar_catalog(session: Session) -> dict[int, str]:
    """Zwraca numer poziomu i nazwę pliku w buckecie."""
    rows = session.execute(
        text("SELECT name FROM storage.objects WHERE bucket_id = :bucket"),
        {"bucket": BUCKET_NAME},
    ).all()

    chosen: dict[int, str] = {}
    ranks: dict[int, int] = {}
    for (name,) in rows:
        path = PurePosixPath(name)
        suffix = path.suffix.lower()
        if suffix not in _IMAGE_SUFFIXES or not path.stem.isdigit():
            continue
        level = int(path.stem)
        rank = _SUFFIX_RANK[suffix]
        if level not in chosen or rank > ranks[level]:
            chosen[level] = name
            ranks[level] = rank
    return chosen


def avatar_url_for_points(points: int, catalog: dict[int, str]) -> str | None:
    level = select_avatar_level(points, list(catalog))
    if level is None:
        return None
    return public_object_url(catalog[level])


def select_avatar_level(points: int, levels: list[int]) -> int | None:
    """Najmniejszy numer to najlepszy awatar i wymaga BEST_AVATAR_POINTS.

    Poniżej tego progu punkty dzielą się równo na gorsze pliki.
    Sam najlepszy plik nie jest pokazywany wcześniej.
    """
    if not levels:
        return None

    ordered = sorted(set(levels))
    best = ordered[0]
    if points >= BEST_AVATAR_POINTS:
        return best
    if len(ordered) == 1:
        return None

    worse_from_worst = list(reversed(ordered[1:]))
    buckets = len(worse_from_worst)
    index = min(int(points / BEST_AVATAR_POINTS * buckets), buckets - 1)
    return worse_from_worst[index]


def public_object_url(object_name: str) -> str:
    encoded = quote(object_name, safe="/")
    return (
        f"{_project_base_url()}/storage/v1/object/public/"
        f"{BUCKET_NAME}/{encoded}"
    )


def _project_base_url() -> str:
    username = database_url.username or ""
    project_ref = username.split(".", 1)[1] if "." in username else ""
    if not project_ref:
        raise RuntimeError(
            "Nie udało się odczytać identyfikatora projektu Supabase z DATABASE_URL."
        )
    return f"https://{project_ref}.supabase.co"
