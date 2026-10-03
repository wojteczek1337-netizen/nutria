# nutriapp/data/repositories/user_repo.py
import hashlib
from sqlalchemy.orm import Session
from passlib.hash import argon2

from nutriapp.data.database import SessionLocal
from nutriapp.models.user import User
from nutriapp.models.user_profile import UserProfile


def get_session() -> Session:
    return SessionLocal()


# ---------- UŻYTKOWNIK (konto) ----------

def _hash_password(raw: str) -> str:
    """Bezpieczny hash hasła przy użyciu Argon2id (passlib)."""
    return argon2.hash(raw)

def _verify_password(raw: str, hashed: str) -> bool:
    """Sprawdza hasło raw względem zapisanego hasha."""
    return argon2.verify(raw, hashed)

def get_user_by_email(session: Session, email: str) -> User | None:
    return session.query(User).filter(User.email == email).first()


def create_user(session: Session, email: str, raw_password: str, display_name: str | None) -> User:
    """Tworzy użytkownika, jeśli jeszcze nie istnieje. Zwraca obiekt User."""
    user = get_user_by_email(session, email=email)
    if user is not None:
        return user  # już istnieje

    user = User(
        email=email,
        password_hash=_hash_password(raw_password),
        display_name=display_name,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def verify_user_credentials(session: Session, email: str, raw_password: str) -> User | None:
    user = get_user_by_email(session, email=email)
    if user is None:
        return None

    if not _verify_password(raw_password, user.password_hash):
        return None

    return user


# ---------- PROFIL ZDROWOTNY ----------

def get_user_profile(session: Session, user_id: int) -> UserProfile | None:
    return (
        session.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )


def save_user_profile(
    session: Session,
    *,
    user_id: int,
    name: str | None,
    sex: str,
    age_years: int,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str,
    calorie_mode: str,
    calorie_algorithm: str,
    manual_calories: float | None,
    calorie_adjustment: float,
    macro_mode: str,
    protein_g_per_kg: float | None,
    fat_g_per_kg: float | None,
    carbs_g_per_kg: float | None,
    manual_protein_g: float | None,
    manual_fat_g: float | None,
    manual_carbs_g: float | None,
) -> UserProfile:
    profile = get_user_profile(session, user_id=user_id)

    if profile is None:
        profile = UserProfile(user_id=user_id)

    profile.name = name
    profile.sex = sex
    profile.age_years = age_years
    profile.height_cm = height_cm
    profile.weight_kg = weight_kg
    profile.activity_level = activity_level
    profile.goal = goal

    profile.calorie_mode = calorie_mode
    profile.calorie_algorithm = calorie_algorithm
    profile.manual_calories = manual_calories
    profile.calorie_adjustment = calorie_adjustment
    profile.macro_mode = macro_mode
    profile.protein_g_per_kg = protein_g_per_kg
    profile.fat_g_per_kg = fat_g_per_kg
    profile.carbs_g_per_kg = carbs_g_per_kg
    profile.manual_protein_g = manual_protein_g
    profile.manual_fat_g = manual_fat_g
    profile.manual_carbs_g = manual_carbs_g

    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile