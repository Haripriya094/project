"""
AI Resume Analyzer Backend
Uses Ollama (local LLM) — no API key required
Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import json
import re
import time
import uuid
from typing import Optional

import pdfplumber
import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="AI Resume Analyzer API",
    description="Analyzes resumes vs job descriptions using a local LLM (Ollama)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Config — change model name if needed
# ─────────────────────────────────────────────
# OLLAMA_URL = "http://localhost:11434/api/generate"
# #OLLAMA_MODEL = "llama3"
# OLLAMA_MODEL = "phi3"# fallback chain: llama3 → mistral → phi3
# FALLBACK_MODELS = ["mistral", "phi3", "gemma2", "llama2"]

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"
FALLBACK_MODELS = ["tinyllama"]


# ─────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────
class MCQQuestion(BaseModel):
    id: int
    question: str
    options: list[str]
    correct_answer: str
    explanation: str
    topic: str


class CodingQuestion(BaseModel):
    id: int
    title: str
    description: str
    examples: list[dict]
    hints: list[str]
    difficulty: str
    topic: str
    sample_solution: str


class AnalysisResult(BaseModel):
    session_id: str
    resume_text: str
    job_description_text: str
    skills_extracted: list[str]
    mcq_questions: list[MCQQuestion]
    coding_questions: list[CodingQuestion]
    feedback: dict
    match_score: dict


class AnswerSubmission(BaseModel):
    session_id: str
    mcq_answers: dict[str, str]          # question_id → selected option
    coding_answers: dict[str, str]       # question_id → code string


# ─────────────────────────────────────────────
# In-memory session store (use Redis/DB in prod)
# ─────────────────────────────────────────────
sessions: dict[str, dict] = {}


# ─────────────────────────────────────────────
# Helper: pick a working Ollama model
# ─────────────────────────────────────────────
def get_available_model() -> str:
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"].split(":")[0] for m in resp.json().get("models", [])]
            for candidate in [OLLAMA_MODEL] + FALLBACK_MODELS:
                if candidate in models:
                    return candidate
    except Exception:
        pass
    return OLLAMA_MODEL   # best guess


# ─────────────────────────────────────────────
# Helper: call Ollama
# ─────────────────────────────────────────────
def call_llm(prompt: str, max_tokens: int = 4096) -> str:
    model = get_available_model()
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.3,
            "top_p": 0.9,
        },
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with: ollama serve",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


# ─────────────────────────────────────────────
# Helper: extract text from PDF bytes
# ─────────────────────────────────────────────
def extract_pdf_text(pdf_bytes: bytes) -> str:
    import io
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts).strip()


# ─────────────────────────────────────────────
# Helper: safe JSON parse from LLM output
# ─────────────────────────────────────────────
def safe_json_parse(text: str) -> dict | list:
    # Try to pull out the first JSON object or array
    text = text.strip()
    for pattern in [r"\{.*\}", r"\[.*\]"]:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    # Try the whole string
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


# ─────────────────────────────────────────────
# Core pipeline functions
# ─────────────────────────────────────────────

def extract_skills(resume_text: str, jd_text: str) -> list[str]:
    prompt = f"""
You are a technical recruiter. Extract all technical and soft skills from the resume below.
Return ONLY a JSON array of strings (skill names). No explanation.

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION:
{jd_text[:2000]}

Return format: ["skill1", "skill2", ...]
"""
    raw = call_llm(prompt, 512)
    result = safe_json_parse(raw)
    if isinstance(result, list):
        return [str(s) for s in result]
    return ["Python", "Problem Solving", "Communication"]   # safe default


def generate_mcq(resume_text: str, jd_text: str, skills: list[str], count: int = 30) -> list[dict]:
    skills_str = ", ".join(skills[:15])
    prompt = f"""
You are an expert technical interviewer. Generate exactly {count} multiple-choice questions
to assess the candidate based on their resume and the job description.

Topics MUST cover: {skills_str}

Rules:
- Each question has exactly 4 options labeled A, B, C, D
- Include questions from: programming concepts, data structures, algorithms,
  system design, domain knowledge, and role-specific topics
- Mix difficulty: 30% easy, 50% medium, 20% hard
- correct_answer must be exactly one of: "A", "B", "C", or "D"

Return ONLY valid JSON (no markdown, no explanation):
{{
  "questions": [
    {{
      "id": 1,
      "question": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "A",
      "explanation": "...",
      "topic": "..."
    }}
  ]
}}

RESUME SNIPPET:
{resume_text[:2000]}

JOB DESCRIPTION SNIPPET:
{jd_text[:1500]}
"""
    raw = call_llm(prompt, 6000)
    parsed = safe_json_parse(raw)
    questions = parsed.get("questions", []) if isinstance(parsed, dict) else []

    # Ensure we always return something
    if not questions:
        questions = _fallback_mcq(skills)

    return questions[:count]


def _fallback_mcq(skills: list[str]) -> list[dict]:
    """Static fallback questions if LLM fails."""
    return [
        {
            "id": i + 1,
            "question": f"Which of the following best describes {skill}?",
            "options": [
                f"A. A fundamental concept in {skill}",
                "B. A database management tool",
                "C. A version control system",
                "D. A cloud platform service",
            ],
            "correct_answer": "A",
            "explanation": f"{skill} is a core technical skill.",
            "topic": skill,
        }
        for i, skill in enumerate(skills[:30])
    ]


def generate_coding_questions(resume_text: str, jd_text: str, skills: list[str]) -> list[dict]:
    lang_skills = [s for s in skills if s.lower() in
                   {"python", "java", "javascript", "c++", "golang", "rust", "typescript", "sql"}]
    primary_lang = lang_skills[0] if lang_skills else "Python"

    prompt = f"""
You are a senior software engineer conducting a coding interview.
Generate 5 coding problems appropriate for the candidate's profile.

Primary language: {primary_lang}
Skills: {", ".join(skills[:10])}

Mix of topics: arrays/strings, data structures, algorithms, SQL, system design snippet.

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "id": 1,
      "title": "...",
      "description": "Full problem statement...",
      "examples": [
        {{"input": "...", "output": "...", "explanation": "..."}}
      ],
      "hints": ["hint1", "hint2"],
      "difficulty": "Easy|Medium|Hard",
      "topic": "Arrays",
      "sample_solution": "# Complete working solution in {primary_lang}\\n..."
    }}
  ]
}}

RESUME SNIPPET:
{resume_text[:1500]}

JOB DESCRIPTION SNIPPET:
{jd_text[:1000]}
"""
    raw = call_llm(prompt, 4000)
    parsed = safe_json_parse(raw)
    questions = parsed.get("questions", []) if isinstance(parsed, dict) else []

    if not questions:
        questions = _fallback_coding(primary_lang)

    return questions[:5]


def _fallback_coding(lang: str) -> list[dict]:
    return [
        {
            "id": 1,
            "title": "Two Sum",
            "description": "Given an array of integers and a target, return indices of the two numbers that add up to the target.",
            "examples": [{"input": "nums=[2,7,11,15], target=9", "output": "[0,1]", "explanation": "nums[0]+nums[1]=9"}],
            "hints": ["Use a hash map for O(n) solution"],
            "difficulty": "Easy",
            "topic": "Arrays",
            "sample_solution": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i",
        }
    ]


def generate_feedback(resume_text: str, jd_text: str, skills: list[str]) -> dict:
    prompt = f"""
You are a professional career coach and technical recruiter. Provide detailed feedback on this resume
compared to the job description.

Return ONLY valid JSON:
{{
  "overall_assessment": "2-3 sentence summary",
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2"],
  "missing_skills": ["skill1", "skill2"],
  "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
  "ats_tips": ["tip1", "tip2"],
  "experience_gap": "analysis of experience vs requirements",
  "keyword_optimization": ["keyword1", "keyword2"],
  "resume_format_tips": ["format_tip1", "format_tip2"],
  "interview_preparation": ["prep_tip1", "prep_tip2", "prep_tip3"]
}}

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION:
{jd_text[:2000]}
"""
    raw = call_llm(prompt, 2000)
    parsed = safe_json_parse(raw)
    if isinstance(parsed, dict) and "overall_assessment" in parsed:
        return parsed
    return {
        "overall_assessment": "Analysis complete. Please review the match score for details.",
        "strengths": ["Technical background identified"],
        "weaknesses": ["Resume needs more quantified achievements"],
        "missing_skills": [],
        "recommendations": ["Add metrics to your experience bullets", "Tailor resume to each role"],
        "ats_tips": ["Use keywords from the job description"],
        "experience_gap": "Unable to fully parse — please ensure your PDF has selectable text.",
        "keyword_optimization": [],
        "resume_format_tips": ["Keep to 1-2 pages"],
        "interview_preparation": ["Review core concepts for listed skills"],
    }


def compute_match_score(resume_text: str, jd_text: str, skills: list[str]) -> dict:
    prompt = f"""
You are a technical recruiter scoring a resume against a job description.
Score each category 0-100 and provide brief reasoning.

Return ONLY valid JSON:
{{
  "overall_score": 75,
  "skill_match": {{
    "score": 80,
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3"],
    "reasoning": "..."
  }},
  "experience_match": {{
    "score": 70,
    "reasoning": "..."
  }},
  "education_match": {{
    "score": 85,
    "reasoning": "..."
  }},
  "keyword_density": {{
    "score": 65,
    "top_keywords": ["kw1", "kw2"],
    "reasoning": "..."
  }},
  "cultural_fit": {{
    "score": 75,
    "reasoning": "..."
  }},
  "recommendation": "Strong Match | Good Match | Partial Match | Weak Match",
  "hiring_probability": "High | Medium | Low",
  "summary": "One paragraph summary of match quality"
}}

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION:
{jd_text[:2000]}

EXTRACTED SKILLS:
{", ".join(skills)}
"""
    raw = call_llm(prompt, 1500)
    parsed = safe_json_parse(raw)
    if isinstance(parsed, dict) and "overall_score" in parsed:
        return parsed
    return {
        "overall_score": 60,
        "skill_match": {"score": 60, "matched_skills": skills[:5], "missing_skills": [], "reasoning": "Partial match detected."},
        "experience_match": {"score": 60, "reasoning": "Experience evaluation pending."},
        "education_match": {"score": 70, "reasoning": "Education details parsed."},
        "keyword_density": {"score": 55, "top_keywords": [], "reasoning": "Increase keyword density."},
        "cultural_fit": {"score": 65, "reasoning": "Culture indicators present."},
        "recommendation": "Partial Match",
        "hiring_probability": "Medium",
        "summary": "Moderate match. Tailor resume with more job-specific keywords.",
    }


def evaluate_answers(session_id: str, mcq_answers: dict, coding_answers: dict) -> dict:
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # ── MCQ scoring ──────────────────────────────
    mcq_questions = session["mcq_questions"]
    mcq_score = 0
    mcq_results = []

    for q in mcq_questions:
        qid = str(q["id"])
        user_ans = mcq_answers.get(qid, "").upper().strip()
        correct = q["correct_answer"].upper().strip()
        is_correct = user_ans == correct
        if is_correct:
            mcq_score += 1
        mcq_results.append({
            "id": q["id"],
            "question": q["question"],
            "user_answer": user_ans,
            "correct_answer": correct,
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
            "topic": q.get("topic", ""),
        })

    mcq_percentage = (mcq_score / len(mcq_questions) * 100) if mcq_questions else 0

    # ── Coding evaluation via LLM ─────────────────
    coding_results = []
    for q in session["coding_questions"]:
        qid = str(q["id"])
        user_code = coding_answers.get(qid, "").strip()
        if not user_code:
            coding_results.append({
                "id": q["id"],
                "title": q["title"],
                "score": 0,
                "feedback": "No answer submitted.",
                "time_complexity": "N/A",
                "space_complexity": "N/A",
                "correctness": False,
                "suggestions": ["Please attempt the problem."],
            })
            continue

        eval_prompt = f"""
Evaluate this code solution for the given problem. Be constructive and specific.

PROBLEM: {q["title"]}
{q["description"]}

SAMPLE SOLUTION:
{q.get("sample_solution", "")}

CANDIDATE'S CODE:
{user_code}

Return ONLY valid JSON:
{{
  "score": 7,
  "correctness": true,
  "feedback": "Overall assessment...",
  "time_complexity": "O(n)",
  "space_complexity": "O(1)",
  "suggestions": ["improvement1", "improvement2"],
  "code_quality": "Good|Fair|Poor",
  "edge_cases_handled": true
}}
"""
        raw = call_llm(eval_prompt, 800)
        result = safe_json_parse(raw)
        if not isinstance(result, dict):
            result = {}

        coding_results.append({
            "id": q["id"],
            "title": q["title"],
            "score": result.get("score", 5),
            "feedback": result.get("feedback", "Code reviewed."),
            "time_complexity": result.get("time_complexity", "N/A"),
            "space_complexity": result.get("space_complexity", "N/A"),
            "correctness": result.get("correctness", False),
            "suggestions": result.get("suggestions", []),
            "code_quality": result.get("code_quality", "Fair"),
        })

    coding_total = sum(r["score"] for r in coding_results)
    coding_max = len(coding_results) * 10
    coding_percentage = (coding_total / coding_max * 100) if coding_max else 0

    # ── Combined score ────────────────────────────
    combined = (mcq_percentage * 0.6) + (coding_percentage * 0.4)

    return {
        "session_id": session_id,
        "mcq": {
            "score": mcq_score,
            "total": len(mcq_questions),
            "percentage": round(mcq_percentage, 1),
            "results": mcq_results,
            "topic_breakdown": _topic_breakdown(mcq_results),
        },
        "coding": {
            "score": coding_total,
            "max_score": coding_max,
            "percentage": round(coding_percentage, 1),
            "results": coding_results,
        },
        "combined_score": round(combined, 1),
        "grade": _grade(combined),
        "performance_summary": _performance_summary(combined, mcq_percentage, coding_percentage),
    }


def _topic_breakdown(mcq_results: list) -> dict:
    breakdown: dict[str, dict] = {}
    for r in mcq_results:
        topic = r.get("topic", "General")
        if topic not in breakdown:
            breakdown[topic] = {"correct": 0, "total": 0}
        breakdown[topic]["total"] += 1
        if r["is_correct"]:
            breakdown[topic]["correct"] += 1
    return {
        t: {"correct": v["correct"], "total": v["total"],
            "percentage": round(v["correct"] / v["total"] * 100, 1)}
        for t, v in breakdown.items()
    }


def _grade(score: float) -> str:
    if score >= 90: return "A+ (Exceptional)"
    if score >= 80: return "A (Excellent)"
    if score >= 70: return "B (Good)"
    if score >= 60: return "C (Average)"
    if score >= 50: return "D (Below Average)"
    return "F (Needs Improvement)"


def _performance_summary(combined: float, mcq: float, coding: float) -> str:
    level = "strong" if combined >= 70 else "moderate" if combined >= 50 else "weak"
    return (
        f"Overall performance is {level} with a combined score of {combined:.1f}%. "
        f"MCQ: {mcq:.1f}% | Coding: {coding:.1f}%. "
        + ("Great job! You're well-prepared for this role." if combined >= 70
           else "Keep practicing — focus on weak topic areas." if combined >= 50
           else "Significant preparation needed. Review fundamentals and practice regularly.")
    )


# ─────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "AI Resume Analyzer API is running!", "docs": "/docs"}


@app.get("/health")
def health():
    model = get_available_model()
    try:
        requests.get("http://localhost:11434/api/tags", timeout=3)
        ollama_status = "running"
    except Exception:
        ollama_status = "not running"
    return {"status": "ok", "ollama": ollama_status, "model": model}


@app.post("/analyze", response_model=None)
async def analyze_resume(
    resume: UploadFile = File(..., description="Resume PDF"),
    job_description: UploadFile = File(..., description="Job Description PDF"),
):
    """
    Upload resume and job description PDFs.
    Returns MCQ questions, coding questions, feedback, and match score.
    """
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Resume must be a PDF file")
    if not job_description.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Job description must be a PDF file")

    resume_bytes = await resume.read()
    jd_bytes = await job_description.read()

    resume_text = extract_pdf_text(resume_bytes)
    jd_text = extract_pdf_text(jd_bytes)

    if not resume_text:
        raise HTTPException(status_code=422, detail="Could not extract text from resume PDF. Ensure it has selectable text (not a scanned image).")
    if not jd_text:
        raise HTTPException(status_code=422, detail="Could not extract text from job description PDF.")

    # Run pipeline
    skills = extract_skills(resume_text, jd_text)
    mcq_questions = generate_mcq(resume_text, jd_text, skills, count=30)
    coding_questions = generate_coding_questions(resume_text, jd_text, skills)
    feedback = generate_feedback(resume_text, jd_text, skills)
    match_score = compute_match_score(resume_text, jd_text, skills)

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "resume_text": resume_text,
        "job_description_text": jd_text,
        "skills_extracted": skills,
        "mcq_questions": mcq_questions,
        "coding_questions": coding_questions,
        "feedback": feedback,
        "match_score": match_score,
        "created_at": time.time(),
    }

    return {
        "session_id": session_id,
        "resume_text": resume_text[:500] + "...",   # truncated for response size
        "job_description_text": jd_text[:300] + "...",
        "skills_extracted": skills,
        "mcq_questions": mcq_questions,
        "coding_questions": coding_questions,
        "feedback": feedback,
        "match_score": match_score,
    }


@app.post("/submit-answers")
async def submit_answers(submission: AnswerSubmission):
    """Submit MCQ and coding answers for evaluation."""
    result = evaluate_answers(
        submission.session_id,
        submission.mcq_answers,
        submission.coding_answers,
    )
    return result


@app.get("/session/{session_id}")
def get_session(session_id: str):
    """Retrieve a previous analysis session."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    sessions.pop(session_id, None)
    return {"message": "Session deleted"}