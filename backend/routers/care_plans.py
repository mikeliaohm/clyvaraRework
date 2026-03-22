from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from config import openai_client, SYSTEM_USER_ID
from database import get_db, CarePlan, VectorIndexEntry
from deps import get_current_user
from rag.extraction import generate_embeddings

router = APIRouter(prefix="/api/care-plans", tags=["care-plans"])


# ── Helpers ───────────────────────────────────────────────────

def build_care_plan_text(care_plan_data: dict) -> str:
    sections = []
    for key, label in [
        ("patient_name", "Patient"), ("age", "Age"), ("sex", "Sex"),
        ("diagnosis", "Diagnosis"), ("procedure", "Procedure"),
        ("pmh", "Past Medical History"), ("psh", "Past Surgical History"),
        ("meds", "Current Medications"),
        ("neuro", "Neurological"), ("cardio", "Cardiovascular"), ("resp", "Respiratory"),
        ("mallampati", "Mallampati"), ("ulbt", "ULBT Grade"),
    ]:
        if care_plan_data.get(key):
            sections.append(f"{label}: {care_plan_data[key]}")

    lab_values = []
    for lab in ["na", "k", "cl", "co2", "bun", "cr", "glu", "wbc", "hgb", "hct", "plt", "pt", "ptt", "inr"]:
        if care_plan_data.get(lab):
            lab_values.append(f"{lab.upper()}: {care_plan_data[lab]}")
    if lab_values:
        sections.append(f"Laboratory Values: {', '.join(lab_values)}")

    return "\n".join(sections)


async def index_care_plan_for_rag(care_plan: CarePlan, db: Session) -> None:
    try:
        if not care_plan.exported_text:
            return
        embedding = generate_embeddings(care_plan.exported_text)
        db.add(VectorIndexEntry(
            user_id=care_plan.user_id,
            content_hash=f"care_plan_{care_plan.id}",
            embedding=embedding,
            content=care_plan.exported_text,
            token_count=len(care_plan.exported_text.split()),
            chunk_index=0,
            source_type="care_plan",
            source_id=care_plan.id,
            embedding_model="text-embedding-3-small",
            vector_metadata={
                "care_plan_id": care_plan.id,
                "patient_name": care_plan.patient_name,
                "procedure": care_plan.procedure,
                "diagnosis": care_plan.diagnosis,
                "created_at": care_plan.created_at.isoformat() if care_plan.created_at else None,
            },
        ))
        db.commit()
    except Exception as e:
        print(f"Error indexing care plan for RAG: {e}")


def build_care_plan_context(care_plan: CarePlan, db: Session) -> str:
    try:
        query_text = f"{care_plan.diagnosis} {care_plan.procedure} anesthesia care plan"
        query_embedding = generate_embeddings(query_text)

        vector_entries = db.query(VectorIndexEntry).filter(
            or_(
                VectorIndexEntry.user_id == care_plan.user_id,
                VectorIndexEntry.user_id == SYSTEM_USER_ID,
            )
        ).all()

        results = sorted(
            [
                {
                    "content": e.content,
                    "similarity": sum(a * b for a, b in zip(query_embedding, e.embedding)),
                    "metadata": e.vector_metadata,
                    "is_system": e.user_id == SYSTEM_USER_ID,
                }
                for e in vector_entries
            ],
            key=lambda x: x["similarity"],
            reverse=True,
        )[:5]

        context_parts = [f"Patient Care Plan:\n{care_plan.exported_text}"]
        if results:
            context_parts.append("\nRelevant Medical Literature:")
            for i, r in enumerate(results, 1):
                label = "System Textbook" if r.get("is_system") else "User Material"
                context_parts.append(
                    f"\n{i}. From {r['metadata'].get('file_name', 'Unknown Source')} ({label}):\n{r['content'][:300]}..."
                )
        return "\n".join(context_parts)
    except Exception as e:
        print(f"Error building care plan context: {e}")
        return care_plan.exported_text or ""


async def generate_care_plan_recommendations(context: str, client) -> dict:
    try:
        system_prompt = """You are an expert anesthesiologist AI assistant. Based on the patient information and relevant medical literature provided, generate comprehensive anesthesia care plan recommendations.

Please provide:
1. Anesthesia Plan: Detailed anesthesia approach including induction, maintenance, and emergence
2. Risk Assessment: Analysis of patient-specific risks and complications
3. Monitoring Plan: Required monitoring during the procedure
4. Medication Plan: Specific medications and dosages

Be specific, evidence-based, and consider the patient's comorbidities and procedure requirements."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context},
            ],
            max_tokens=1500,
        )
        return {
            "anesthesia_plan": response.choices[0].message.content,
            "risk_assessment": "",
            "monitoring_plan": "",
            "medication_plan": "",
            "sources": [],
            "confidence_score": 0.8,
        }
    except Exception as e:
        print(f"Error generating AI recommendations: {e}")
        return {
            "anesthesia_plan": "Error generating recommendations",
            "risk_assessment": "",
            "monitoring_plan": "",
            "medication_plan": "",
            "sources": [],
            "confidence_score": 0.0,
        }


# ── Endpoints ─────────────────────────────────────────────────

@router.post("")
async def create_care_plan(
    care_plan_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        care_plan = CarePlan(
            user_id=current_user["user_id"],
            title=care_plan_data.get("title", "Untitled Care Plan"),
            patient_name=care_plan_data.get("patient_name"),
            procedure=care_plan_data.get("procedure"),
            diagnosis=care_plan_data.get("diagnosis"),
            age=care_plan_data.get("age"),
            sex=care_plan_data.get("sex"),
            height=care_plan_data.get("height"),
            weight=care_plan_data.get("weight"),
            temperature_f=care_plan_data.get("tempF"),
            blood_pressure=care_plan_data.get("bp"),
            heart_rate=care_plan_data.get("hr"),
            respiration_rate=care_plan_data.get("rr"),
            oxygen_saturation=care_plan_data.get("oxygen_saturation"),
            lmp_date=care_plan_data.get("lmp_date"),
            past_medical_history=care_plan_data.get("pmh"),
            past_surgical_history=care_plan_data.get("psh"),
            anesthesia_history=care_plan_data.get("anesthesiaHx"),
            current_medications=care_plan_data.get("meds"),
            alcohol_use=care_plan_data.get("alcohol"),
            substance_use=care_plan_data.get("substance"),
            allergies=care_plan_data.get("allergies"),
            neurological_findings=care_plan_data.get("neuro"),
            heent_findings=care_plan_data.get("heent"),
            respiratory_findings=care_plan_data.get("resp"),
            cardiovascular_findings=care_plan_data.get("cardio"),
            gastrointestinal_findings=care_plan_data.get("gi"),
            genitourinary_findings=care_plan_data.get("gu"),
            endocrine_findings=care_plan_data.get("endo"),
            other_findings=care_plan_data.get("otherFindings"),
            mallampati_class=care_plan_data.get("mallampati"),
            ulbt_grade=care_plan_data.get("ulbt"),
            thyromental_distance=care_plan_data.get("thyromental"),
            interincisor_distance=care_plan_data.get("interincisor"),
            dentition=care_plan_data.get("dentition"),
            neck_assessment=care_plan_data.get("neck"),
            oral_mucosa=care_plan_data.get("oralMucosa"),
            sodium=care_plan_data.get("na"),
            potassium=care_plan_data.get("k"),
            chloride=care_plan_data.get("cl"),
            co2=care_plan_data.get("co2"),
            bun=care_plan_data.get("bun"),
            creatinine=care_plan_data.get("cr"),
            glucose=care_plan_data.get("glu"),
            wbc=care_plan_data.get("wbc"),
            hemoglobin=care_plan_data.get("hgb"),
            hematocrit=care_plan_data.get("hct"),
            platelets=care_plan_data.get("plt"),
            pt=care_plan_data.get("pt"),
            ptt=care_plan_data.get("ptt"),
            inr=care_plan_data.get("inr"),
            abg=care_plan_data.get("abg"),
            other_labs=care_plan_data.get("otherLabs"),
            ekg=care_plan_data.get("ekg"),
            chest_xray=care_plan_data.get("cxr"),
            echocardiogram=care_plan_data.get("echo"),
            other_imaging=care_plan_data.get("otherImaging"),
            cultural_religious_attributes=care_plan_data.get("cultural_religious_attributes"),
            exported_text=build_care_plan_text(care_plan_data),
            export_hash=hash(str(care_plan_data)),
        )
        db.add(care_plan)
        db.commit()
        db.refresh(care_plan)
        await index_care_plan_for_rag(care_plan, db)
        return {"success": True, "care_plan_id": care_plan.id, "message": "Care plan created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating care plan: {str(e)}")


@router.get("")
async def get_care_plans(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        care_plans = (
            db.query(CarePlan)
            .filter(CarePlan.user_id == current_user["user_id"])
            .order_by(CarePlan.created_at.desc())
            .all()
        )
        return {
            "success": True,
            "care_plans": [
                {
                    "id": cp.id,
                    "title": cp.title,
                    "patient_name": cp.patient_name,
                    "procedure": cp.procedure,
                    "diagnosis": cp.diagnosis,
                    "status": cp.status,
                    "created_at": cp.created_at.isoformat() if cp.created_at else None,
                    "updated_at": cp.updated_at.isoformat() if cp.updated_at else None,
                }
                for cp in care_plans
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching care plans: {str(e)}")


@router.get("/{care_plan_id}")
async def get_care_plan(
    care_plan_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        care_plan = db.query(CarePlan).filter(
            CarePlan.id == care_plan_id,
            CarePlan.user_id == current_user["user_id"],
        ).first()

        if not care_plan:
            raise HTTPException(status_code=404, detail="Care plan not found")

        care_plan.last_accessed = func.now()
        db.commit()

        return {
            "success": True,
            "care_plan": {
                "id": care_plan.id,
                "title": care_plan.title,
                "patient_name": care_plan.patient_name,
                "procedure": care_plan.procedure,
                "diagnosis": care_plan.diagnosis,
                "age": care_plan.age,
                "sex": care_plan.sex,
                "height": care_plan.height,
                "weight": care_plan.weight,
                "tempF": care_plan.temperature_f,
                "bp": care_plan.blood_pressure,
                "hr": care_plan.heart_rate,
                "rr": care_plan.respiration_rate,
                "oxygen_saturation": care_plan.oxygen_saturation,
                "lmp_date": care_plan.lmp_date,
                "pmh": care_plan.past_medical_history,
                "psh": care_plan.past_surgical_history,
                "anesthesiaHx": care_plan.anesthesia_history,
                "meds": care_plan.current_medications,
                "alcohol": care_plan.alcohol_use,
                "substance": care_plan.substance_use,
                "allergies": care_plan.allergies,
                "neuro": care_plan.neurological_findings,
                "heent": care_plan.heent_findings,
                "resp": care_plan.respiratory_findings,
                "cardio": care_plan.cardiovascular_findings,
                "gi": care_plan.gastrointestinal_findings,
                "gu": care_plan.genitourinary_findings,
                "endo": care_plan.endocrine_findings,
                "otherFindings": care_plan.other_findings,
                "mallampati": care_plan.mallampati_class,
                "ulbt": care_plan.ulbt_grade,
                "thyromental": care_plan.thyromental_distance,
                "interincisor": care_plan.interincisor_distance,
                "dentition": care_plan.dentition,
                "neck": care_plan.neck_assessment,
                "oralMucosa": care_plan.oral_mucosa,
                "na": care_plan.sodium,
                "k": care_plan.potassium,
                "cl": care_plan.chloride,
                "co2": care_plan.co2,
                "bun": care_plan.bun,
                "cr": care_plan.creatinine,
                "glu": care_plan.glucose,
                "wbc": care_plan.wbc,
                "hgb": care_plan.hemoglobin,
                "hct": care_plan.hematocrit,
                "plt": care_plan.platelets,
                "pt": care_plan.pt,
                "ptt": care_plan.ptt,
                "inr": care_plan.inr,
                "abg": care_plan.abg,
                "otherLabs": care_plan.other_labs,
                "ekg": care_plan.ekg,
                "cxr": care_plan.chest_xray,
                "echo": care_plan.echocardiogram,
                "otherImaging": care_plan.other_imaging,
                "cultural_religious_attributes": care_plan.cultural_religious_attributes,
                "ai_recommendations": care_plan.ai_recommendations,
                "risk_assessment": care_plan.risk_assessment,
                "monitoring_plan": care_plan.monitoring_plan,
                "medication_plan": care_plan.medication_plan,
                "status": care_plan.status,
                "version": care_plan.version,
                "created_at": care_plan.created_at.isoformat() if care_plan.created_at else None,
                "updated_at": care_plan.updated_at.isoformat() if care_plan.updated_at else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching care plan: {str(e)}")


@router.post("/{care_plan_id}/generate-ai")
async def generate_ai_recommendations_endpoint(
    care_plan_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        care_plan = db.query(CarePlan).filter(
            CarePlan.id == care_plan_id,
            CarePlan.user_id == current_user["user_id"],
        ).first()

        if not care_plan:
            raise HTTPException(status_code=404, detail="Care plan not found")
        if not openai_client:
            raise HTTPException(status_code=503, detail="OpenAI client not configured")

        context = build_care_plan_context(care_plan, db)
        recommendations = await generate_care_plan_recommendations(context, openai_client)

        care_plan.ai_recommendations = recommendations.get("anesthesia_plan", "")
        care_plan.risk_assessment = recommendations.get("risk_assessment", "")
        care_plan.monitoring_plan = recommendations.get("monitoring_plan", "")
        care_plan.medication_plan = recommendations.get("medication_plan", "")
        care_plan.rag_context = context
        care_plan.rag_sources = recommendations.get("sources", [])
        care_plan.rag_confidence_score = recommendations.get("confidence_score", 0.0)
        care_plan.updated_at = func.now()
        db.commit()

        return {"success": True, "recommendations": recommendations, "message": "AI recommendations generated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating AI recommendations: {str(e)}")


@router.delete("/{care_plan_id}")
async def delete_care_plan(
    care_plan_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        care_plan = db.query(CarePlan).filter(
            CarePlan.id == care_plan_id,
            CarePlan.user_id == current_user["user_id"],
        ).first()

        if not care_plan:
            raise HTTPException(status_code=404, detail="Care plan not found")

        db.query(VectorIndexEntry).filter(
            VectorIndexEntry.source_id == care_plan_id,
            VectorIndexEntry.source_type == "care_plan",
        ).delete()

        db.delete(care_plan)
        db.commit()
        return {"success": True, "message": "Care plan deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting care plan: {str(e)}")
