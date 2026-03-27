"""SQLAlchemy models and database helpers.

Only actively-used models are defined here. For a record of removed models
see docs/REMOVED_MODELS.md.
"""

from sqlalchemy import (
    create_engine, Column, String, DateTime, JSON, Integer, Boolean,
    DECIMAL, Text, text, Numeric, ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://username:password@your-aws-rds-endpoint:5432/your-database-name",
)

# Lazy engine creation to avoid import-time database connection
def get_engine():
    return create_engine(DATABASE_URL)


def get_session_local():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_async_engine():
    return create_async_engine(DATABASE_URL)


def get_async_session_local():
    return async_sessionmaker(
        get_async_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


Base = declarative_base()


# ---------------------------------------------------------------------------
# Dependency for database sessions
# ---------------------------------------------------------------------------

def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as db:
        yield db


# ---------------------------------------------------------------------------
# Core User Management
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=True, unique=True)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    is_superuser = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    is_verified = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    specialty = Column(String)
    graduation_year = Column(Integer)
    institution = Column(String)
    profile_completed = Column(Boolean, default=False)
    avatar = Column(String)
    requires_password_change = Column(Boolean, default=False)
    external_auth_id = Column(String, unique=True)
    created_at = Column(DateTime, server_default=func.now())


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String)
    created_at = Column(DateTime, server_default=func.now())


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID, primary_key=True)
    full_name = Column(String, nullable=True)
    institution = Column(String, nullable=True)
    grad_year = Column(String, nullable=True)
    specialty = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------------------
# Chat / User Data
# ---------------------------------------------------------------------------

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    session_id = Column(String)
    message_type = Column(String)
    message_content = Column(JSON)
    timestamp = Column(DateTime, server_default=func.now())
    thread_id = Column(String)
    user_id = Column(UUID)
    response_time_ms = Column(Integer)
    message_length = Column(Integer)


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    session_id = Column(String)
    interaction_type = Column(String)
    interaction_data = Column(JSON)
    timestamp = Column(DateTime, server_default=func.now())
    user_id = Column(UUID)
    page_url = Column(Text)
    device_info = Column(JSON)


class UserSession(Base):
    __tablename__ = "user_session"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    session_id = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    last_activity = Column(DateTime)
    is_active = Column(Boolean, default=True)
    user_id = Column(UUID)
    ip_address = Column(INET)
    user_agent = Column(Text)
    session_duration = Column(Integer)


# ---------------------------------------------------------------------------
# Materials & RAG
# ---------------------------------------------------------------------------

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    course_id = Column(Integer)
    title = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_path = Column(String)
    file_size = Column(Integer)

    # RAG Processing
    status = Column(String, nullable=False, default="uploaded")
    processing_progress = Column(Integer, default=0)
    processing_error = Column(Text)

    # RAG Content
    extracted_text = Column(Text)
    chunk_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    embedding_model = Column(String, default="text-embedding-3-small")

    # Timestamps
    uploaded_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)
    last_accessed = Column(DateTime)


# ---------------------------------------------------------------------------
# Learning Plans
# ---------------------------------------------------------------------------

class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    video_url = Column(String(500))
    video_title = Column(String(255))
    video_duration = Column(Integer)
    case_study = Column(Text, nullable=False)
    case_study_editable = Column(Boolean, default=False)
    quiz_questions = Column(JSON, nullable=False)
    topic = Column(String(255))
    difficulty_level = Column(String(50))
    estimated_duration = Column(Integer)
    is_published = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String)


class LearningPlanProgress(Base):
    __tablename__ = "learning_plan_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    learning_plan_id = Column(Integer, nullable=False)
    video_watched = Column(Boolean, default=False)
    video_watched_at = Column(DateTime)
    video_progress = Column(Integer, default=0)
    case_study_read = Column(Boolean, default=False)
    case_study_read_at = Column(DateTime)
    case_study_notes = Column(Text)
    quiz_submitted = Column(Boolean, default=False)
    quiz_submitted_at = Column(DateTime)
    quiz_answers = Column(JSON)
    quiz_score = Column(Integer)
    quiz_total = Column(Integer)
    quiz_percentage = Column(Numeric)
    attempt_count = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    started_at = Column(DateTime, server_default=func.now())
    last_accessed = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------------------
# Care Plans
# ---------------------------------------------------------------------------

class CarePlan(Base):
    __tablename__ = "care_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)

    # Basic Information
    title = Column(String(255), nullable=False)
    patient_name = Column(String(255))
    procedure = Column(String(500))
    diagnosis = Column(String(500))

    # Patient Demographics
    age = Column(String(50))
    sex = Column(String(20))
    height = Column(String(50))
    weight = Column(String(50))

    # Vital Signs
    temperature_f = Column(String(20))
    blood_pressure = Column(String(50))
    heart_rate = Column(String(20))
    respiration_rate = Column(String(20))
    oxygen_saturation = Column(String(20))
    lmp_date = Column(String(50))

    # Medical History
    past_medical_history = Column(Text)
    past_surgical_history = Column(Text)
    anesthesia_history = Column(Text)
    current_medications = Column(Text)
    alcohol_use = Column(Text)
    substance_use = Column(Text)
    allergies = Column(Text)

    # Physical Assessment
    neurological_findings = Column(Text)
    heent_findings = Column(Text)
    respiratory_findings = Column(Text)
    cardiovascular_findings = Column(Text)
    gastrointestinal_findings = Column(Text)
    genitourinary_findings = Column(Text)
    endocrine_findings = Column(Text)
    other_findings = Column(Text)

    # Airway Assessment
    mallampati_class = Column(String(50))
    ulbt_grade = Column(String(50))
    thyromental_distance = Column(String(20))
    interincisor_distance = Column(String(20))
    dentition = Column(Text)
    neck_assessment = Column(Text)
    oral_mucosa = Column(Text)

    # Laboratory Values
    sodium = Column(String(20))
    potassium = Column(String(20))
    chloride = Column(String(20))
    co2 = Column(String(20))
    bun = Column(String(20))
    creatinine = Column(String(20))
    glucose = Column(String(20))
    wbc = Column(String(20))
    hemoglobin = Column(String(20))
    hematocrit = Column(String(20))
    platelets = Column(String(20))
    pt = Column(String(20))
    ptt = Column(String(20))
    inr = Column(String(20))
    abg = Column(String(50))
    other_labs = Column(Text)

    # Imaging/Diagnostic Tests
    ekg = Column(Text)
    chest_xray = Column(Text)
    echocardiogram = Column(Text)
    other_imaging = Column(Text)

    # Cultural/Religious Considerations
    cultural_religious_attributes = Column(Text)

    # AI-Generated Content
    ai_recommendations = Column(Text)
    risk_assessment = Column(Text)
    monitoring_plan = Column(Text)
    medication_plan = Column(Text)

    # RAG Integration
    rag_context = Column(Text)
    rag_sources = Column(JSON)
    rag_confidence_score = Column(DECIMAL)

    # Status and Metadata
    status = Column(String(50), default="draft")
    version = Column(Integer, default=1)
    is_template = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_accessed = Column(DateTime)

    # File Export
    exported_text = Column(Text)
    export_hash = Column(String(64))


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def test_connection():
    try:
        engine = get_engine()
        with engine.connect() as connection:
            from sqlalchemy import text as sa_text
            result = connection.execute(sa_text("SELECT 1"))
            print("Database connection successful!")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def init_db():
    """Create extension and all tables."""
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


def create_all_tables():
    """Create all tables in the database."""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False


# ---------------------------------------------------------------------------
# Import RAG models so they are registered on Base.metadata
# ---------------------------------------------------------------------------
from models.rag import RagDocument, RagNode, RagChunk, IngestionRun  # noqa: F401, E402


if __name__ == "__main__":
    if test_connection():
        print("\nInitializing database...")
        init_db()
