import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import openai_client, SYSTEM_USER_ID
from database import get_db, LearningPlan, LearningPlanProgress
from deps import get_current_user

router = APIRouter(tags=["learning-plans"])


# ── Schemas ───────────────────────────────────────────────────

class GenerateQuestionsRequest(BaseModel):
    case_study: Optional[str] = None
    topic: Optional[str] = None
    num_questions: int = 3


class CreateLearningPlanRequest(BaseModel):
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    video_title: Optional[str] = None
    video_duration: Optional[int] = None
    case_study: str
    case_study_editable: bool = False
    quiz_questions: List[Dict[str, Any]]
    topic: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration: Optional[int] = None


class SubmitQuizRequest(BaseModel):
    learning_plan_id: int
    quiz_answers: Dict[str, int]
    video_watched: Optional[bool] = False
    case_study_read: Optional[bool] = False


# ── Endpoints ─────────────────────────────────────────────────

@router.get("/test-learning-plan")
def test_learning_plan_endpoint():
    return {"message": "Learning plan endpoint is working"}


@router.post("/api/learning-plan/generate-questions")
async def generate_learning_plan_questions(
    request: GenerateQuestionsRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not configured")

    try:
        use_general_query = not request.case_study and not request.topic
        if request.case_study:
            query_text = f"Case Study: {request.case_study}"
        elif request.topic:
            query_text = f"Topic: {request.topic}"
        else:
            query_text = "medical education anesthesia nursing clinical concepts"

        relevant_context = ""
        try:
            from rag.embedder import get_embedder
            from rag.pipeline import search_chunks

            embedder = get_embedder()
            user_id = SYSTEM_USER_ID if use_general_query else current_user["user_id"]
            results = search_chunks(
                query=query_text,
                user_id=user_id,
                db=db,
                embedder=embedder,
                top_k=3,
            )

            if results:
                relevant_context = "\n\nRelevant information:\n"
                for r in results:
                    relevant_context += f"\n{r.get('content', '')[:400]}\n"

        except Exception as e:
            print(f"RAG search error: {e}")

        if use_general_query:
            system_prompt = f"""Generate {request.num_questions} medical multiple-choice questions. Return ONLY JSON array:
[{{"id":"q1","type":"single","text":"Question?","options":["A","B","C","D"],"correctIndex":0,"explanation":"Why correct"}}]"""
            user_prompt = f"Based on: {relevant_context}\n\nGenerate {request.num_questions} diverse medical questions."
        else:
            system_prompt = f"""Generate {request.num_questions} medical questions. Return ONLY JSON:
[{{"id":"q1","type":"single","text":"Question?","options":["A","B","C","D"],"correctIndex":0,"explanation":"Why"}}]"""
            user_prompt = f"{query_text}\n\n{relevant_context}\n\nGenerate {request.num_questions} questions."

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            max_tokens=800,
            temperature=0.7,
            stream=False,
        )

        ai_response = response.choices[0].message.content.strip()
        for prefix in ("```json", "```"):
            if ai_response.startswith(prefix):
                ai_response = ai_response[len(prefix):]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        ai_response = ai_response.strip()

        try:
            questions = json.loads(ai_response)
            validated = []
            for i, q in enumerate(questions):
                if not isinstance(q, dict):
                    continue
                vq = {
                    "id": q.get("id", f"q{i+1}"),
                    "type": q.get("type", "single"),
                    "text": q.get("text", ""),
                    "options": q.get("options", []),
                    "correctIndex": q.get("correctIndex", 0),
                    "explanation": q.get("explanation", ""),
                }
                if len(vq["options"]) != 4:
                    continue
                if not (0 <= vq["correctIndex"] < 4):
                    vq["correctIndex"] = 0
                validated.append(vq)

            if not validated:
                raise ValueError("No valid questions generated")

            return {"success": True, "questions": validated, "num_generated": len(validated)}
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Error parsing generated questions: {ai_response[:200]}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error validating generated questions: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@router.post("/api/learning-plans")
async def create_or_get_learning_plan(
    request: CreateLearningPlanRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_id = current_user["user_id"]
        learning_plan = LearningPlan(
            user_id=user_id,
            title=request.title,
            description=request.description,
            video_url=request.video_url,
            video_title=request.video_title,
            video_duration=request.video_duration,
            case_study=request.case_study,
            case_study_editable=request.case_study_editable,
            quiz_questions=request.quiz_questions,
            topic=request.topic,
            difficulty_level=request.difficulty_level,
            estimated_duration=request.estimated_duration,
            created_by=user_id,
        )
        db.add(learning_plan)
        db.commit()
        db.refresh(learning_plan)
        return {"success": True, "learning_plan_id": learning_plan.id, "message": "Learning plan created successfully", "is_new": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating learning plan: {str(e)}")


@router.post("/api/learning-plans/submit-quiz")
async def submit_learning_plan_quiz(
    request: SubmitQuizRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_id = current_user["user_id"]
        learning_plan = db.query(LearningPlan).filter(
            LearningPlan.id == request.learning_plan_id,
            LearningPlan.user_id == user_id,
        ).first()

        if not learning_plan:
            raise HTTPException(status_code=404, detail="Learning plan not found")

        questions = learning_plan.quiz_questions if isinstance(learning_plan.quiz_questions, list) else []
        correct = sum(
            1 for q in questions
            if (request.quiz_answers.get(str(q.get("id"))) or request.quiz_answers.get(q.get("id"))) == q.get("correctIndex")
        )
        total = len(questions)
        percentage = (correct / total * 100) if total > 0 else 0

        attempt_count = db.query(LearningPlanProgress).filter(
            LearningPlanProgress.user_id == user_id,
            LearningPlanProgress.learning_plan_id == request.learning_plan_id,
            LearningPlanProgress.quiz_submitted == True,
        ).count() + 1

        base = db.query(LearningPlanProgress).filter(
            LearningPlanProgress.user_id == user_id,
            LearningPlanProgress.learning_plan_id == request.learning_plan_id,
        ).order_by(LearningPlanProgress.started_at.desc()).first()

        progress = LearningPlanProgress(
            user_id=user_id,
            learning_plan_id=request.learning_plan_id,
            video_watched=base.video_watched if base else (request.video_watched or False),
            video_watched_at=base.video_watched_at if base and base.video_watched else None,
            video_progress=base.video_progress if base else 0,
            case_study_read=base.case_study_read if base else (request.case_study_read or False),
            case_study_read_at=base.case_study_read_at if base and base.case_study_read else None,
            quiz_submitted=True,
            quiz_submitted_at=func.now(),
            quiz_answers=request.quiz_answers,
            quiz_score=correct,
            quiz_total=total,
            quiz_percentage=percentage,
            attempt_count=attempt_count,
            last_accessed=func.now(),
        )

        if request.video_watched and not progress.video_watched:
            progress.video_watched = True
            progress.video_watched_at = func.now()
        if request.case_study_read and not progress.case_study_read:
            progress.case_study_read = True
            progress.case_study_read_at = func.now()
        if progress.video_watched and progress.case_study_read and progress.quiz_submitted:
            progress.completed = True
            progress.completed_at = func.now()

        db.add(progress)
        db.commit()
        db.refresh(progress)

        return {
            "success": True,
            "message": "Quiz submitted successfully",
            "score": correct,
            "total": total,
            "percentage": float(percentage),
            "completed": progress.completed,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting quiz: {str(e)}")


@router.get("/api/learning-plans/{learning_plan_id}/progress")
async def get_learning_plan_progress(
    learning_plan_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_id = current_user["user_id"]
        all_progress = (
            db.query(LearningPlanProgress)
            .filter(
                LearningPlanProgress.user_id == user_id,
                LearningPlanProgress.learning_plan_id == learning_plan_id,
            )
            .order_by(LearningPlanProgress.quiz_submitted_at.desc(), LearningPlanProgress.started_at.desc())
            .all()
        )

        if not all_progress:
            return {"success": True, "progress": None, "quiz_attempts": [], "message": "No progress found"}

        latest = all_progress[0]
        quiz_attempts = [
            {
                "id": p.id,
                "quiz_submitted_at": p.quiz_submitted_at.isoformat() if p.quiz_submitted_at else None,
                "quiz_answers": p.quiz_answers,
                "quiz_score": p.quiz_score,
                "quiz_total": p.quiz_total,
                "quiz_percentage": float(p.quiz_percentage) if p.quiz_percentage else None,
                "attempt_number": p.attempt_count,
            }
            for p in all_progress if p.quiz_submitted
        ]

        return {
            "success": True,
            "progress": {
                "id": latest.id,
                "video_watched": latest.video_watched,
                "video_watched_at": latest.video_watched_at.isoformat() if latest.video_watched_at else None,
                "video_progress": latest.video_progress,
                "case_study_read": latest.case_study_read,
                "case_study_read_at": latest.case_study_read_at.isoformat() if latest.case_study_read_at else None,
                "completed": latest.completed,
                "completed_at": latest.completed_at.isoformat() if latest.completed_at else None,
                "started_at": latest.started_at.isoformat() if latest.started_at else None,
                "total_quiz_attempts": len(quiz_attempts),
            },
            "quiz_attempts": quiz_attempts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching progress: {str(e)}")
