import traceback
from typing import Any, Dict
from uuid import UUID as UUIDType

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db, Profile, User
from deps import get_current_user

router = APIRouter(tags=["profile"])


def _get_user_uuid(user_id):
    if isinstance(user_id, str):
        try:
            return UUIDType(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id}")
    return user_id


@router.post("/api/profile")
async def create_or_update_profile(
    profile_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_id_str = current_user["user_id"]
        print(f"DEBUG: Original user_id: {user_id_str}, type: {type(user_id_str)}")

        user_id_uuid = _get_user_uuid(user_id_str)
        print(f"DEBUG: Converted user_id UUID: {user_id_uuid}, type: {type(user_id_uuid)}")
        print(f"DEBUG: Profile data: {profile_data}")

        existing_profile_str = None
        try:
            existing_profile_str = (
                db.query(Profile).filter(Profile.id == user_id_str).first()
            )
            if existing_profile_str:
                print(f"DEBUG: Found profile with string ID: {existing_profile_str.id}")
        except Exception as e:
            print(f"DEBUG: Error checking string ID (expected if UUID type): {e}")

        raw_grad_year = profile_data.get("grad_year")
        if isinstance(raw_grad_year, str):
            raw_grad_year = raw_grad_year.strip() or None

        existing_profile = (
            db.query(Profile).filter(Profile.id == user_id_uuid).first()
        )
        print(f"DEBUG: Existing profile found (UUID): {existing_profile is not None}")

        if existing_profile_str and not existing_profile:
            print(f"DEBUG: Using profile found with string ID")
            existing_profile = existing_profile_str

        if existing_profile:
            existing_profile.full_name = profile_data.get("full_name")
            existing_profile.institution = profile_data.get("institution")
            existing_profile.grad_year = raw_grad_year
            existing_profile.specialty = profile_data.get("specialty")

            if hasattr(existing_profile, "updated_at"):
                existing_profile.updated_at = func.now()

            print(f"DEBUG: Updating existing profile, committing...")
            db.commit()
            db.refresh(existing_profile)
            print(f"DEBUG: Profile updated: {existing_profile.id}, {existing_profile.full_name}")

            return {
                "success": True,
                "message": "Profile updated successfully",
                "profile": {
                    "id": existing_profile.id,
                    "full_name": existing_profile.full_name,
                    "institution": existing_profile.institution,
                    "grad_year": existing_profile.grad_year,
                    "specialty": existing_profile.specialty,
                    "updated_at": (
                        existing_profile.updated_at.isoformat()
                        if getattr(existing_profile, "updated_at", None)
                        else None
                    ),
                },
            }
        else:
            print(f"DEBUG: No existing profile found, creating new one...")

            try:
                all_profiles = db.query(Profile).limit(10).all()
                print(f"DEBUG: Sample of existing profiles in DB ({len(all_profiles)} shown):")
                for p in all_profiles:
                    print(f"  - Profile ID: {p.id} (type: {type(p.id).__name__}), name: {p.full_name}")
            except Exception as e:
                print(f"DEBUG: Could not list profiles: {e}")

            try:
                profile = Profile(
                    id=user_id_uuid,
                    full_name=profile_data.get("full_name"),
                    institution=profile_data.get("institution"),
                    grad_year=raw_grad_year,
                    specialty=profile_data.get("specialty"),
                )
                db.add(profile)
                print(f"DEBUG: Profile added to session, attempting commit...")
                db.commit()
                db.refresh(profile)
                print(f"DEBUG: Profile refreshed: {profile.id}, {profile.full_name}")
            except Exception as create_error:
                db.rollback()
                error_msg = str(create_error)
                print(f"DEBUG: Error type: {type(create_error).__name__}")
                print(f"DEBUG: Error message: {error_msg}")
                if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
                    print(f"DEBUG: Possible duplicate key error - profile may already exist")
                    try:
                        found = db.query(Profile).filter(Profile.id == user_id_str).first()
                        if found:
                            print(f"DEBUG: Found existing profile with string ID: {found.id}")
                        found_uuid = db.query(Profile).filter(Profile.id == user_id_uuid).first()
                        if found_uuid:
                            print(f"DEBUG: Found existing profile with UUID: {found_uuid.id}")
                    except Exception:
                        pass
                raise

            return {
                "success": True,
                "message": "Profile created successfully",
                "profile": {
                    "id": profile.id,
                    "full_name": profile.full_name,
                    "institution": profile.institution,
                    "grad_year": profile.grad_year,
                    "specialty": profile.specialty,
                    "created_at": (
                        profile.created_at.isoformat()
                        if getattr(profile, "created_at", None)
                        else None
                    ),
                },
            }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_trace = traceback.format_exc()
        print("=" * 50)
        print("ERROR SAVING PROFILE:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(error_trace)
        print("=" * 50)
        raise HTTPException(status_code=500, detail=f"Error saving profile: {str(e)}")


@router.get("/api/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_id_uuid = _get_user_uuid(current_user["user_id"])
        profile = db.query(Profile).filter(Profile.id == user_id_uuid).first()

        if not profile:
            return {"success": True, "profile": None, "message": "No profile found"}

        return {
            "success": True,
            "profile": {
                "id": profile.id,
                "full_name": profile.full_name,
                "institution": profile.institution,
                "grad_year": profile.grad_year,
                "specialty": profile.specialty,
                "created_at": (
                    profile.created_at.isoformat()
                    if getattr(profile, "created_at", None)
                    else None
                ),
                "updated_at": (
                    profile.updated_at.isoformat()
                    if getattr(profile, "updated_at", None)
                    else None
                ),
            },
        }

    except Exception as e:
        print("Error fetching profile:", e)
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")


@router.get("/api/profile/me")
async def get_my_profile_with_user_data(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_id = int(current_user["user_id"])
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "profile": {
                "user_id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "institution": user.institution,
                "grad_year": user.graduation_year,
                "specialty": user.specialty,
                "profile_exists": user.profile_completed,
            },
        }

    except Exception as e:
        print("Error fetching user data:", e)
        raise HTTPException(status_code=500, detail=f"Error fetching user data: {str(e)}")
