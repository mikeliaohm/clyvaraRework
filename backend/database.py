#populated database schemas

from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer, Boolean, DECIMAL, Text, text, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, synonym
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://username:password@your-aws-rds-endpoint:5432/your-database-name")

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

# Dependency for database sessions
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

# User Data Schema Models
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {'schema': 'user_data'}
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    session_id = Column(String)
    message_type = Column(String)
    message_content = Column(JSON)
    timestamp = Column(DateTime, server_default=func.now())
    thread_id = Column(String)
    user_id = Column(UUID)  # Link to Supabase user
    response_time_ms = Column(Integer)
    message_length = Column(Integer)

class UserInteraction(Base):
    __tablename__ = "user_interactions"
    __table_args__ = {'schema': 'user_data'}
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    session_id = Column(String)
    interaction_type = Column(String)
    interaction_data = Column(JSON)
    timestamp = Column(DateTime, server_default=func.now())
    user_id = Column(UUID)  # Link to Supabase user
    page_url = Column(Text)
    device_info = Column(JSON)

class UserSession(Base):
    __tablename__ = "user_session"
    __table_args__ = {'schema': 'user_data'}
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    session_id = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    last_activity = Column(DateTime)
    is_active = Column(Boolean, default=True)
    user_id = Column(UUID)  # Link to Supabase user
    ip_address = Column(INET)
    user_agent = Column(Text)
    session_duration = Column(Integer)

# Dashboard Schema Models
class DashboardLayout(Base):
    __tablename__ = "dashboard_layouts"
    __table_args__ = {'schema': 'dashboard'}
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID, nullable=False)
    layout_name = Column(String(100), nullable=False)
    layout_config = Column(JSON, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

class Widget(Base):
    __tablename__ = "widgets"
    __table_args__ = {'schema': 'dashboard'}
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    widget_type = Column(String(50), nullable=False)
    widget_name = Column(String(100), nullable=False)
    widget_config = Column(JSON, nullable=False)
    is_system = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class UserWidget(Base):
    __tablename__ = "user_widgets"
    __table_args__ = {'schema': 'dashboard'}
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID, nullable=False)
    dashboard_layout_id = Column(UUID)
    widget_id = Column(UUID)
    widget_position = Column(JSON, nullable=False)
    widget_settings = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = {'schema': 'dashboard'}
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID, nullable=False, unique=True)
    theme = Column(String(20), default='light')
    timezone = Column(String(50), default='UTC')
    date_format = Column(String(20), default='MM/DD/YYYY')
    dashboard_settings = Column(JSON)
    notification_settings = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

class AnalyticsData(Base):
    __tablename__ = "analytics_data"
    __table_args__ = {'schema': 'dashboard'}
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(DECIMAL(15, 4), nullable=False)
    metric_unit = Column(String(20))
    metadata_json = Column(JSON)
    recorded_at = Column(DateTime, server_default=func.now())

# Test database connection
def test_connection():
    try:
        engine = get_engine()
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1"))
            print("Database connection successful!")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
    
def init_db():
    """Create schemas, extension, and all tables."""
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS main;"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS user_data;"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS dashboard;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
        
        Base.metadata.create_all(bind=engine)
        print("Schemas + tables created successfully!")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def create_all_tables():
    """Create all tables in the database"""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False




# Medical Education Platform - SQLAlchemy Models
# Converted from TypeScript Drizzle schemas

# Core User Management
class Session(Base):
    __tablename__ = "sessions"
    
    sid = Column(String, primary_key=True)
    sess = Column(JSON, nullable=False)
    expire = Column(DateTime, nullable=False)

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'main'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=True, unique=True)
    password = Column(String, nullable=False)
    hashed_password = synonym("password")
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    is_superuser = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    is_verified = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    specialty = Column(String)  # nursing, medical-school, nurse-anesthesia, nurse-practitioner
    graduation_year = Column(Integer)
    institution = Column(String)
    profile_completed = Column(Boolean, default=False)
    avatar = Column(String)
    requires_password_change = Column(Boolean, default=False)
    external_auth_id = Column(String, unique=True)  # Supabase/external auth subject
    created_at = Column(DateTime, server_default=func.now())


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {'schema': 'main'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String)
    created_at = Column(DateTime, server_default=func.now())


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        {'schema': 'main'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("main.users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("main.roles.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Waitlist(Base):
    __tablename__ = "waitlist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    specialty = Column(String, nullable=False)
    institution = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    notified = Column(Boolean, default=False)

# Learning Management
class Course(Base):
    __tablename__ = "courses"
    __table_args__ = {'schema': 'main'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    source = Column(String, nullable=False, default="custom")  # 'canvas' | 'custom'
    lms_id = Column(String)  # External LMS course ID
    name = Column(String, nullable=False)
    term = Column(String)  # 'Fall 2025', 'Spring 2026', etc.
    status = Column(String, nullable=False, default="active")  # 'active' | 'archived'
    syllabus_html = Column(Text)
    course_metadata = Column(JSON)  # Additional course metadata
    created_at = Column(DateTime, server_default=func.now())

class CourseItem(Base):
    __tablename__ = "course_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, nullable=False)
    type = Column(String, nullable=False)  # 'assignment' | 'quiz' | 'file' | 'page' | 'textbook'
    title = Column(String, nullable=False)
    url = Column(String)  # External URL for Canvas items
    due_at = Column(DateTime)
    file_path = Column(String)  # Local file path if downloaded
    file_type = Column(String)  # File extension or type
    raw = Column(JSON)  # Raw data from Canvas API
    created_at = Column(DateTime, server_default=func.now())

class PlanCourse(Base):
    __tablename__ = "plan_courses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)

class Material(Base):
    __tablename__ = "materials"
    __table_args__ = {'schema': 'main'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # Changed to String for Supabase UUID
    course_id = Column(Integer)
    title = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, pptx, docx, txt
    file_path = Column(String)  # S3 URL or local path
    file_size = Column(Integer)  # File size in bytes
    
    # RAG Processing Fields
    status = Column(String, nullable=False, default="uploaded")  # uploaded, processing, processed, failed
    processing_progress = Column(Integer, default=0)
    processing_error = Column(Text)  # Error message if processing failed
    
    # RAG Content Fields
    extracted_text = Column(Text)  # Full extracted text
    chunk_count = Column(Integer, default=0)  # Number of chunks created
    total_tokens = Column(Integer, default=0)  # Total tokens in document
    embedding_model = Column(String, default="text-embedding-3-small")  # Model used for embeddings
    
    # Timestamps
    uploaded_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)
    last_accessed = Column(DateTime)

class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = {'schema': 'main'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    material_id = Column(Integer)
    name = Column(String, nullable=False)
    description = Column(String)
    percentage_complete = Column(Integer, default=0)
    last_studied = Column(DateTime)
    decay_rate = Column(Integer, default=5)  # percentage per day without review

class LearningModule(Base):
    __tablename__ = "learning_modules"
    __table_args__ = {'schema': 'main'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    topic_id = Column(Integer)
    title = Column(String, nullable=False)
    description = Column(String)
    type = Column(String, nullable=False)  # case-study, interactive, quiz, visual-guide
    content = Column(JSON, nullable=False)
    duration = Column(Integer, nullable=False)  # in minutes
    source = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class LearningPlan(Base):
    __tablename__ = "learning_plans"
    __table_args__ = {'schema': 'main'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # Supabase UUID
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
    __table_args__ = {'schema': 'main'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # Supabase UUID
    learning_plan_id = Column(Integer, nullable=False)
    video_watched = Column(Boolean, default=False)
    video_watched_at = Column(DateTime)
    video_progress = Column(Integer, default=0)  # 0-100
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

class Test(Base):
    __tablename__ = "tests"
    __table_args__ = {'schema': 'main'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    topic_id = Column(Integer)
    title = Column(String, nullable=False)
    description = Column(String)
    type = Column(String, nullable=False)  # adaptive, mastery, recovery
    questions = Column(JSON, nullable=False)
    difficulty = Column(Integer, nullable=False, default=3)  # 1-5
    duration_minutes = Column(Integer, nullable=False)
    question_count = Column(Integer, nullable=False)
    last_attempt_score = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    test_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    completed_at = Column(DateTime, server_default=func.now())
    answers = Column(JSON, nullable=False)

class StudyActivity(Base):
    __tablename__ = "study_activity"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    module_id = Column(Integer)
    test_id = Column(Integer)
    topic_id = Column(Integer)
    duration = Column(Integer, nullable=False)  # in seconds
    date = Column(DateTime, server_default=func.now())

class WeeklyInsight(Base):
    __tablename__ = "weekly_insights"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    week_starting = Column(DateTime, nullable=False)
    week_ending = Column(DateTime, nullable=False)
    total_study_time = Column(Integer, nullable=False)  # in seconds
    daily_average = Column(Integer, nullable=False)  # in seconds
    overall_retention = Column(Integer, nullable=False)  # percentage
    strongest_topics = Column(JSON, nullable=False)
    weakest_topics = Column(JSON, nullable=False)
    recommendations = Column(JSON, nullable=False)
    daily_activity = Column(JSON, nullable=False)

# Board Exam Topics
class BoardExamTopic(Base):
    __tablename__ = "board_exam_topics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    specialty = Column(String, nullable=False)  # nursing, medical-school, nurse-anesthesia, nurse-practitioner, dentistry
    exam_type = Column(String, nullable=False)  # NCLEX-RN, NCLEX-PN, USMLE-Step1, USMLE-Step2, SEE, NCE, NBDE-1, NBDE-2
    category = Column(String, nullable=False)  # pharmacology, pathophysiology, patient-care, etc.
    topic_name = Column(String, nullable=False)
    description = Column(String)
    frequency = Column(Integer, default=1)  # how often this appears on exams (1-5)
    difficulty = Column(Integer, default=3)  # complexity level (1-5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

# Content Generation
class ContentGeneration(Base):
    __tablename__ = "content_generation"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    material_id = Column(Integer)
    board_topic_id = Column(Integer)
    generation_type = Column(String, nullable=False)  # auto-from-material, board-exam-topic, manual
    status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    generated_content = Column(JSON)
    error_message = Column(String)
    requested_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

# Comprehensive Care Plans with RAG Integration
class CarePlan(Base):
    __tablename__ = "care_plans"
    __table_args__ = {'schema': 'main'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # Supabase UUID
    
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
    ai_recommendations = Column(Text)  # AI-generated anesthesia plan
    risk_assessment = Column(Text)     # AI-generated risk analysis
    monitoring_plan = Column(Text)    # AI-generated monitoring recommendations
    medication_plan = Column(Text)    # AI-generated medication recommendations
    
    # RAG Integration Fields
    rag_context = Column(Text)        # Context used for AI generation
    rag_sources = Column(JSON)        # Sources referenced during generation
    rag_confidence_score = Column(DECIMAL)  # Confidence in AI recommendations
    
    # Status and Metadata
    status = Column(String(50), default="draft")  # draft, completed, archived
    version = Column(Integer, default=1)
    is_template = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_accessed = Column(DateTime)
    
    # File Export
    exported_text = Column(Text)      # Full text export for RAG indexing
    export_hash = Column(String(64))  # Hash for change detection

# Legacy Anesthesia Care Plans (keeping for backward compatibility)
class AnesthesiaCarePlan(Base):
    __tablename__ = "anesthesia_care_plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    patient_name = Column(String(255), nullable=False)
    procedure = Column(String(500), nullable=False)
    diagnosis = Column(String(500))
    plan_data = Column(JSON, nullable=False)
    patient_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

# Agentic AI System Tables
class BiometricData(Base):
    __tablename__ = "biometric_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    heart_rate_variability = Column(DECIMAL)
    sleep_score = Column(DECIMAL)
    resting_heart_rate = Column(Integer)
    activity_level = Column(DECIMAL)
    stress_level = Column(DECIMAL)
    readiness_score = Column(DECIMAL)
    source = Column(String(50), nullable=False)  # 'oura', 'apple_watch', 'fitbit', 'whoop'
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class LearningPreference(Base):
    __tablename__ = "learning_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    vark_style = Column(String(20), nullable=False, default='balanced')
    preferred_study_duration = Column(Integer, default=45)
    best_study_times = Column(JSON, default=list)
    difficulty_preference = Column(String(20), default='gradual')
    content_types = Column(JSON, default=list)
    last_vark_assessment = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

class StudyPlan(Base):
    __tablename__ = "study_plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    week_of = Column(DateTime, nullable=False)
    plan_data = Column(JSON, nullable=False)
    generated_by = Column(String(20), default='planner_agent')
    status = Column(String(20), default='active')
    created_at = Column(DateTime, server_default=func.now())

class ProactiveQuiz(Base):
    __tablename__ = "proactive_quizzes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    topic_id = Column(Integer)
    quiz_data = Column(JSON, nullable=False)
    difficulty = Column(Integer, default=1)
    completed = Column(Boolean, default=False)
    score = Column(DECIMAL)
    completed_at = Column(DateTime)
    generated_by = Column(String(20), default='tutor_agent')
    created_at = Column(DateTime, server_default=func.now())

class VarkContent(Base):
    __tablename__ = "vark_content"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    topic_id = Column(Integer)
    material_id = Column(Integer)
    learning_style = Column(String(20), nullable=False)
    content_type = Column(String(50), nullable=False)  # 'visual_guide', 'flashcards', 'case_study', etc.
    content = Column(JSON, nullable=False)
    generated_by = Column(String(20), default='generator_agent')
    created_at = Column(DateTime, server_default=func.now())

class BehavioralAnalysis(Base):
    __tablename__ = "behavioral_analysis"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    analysis_data = Column(JSON, nullable=False)
    interventions = Column(JSON, default=list)
    engagement_level = Column(DECIMAL)
    knowledge_decay_risk = Column(DECIMAL)
    average_performance = Column(DECIMAL)
    stress_level = Column(DECIMAL)
    generated_by = Column(String(20), default='observer_agent')
    created_at = Column(DateTime, server_default=func.now())

class AgentNotification(Base):
    __tablename__ = "agent_notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    agent_type = Column(String(20), nullable=False)  # 'planner', 'tutor', 'generator', 'observer'
    notification_type = Column(String(50), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    action_data = Column(JSON)
    priority = Column(String(10), default='medium')
    read = Column(Boolean, default=False)
    scheduled_for = Column(DateTime)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

class Flashcard(Base):
    __tablename__ = "flashcards"
    __table_args__ = {'schema': 'main'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    material_id = Column(Integer)
    topic_id = Column(Integer)
    front = Column(String, nullable=False)
    back = Column(String, nullable=False)
    difficulty = Column(Integer, default=1)
    tags = Column(JSON, default=list)
    memory_aid = Column(String)
    learning_style = Column(String(20))
    times_reviewed = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    last_reviewed = Column(DateTime)
    next_review = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

class LibraryContent(Base):
    __tablename__ = "library_content"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    material_id = Column(Integer)
    topic_id = Column(Integer)
    content_type = Column(String(20), nullable=False)  # 'case-study', 'audio', 'visual-guide', 'cheat-sheet'
    title = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    description = Column(String)
    difficulty = Column(Integer, default=1)
    estimated_duration = Column(Integer)
    source = Column(String)
    tags = Column(JSON, default=list)
    times_accessed = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

class VisualGuide(Base):
    __tablename__ = "visual_guides"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    topic_id = Column(Integer)
    title = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    svg_elements = Column(JSON)
    interactive_elements = Column(JSON)
    completion_status = Column(String(20), default='not_started')
    view_count = Column(Integer, default=0)
    last_viewed = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

class BiometricDevice(Base):
    __tablename__ = "biometric_devices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    device_type = Column(String(50), nullable=False)  # 'oura', 'apple_watch', 'fitbit', 'whoop'
    device_name = Column(String(100))
    api_key = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    connected = Column(Boolean, default=False)
    last_sync = Column(DateTime)
    sync_frequency = Column(Integer, default=60)  # minutes
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

# OAuth Tables
class OAuthState(Base):
    __tablename__ = "oauth_states"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)  # Can be null for anonymous sessions
    state = Column(String(64), nullable=False, unique=True)
    platform = Column(String(20), nullable=False)  # 'canvas', 'blackboard', etc.
    redirect_uri = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

class OAuthToken(Base):
    __tablename__ = "oauth_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    platform = Column(String(20), nullable=False)  # 'canvas', 'blackboard', etc.
    encrypted_access_token = Column(String, nullable=False)
    encrypted_refresh_token = Column(String)
    expires_at = Column(DateTime)
    scope = Column(String)
    token_metadata = Column(JSON)  # Additional platform-specific data
    last_refreshed = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

# Academic Study Plans
class AcademicStudyPlan(Base):
    __tablename__ = "academic_study_plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    class_name = Column(String, nullable=False)
    syllabus_file = Column(String)
    plan_type = Column(String, nullable=False)  # 'ai-generated' | 'custom'
    timeline = Column(JSON, nullable=False)
    exam_dates = Column(JSON)  # Array of exam dates
    difficulty = Column(Integer, default=1)
    total_weeks = Column(Integer, nullable=False)
    progress = Column(Integer, default=0)
    description = Column(String)
    goal_type = Column(String)  # 'course', 'board-exam', 'certification', 'personal'
    custom_goals = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

# Password Reset
class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False)
    token = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    used = Column(Boolean, default=False)

# Contact Messages
class ContactMessage(Base):
    __tablename__ = "contact_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    inquiry_type = Column(String, nullable=False)  # general, support, billing, partnership
    message = Column(String, nullable=False)
    status = Column(String, nullable=False, default="new")  # new, read, responded, archived
    created_at = Column(DateTime, server_default=func.now())
    responded_at = Column(DateTime)
    admin_notes = Column(String)

# Multi-Agent LMS Tables
class Artifact(Base):
    __tablename__ = "artifacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    concept_id = Column(Integer)
    user_id = Column(Integer, nullable=False)
    modality = Column(String(50), nullable=False)  # flashcard, cheatsheet, diagram, audio, video
    content_url = Column(String)
    content_blob = Column(String)  # Base64 encoded binary data
    artifact_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    scheduled_review = Column(DateTime)
    retention_score = Column(DECIMAL)
    times_reviewed = Column(Integer, default=0)
    last_reviewed = Column(DateTime)
    quality = Column(DECIMAL)  # 0.0-1.0 quality score
    generated_by = Column(String(50), default='ContentAgent')

class NotificationQueue(Base):
    __tablename__ = "notification_queue"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    artifact_id = Column(Integer)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, dismissed, completed
    notification_type = Column(String(50), nullable=False)
    priority = Column(Integer, default=5)  # 1-10, higher is more important
    created_at = Column(DateTime, server_default=func.now())
    sent_at = Column(DateTime)
    completed_at = Column(DateTime)
    payload = Column(JSON, default=dict)
    delivery_method = Column(String(30), default="push")  # push, email, in-app
    retry_count = Column(Integer, default=0)

class VectorIndexEntry(Base):
    __tablename__ = "vector_index_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # For user-specific queries
    content_hash = Column(String(64), unique=True)
    embedding = Column(JSON, nullable=False)  # Store vector as JSON array
    content = Column(Text, nullable=False)  # Changed to Text for longer content
    token_count = Column(Integer, default=0)  # Number of tokens in this chunk
    chunk_index = Column(Integer, default=0)  # Order of chunk in document
    
    # Source tracking
    source_type = Column(String(50), nullable=False)  # material, artifact, web, manual
    source_id = Column(Integer)  # References Material.id or other source
    
    # Metadata
    vector_metadata = Column(JSON, default=dict)
    embedding_model = Column(String, default="text-embedding-3-small")
    
    # Usage tracking
    created_at = Column(DateTime, server_default=func.now())
    last_accessed = Column(DateTime)
    access_count = Column(Integer, default=0)
    relevance_score = Column(DECIMAL)

class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(50), nullable=False)
    user_id = Column(Integer)
    action = Column(String(100), nullable=False)
    input = Column(JSON, default=dict)
    output = Column(JSON, default=dict)
    execution_time = Column(Integer)  # milliseconds
    status = Column(String(20), nullable=False)  # success, failure, timeout
    error_message = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class RagRetrievalLog(Base):
    __tablename__ = "rag_retrieval_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    query = Column(String, nullable=False)
    retrieved_docs = Column(JSON, nullable=False)
    relevance_scores = Column(JSON, nullable=False)
    iteration_count = Column(Integer, default=1)
    final_response = Column(String)
    response_quality = Column(DECIMAL)
    execution_time = Column(Integer)  # milliseconds
    created_at = Column(DateTime, server_default=func.now())

class FederationUpdate(Base):
    __tablename__ = "federation_updates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    subnet_id = Column(String(100), nullable=False)
    update_data = Column(JSON, nullable=False)
    update_type = Column(String(50), nullable=False)  # weights, gradients, metrics
    status = Column(String(20), nullable=False, default="pending")  # pending, aggregated, applied
    created_at = Column(DateTime, server_default=func.now())
    aggregated_at = Column(DateTime)

class MasteryScore(Base):
    __tablename__ = "mastery_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    concept_id = Column(Integer, nullable=False)
    mastery_level = Column(DECIMAL, nullable=False)  # 0.0-1.0
    readiness_score = Column(DECIMAL, nullable=False)  # 0.0-1.0
    last_assessed = Column(DateTime, server_default=func.now())
    assessment_count = Column(Integer, default=0)
    trend = Column(String(20))  # improving, stable, declining
    mastery_metadata = Column(JSON, default=dict)

class ModalityPreference(Base):
    __tablename__ = "modality_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    modality = Column(String(50), nullable=False)
    preference_score = Column(DECIMAL, nullable=False)  # 0.0-1.0
    success_rate = Column(DECIMAL)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

class AgentState(Base):
    __tablename__ = "agent_states"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(50), nullable=False)
    user_id = Column(Integer)
    current_state = Column(JSON, nullable=False)
    pending_tasks = Column(JSON, default=list)
    last_activity = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    agent_metadata = Column(JSON, default=dict)
    
# Profile Management
class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {'schema': 'main'}
    
    id = Column(UUID, primary_key=True)  
    full_name = Column(String, nullable=True)
    institution = Column(String, nullable=True)
    grad_year = Column(String, nullable=True)
    specialty = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


if __name__ == "__main__":
    if test_connection():
        print("\nInitializing database...")
        init_db()
