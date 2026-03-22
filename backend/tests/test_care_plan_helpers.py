from routers.care_plans import build_care_plan_text
from rag.extraction import chunk_text


def test_build_care_plan_text_includes_core_fields_and_labs():
    payload = {
        "patient_name": "John Doe",
        "procedure": "Appendectomy",
        "diagnosis": "Appendicitis",
        "na": "140",
        "k": "4.0",
    }

    result = build_care_plan_text(payload)

    assert "Patient: John Doe" in result
    assert "Procedure: Appendectomy" in result
    assert "Diagnosis: Appendicitis" in result
    assert "Laboratory Values:" in result
    assert "NA: 140" in result


def test_chunk_text_creates_multiple_chunks_with_overlap():
    text = " ".join(f"w{i}" for i in range(30))
    chunks = chunk_text(text, chunk_size=10, overlap=2)

    assert len(chunks) >= 3
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]
