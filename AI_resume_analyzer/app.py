"""
AI Resume Analyzer — Streamlit Frontend
Run: streamlit run app.py
"""

import json
import time
import requests
import streamlit as st

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
API_BASE = "http://localhost:8000"

# ─────────────────────────────────────────────
# Page setup
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────
st.markdown("""
<style>
  .main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem; border-radius: 12px; color: white;
    text-align: center; margin-bottom: 2rem;
  }
  .score-card {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    padding: 1.5rem; border-radius: 10px; color: white;
    text-align: center; margin: 0.5rem 0;
  }
  .skill-tag {
    display: inline-block; background: #e8f4f8;
    border: 1px solid #bee3f8; border-radius: 20px;
    padding: 4px 12px; margin: 3px; font-size: 13px; color: #2b6cb0;
  }
  .correct { background-color: #c6f6d5 !important; border-left: 4px solid #38a169; padding: 10px; border-radius: 4px; }
  .wrong   { background-color: #fed7d7 !important; border-left: 4px solid #e53e3e; padding: 10px; border-radius: 4px; }
  .stProgress > div > div { background: linear-gradient(90deg, #667eea, #764ba2); }
  .section-header {
    font-size: 1.4rem; font-weight: 700; color: #2d3748;
    border-bottom: 3px solid #667eea; padding-bottom: 8px; margin: 1.5rem 0 1rem;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────
defaults = {
    "step": "upload",           # upload → quiz → results
    "session_id": None,
    "analysis": None,
    "mcq_answers": {},
    "coding_answers": {},
    "quiz_submitted": False,
    "evaluation": None,
    "current_mcq": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 AI Resume Analyzer")
    st.markdown("**Powered by Local LLM (Ollama)**")
    st.markdown("---")

    try:
        resp = requests.get(f"{API_BASE}/health", timeout=10)
        h = resp.json()
        ollama_ok = h.get("ollama") == "running"
        st.success(f"✅ API: Online" if resp.status_code == 200 else "❌ API: Offline")
        if ollama_ok:
            st.success(f"🦙 Ollama: Running ({h.get('model', 'unknown')})")
        else:
            st.error("❌ Ollama: Not running")
            st.code("ollama serve\nollama pull llama3", language="bash")
    except Exception:
        st.error("❌ Backend not reachable")
        st.code("uvicorn main:app --reload", language="bash")

    st.markdown("---")
    st.markdown("### 📋 Workflow")
    steps = {"upload": "1", "quiz": "2", "results": "3"}
    cur = st.session_state.step
    for step, num in steps.items():
        icon = "✅" if list(steps).index(step) < list(steps).index(cur) else ("🔵" if step == cur else "⚪")
        label = {"upload": "Upload & Analyze", "quiz": "Take Assessment", "results": "View Results"}[step]
        st.markdown(f"{icon} **Step {num}:** {label}")

    st.markdown("---")
    if st.button("🔄 Start Over", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()


# ─────────────────────────────────────────────
# STEP 1 — Upload & Analyze
# ─────────────────────────────────────────────
if st.session_state.step == "upload":
    st.markdown("""
    <div class="main-header">
        <h1>🎯 AI Resume Analyzer</h1>
        <p style="font-size:1.1rem; opacity:0.9;">Upload your Resume & Job Description to get an instant AI-powered assessment</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("### 📄 Your Resume")
        resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"], key="resume_up")
        if resume_file:
            st.success(f"✅ {resume_file.name} ({resume_file.size // 1024} KB)")
    with col2:
        st.markdown("### 💼 Job Description")
        jd_file = st.file_uploader("Upload Job Description (PDF)", type=["pdf"], key="jd_up")
        if jd_file:
            st.success(f"✅ {jd_file.name} ({jd_file.size // 1024} KB)")

    st.markdown("---")
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        analyze_btn = st.button(
            "🚀 Analyze & Generate Assessment",
            use_container_width=True,
            disabled=not (resume_file and jd_file),
            type="primary",
        )

    if analyze_btn and resume_file and jd_file:
        with st.spinner("🤖 AI is analyzing your resume… (this may take 1-3 minutes with local LLM)"):
            progress = st.progress(0)
            status = st.empty()

            status.text("📖 Extracting text from PDFs…")
            progress.progress(10)

            files = {
                "resume": (resume_file.name, resume_file.getvalue(), "application/pdf"),
                "job_description": (jd_file.name, jd_file.getvalue(), "application/pdf"),
            }

            try:
                status.text("🧠 Identifying skills and generating questions…")
                progress.progress(30)

                resp = requests.post(f"{API_BASE}/analyze", files=files, timeout=300)

                if resp.status_code == 200:
                    status.text("✅ Analysis complete!")
                    progress.progress(100)
                    time.sleep(0.5)

                    analysis = resp.json()
                    st.session_state.analysis = analysis
                    st.session_state.session_id = analysis["session_id"]
                    st.session_state.step = "quiz"
                    st.rerun()
                else:
                    st.error(f"❌ Error {resp.status_code}: {resp.json().get('detail', 'Unknown error')}")
            except requests.exceptions.Timeout:
                st.error("⏱ Request timed out. The LLM is taking too long. Try a smaller PDF or a faster model.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure `uvicorn main:app --reload` is running.")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")

    # Feature cards
    st.markdown("---")
    st.markdown("### What you'll get:")
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("🧠", "30 MCQ Questions", "Tailored to your skills and the job requirements"),
        ("💻", "Coding Round", "5 programming problems at your skill level"),
        ("📊", "Detailed Feedback", "Strengths, gaps, and ATS optimization tips"),
        ("🎯", "Match Score", "Percentage match across 5 categories"),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], cards):
        with col:
            st.markdown(f"""
            <div style="background:#f7fafc;border:1px solid #e2e8f0;border-radius:10px;padding:1rem;text-align:center;height:140px">
                <div style="font-size:2rem">{icon}</div>
                <div style="font-weight:700;color:#2d3748;margin:4px 0">{title}</div>
                <div style="font-size:0.85rem;color:#718096">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# STEP 2 — Assessment (MCQ + Coding)
# ─────────────────────────────────────────────
elif st.session_state.step == "quiz":
    analysis = st.session_state.analysis
    mcq_questions = analysis.get("mcq_questions", [])
    coding_questions = analysis.get("coding_questions", [])

    st.markdown("## 📝 Technical Assessment")

    # Tabs
    tab_mcq, tab_coding, tab_preview = st.tabs(["🧠 MCQ Round (30 Qs)", "💻 Coding Round (5 Qs)", "📊 Quick Preview"])

    # ── MCQ Tab ───────────────────────────────
    with tab_mcq:
        st.markdown(f"### Answer all {len(mcq_questions)} questions")
        answered = len(st.session_state.mcq_answers)
        st.progress(answered / max(len(mcq_questions), 1))
        st.caption(f"Answered: {answered}/{len(mcq_questions)}")

        for idx, q in enumerate(mcq_questions):
            with st.expander(
                f"Q{idx+1}. {q['question'][:80]}…" if len(q['question']) > 80 else f"Q{idx+1}. {q['question']}",
                expanded=(idx < 3),
            ):
                badge_color = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(q.get("difficulty", ""), "⚪")
                st.caption(f"{badge_color} {q.get('difficulty','')!s}  |  📌 {q.get('topic','General')}")
                st.markdown(f"**{q['question']}**")

                options = q.get("options", [])
                qid = str(q["id"])
                prev = st.session_state.mcq_answers.get(qid)
                selected = st.radio(
                    "Choose your answer:",
                    options,
                    key=f"mcq_{qid}",
                    index=options.index(prev) if prev in options else None,
                    label_visibility="collapsed",
                )
                if selected:
                    # Extract letter (A/B/C/D) from the option string
                    letter = selected[0].upper() if selected else ""
                    st.session_state.mcq_answers[qid] = letter

    # ── Coding Tab ────────────────────────────
    with tab_coding:
        st.markdown("### Solve the coding problems below")
        st.info("💡 Write working code — the AI will evaluate correctness, complexity, and style.")

        for q in coding_questions:
            with st.expander(f"Problem {q['id']}: {q['title']} [{q.get('difficulty','Medium')}]"):
                diff_color = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(q.get("difficulty", ""), "⚪")
                st.caption(f"{diff_color} {q.get('difficulty','')}  |  📌 {q.get('topic','')}")
                st.markdown(f"**Problem:** {q['description']}")

                if q.get("examples"):
                    st.markdown("**Examples:**")
                    for ex in q["examples"]:
                        st.code(f"Input:  {ex.get('input','')}\nOutput: {ex.get('output','')}", language="text")
                        if ex.get("explanation"):
                            st.caption(f"💬 {ex['explanation']}")

                if q.get("hints"):
                    # with st.expander("💡 Show Hints"):
                    #     for h in q["hints"]:
                    #         st.markdown(f"• {h}")
                    st.markdown("**💡 Hints:**")
                    for h in q.get("hints", []):
                        st.markdown(f"• {h}")

                qid = str(q["id"])
                code = st.text_area(
                    "Your Solution:",
                    value=st.session_state.coding_answers.get(qid, "# Write your solution here\n"),
                    height=220,
                    key=f"code_{qid}",
                )
                st.session_state.coding_answers[qid] = code

    # ── Preview Tab ───────────────────────────
    with tab_preview:
        st.markdown("### 📊 Resume Analysis Preview")
        skills = analysis.get("skills_extracted", [])
        if skills:
            st.markdown("**Skills Identified:**")
            html = "".join(f'<span class="skill-tag">{s}</span>' for s in skills)
            st.markdown(f'<div style="line-height:2.2">{html}</div>', unsafe_allow_html=True)
            st.markdown("---")

        ms = analysis.get("match_score", {})
        if ms:
            st.markdown("**Job Match Preview:**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Overall Match", f"{ms.get('overall_score', 0)}%")
            c2.metric("Recommendation", ms.get("recommendation", "—"))
            c3.metric("Hiring Probability", ms.get("hiring_probability", "—"))

    # ── Submit button ─────────────────────────
    st.markdown("---")
    mcq_done = len(st.session_state.mcq_answers)
    code_done = sum(1 for v in st.session_state.coding_answers.values() if v.strip() and v.strip() != "# Write your solution here")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.session_state.quiz_submitted:
            if st.button("📤 Submit Assessment", use_container_width=True, type="primary"):
                with st.spinner("🔍 AI is evaluating your answers…"):
                    payload = {
                        "session_id": st.session_state.session_id,
                        "mcq_answers": st.session_state.mcq_answers,
                        "coding_answers": st.session_state.coding_answers,
                    }
                    try:
                        resp = requests.post(f"{API_BASE}/submit-answers", json=payload, timeout=600)
                        if resp.status_code == 200:
                            st.session_state.evaluation = resp.json()
                            st.session_state.quiz_submitted = True
                            st.session_state.step = "results"
                            st.rerun()
                        else:
                            st.error(f"Submission failed: {resp.json().get('detail')}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.caption(f"📊 Progress: {mcq_done}/30 MCQ answered | {code_done}/5 coding problems attempted")


# ─────────────────────────────────────────────
# STEP 3 — Results
# ─────────────────────────────────────────────
elif st.session_state.step == "results":
    analysis = st.session_state.analysis
    evaluation = st.session_state.evaluation
    feedback = analysis.get("feedback", {})
    match_score = analysis.get("match_score", {})

    st.markdown("## 🏆 Your Assessment Results")

    # ── Score banner ──────────────────────────
    if evaluation:
        cs = evaluation.get("combined_score", 0)
        grade = evaluation.get("grade", "")
        mcq_pct = evaluation.get("mcq", {}).get("percentage", 0)
        code_pct = evaluation.get("coding", {}).get("percentage", 0)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🎯 Combined Score", f"{cs}%")
        c2.metric("🧠 MCQ Score", f"{mcq_pct}%")
        c3.metric("💻 Coding Score", f"{code_pct}%")
        c4.metric("📊 Job Match", f"{match_score.get('overall_score', 0)}%")

        grade_color = "#38a169" if cs >= 70 else "#d69e2e" if cs >= 50 else "#e53e3e"
        st.markdown(f"""
        <div style="background:{grade_color};color:white;padding:1rem;border-radius:10px;text-align:center;font-size:1.3rem;font-weight:700;margin:1rem 0">
            {grade}
        </div>
        """, unsafe_allow_html=True)

        perf_summary = evaluation.get("performance_summary", "")
        if perf_summary:
            st.info(perf_summary)

    result_tabs = st.tabs(["🧠 MCQ Review", "💻 Coding Review", "📋 Feedback", "🎯 Match Score"])

    # ── MCQ Review ────────────────────────────
    with result_tabs[0]:
        if evaluation:
            mcq_data = evaluation.get("mcq", {})
            sc, tot = mcq_data.get("score", 0), mcq_data.get("total", 30)
            st.markdown(f"### Score: {sc}/{tot} ({mcq_data.get('percentage',0)}%)")
            st.progress(sc / max(tot, 1))

            # Topic breakdown
            tb = mcq_data.get("topic_breakdown", {})
            if tb:
                st.markdown("**Performance by Topic:**")
                for topic, stats in tb.items():
                    col1, col2 = st.columns([3, 1])
                    col1.markdown(f"📌 **{topic}**")
                    col1.progress(stats["percentage"] / 100)
                    col2.markdown(f"**{stats['correct']}/{stats['total']}**")

            st.markdown("---")
            show_wrong = st.checkbox("Show only wrong answers")
            for r in mcq_data.get("results", []):
                if show_wrong and r["is_correct"]:
                    continue
                css_class = "correct" if r["is_correct"] else "wrong"
                icon = "✅" if r["is_correct"] else "❌"
                with st.expander(f"{icon} Q{r['id']}: {r['question'][:70]}…"):
                    st.markdown(f"**Your answer:** {r['user_answer']}  |  **Correct:** {r['correct_answer']}")
                    st.markdown(f"💡 {r.get('explanation', '')}")

    # ── Coding Review ─────────────────────────
    with result_tabs[1]:
        if evaluation:
            code_data = evaluation.get("coding", {})
            st.markdown(f"### Score: {code_data.get('score',0)}/{code_data.get('max_score',50)} ({code_data.get('percentage',0)}%)")

            for r in code_data.get("results", []):
                score = r.get("score", 0)
                color = "🟢" if score >= 7 else "🟡" if score >= 4 else "🔴"
                with st.expander(f"{color} Problem {r['id']}: {r['title']} — {score}/10"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Score", f"{score}/10")
                    c2.metric("Time Complexity", r.get("time_complexity", "N/A"))
                    c3.metric("Space Complexity", r.get("space_complexity", "N/A"))

                    st.markdown(f"**Feedback:** {r.get('feedback', '')}")
                    st.markdown(f"**Code Quality:** {r.get('code_quality', 'N/A')}")
                    st.markdown(f"**Correctness:** {'✅ Yes' if r.get('correctness') else '❌ No'}")

                    suggestions = r.get("suggestions", [])
                    if suggestions:
                        st.markdown("**Suggestions for improvement:**")
                        for s in suggestions:
                            st.markdown(f"• {s}")

                    # Show sample solution
                    for cq in analysis.get("coding_questions", []):
                        if str(cq["id"]) == str(r["id"]) and cq.get("sample_solution"):
                            with st.expander("📖 View Sample Solution"):
                                st.code(cq["sample_solution"], language="python")
                            break

    # ── Detailed Feedback ─────────────────────
    with result_tabs[2]:
        st.markdown("### 📋 Personalized Feedback")

        if feedback.get("overall_assessment"):
            st.info(f"**Overall Assessment:** {feedback['overall_assessment']}")

        c1, c2 = st.columns(2)
        with c1:
            if feedback.get("strengths"):
                st.markdown("#### ✅ Strengths")
                for s in feedback["strengths"]:
                    st.markdown(f"• {s}")

            if feedback.get("missing_skills"):
                st.markdown("#### ❗ Missing Skills")
                for s in feedback["missing_skills"]:
                    st.markdown(f"• {s}")

            if feedback.get("ats_tips"):
                st.markdown("#### 🤖 ATS Optimization Tips")
                for t in feedback["ats_tips"]:
                    st.markdown(f"• {t}")

        with c2:
            if feedback.get("weaknesses"):
                st.markdown("#### ⚠️ Areas to Improve")
                for w in feedback["weaknesses"]:
                    st.markdown(f"• {w}")

            if feedback.get("recommendations"):
                st.markdown("#### 💡 Recommendations")
                for r in feedback["recommendations"]:
                    st.markdown(f"• {r}")

            if feedback.get("interview_preparation"):
                st.markdown("#### 🎤 Interview Preparation")
                for p in feedback["interview_preparation"]:
                    st.markdown(f"• {p}")

        if feedback.get("experience_gap"):
            st.markdown("#### 📈 Experience Gap Analysis")
            st.warning(feedback["experience_gap"])

        if feedback.get("keyword_optimization"):
            st.markdown("#### 🔑 Keywords to Add to Resume")
            html = "".join(f'<span class="skill-tag">{k}</span>' for k in feedback["keyword_optimization"])
            st.markdown(f'<div style="line-height:2.2">{html}</div>', unsafe_allow_html=True)

    # ── Match Score ───────────────────────────
    with result_tabs[3]:
        st.markdown("### 🎯 Resume vs Job Description Match")

        overall = match_score.get("overall_score", 0)
        col1, col2 = st.columns([1, 2])
        with col1:
            gauge_color = "#38a169" if overall >= 70 else "#d69e2e" if overall >= 50 else "#e53e3e"
            st.markdown(f"""
            <div style="background:{gauge_color};color:white;border-radius:50%;width:140px;height:140px;
                        display:flex;flex-direction:column;align-items:center;justify-content:center;
                        font-size:2.2rem;font-weight:700;margin:auto">
                {overall}%
                <div style="font-size:0.7rem;font-weight:400">Overall Match</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style="text-align:center;margin-top:1rem">
                <b>{match_score.get('recommendation','')}</b><br>
                Hiring Probability: <b>{match_score.get('hiring_probability','')}</b>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            categories = {
                "skill_match": "🛠 Skill Match",
                "experience_match": "📅 Experience",
                "education_match": "🎓 Education",
                "keyword_density": "🔑 Keywords",
                "cultural_fit": "🤝 Cultural Fit",
            }
            for key, label in categories.items():
                cat = match_score.get(key, {})
                score = cat.get("score", 0) if isinstance(cat, dict) else 0
                st.markdown(f"**{label}:** {score}%")
                st.progress(score / 100)
                if isinstance(cat, dict) and cat.get("reasoning"):
                    st.caption(cat["reasoning"])

        if match_score.get("summary"):
            st.markdown("---")
            st.markdown(f"**Summary:** {match_score['summary']}")

        # Matched skills
        sm = match_score.get("skill_match", {})
        if isinstance(sm, dict):
            c1, c2 = st.columns(2)
            with c1:
                if sm.get("matched_skills"):
                    st.markdown("**✅ Matched Skills:**")
                    for s in sm["matched_skills"]:
                        st.markdown(f"• {s}")
            with c2:
                if sm.get("missing_skills"):
                    st.markdown("**❌ Missing Skills:**")
                    for s in sm["missing_skills"]:
                        st.markdown(f"• {s}")

    # ── Download report ───────────────────────
    st.markdown("---")
    report = {
        "session_id": st.session_state.session_id,
        "skills_extracted": analysis.get("skills_extracted", []),
        "match_score": match_score,
        "feedback": feedback,
        "evaluation": evaluation,
    }
    st.download_button(
        "⬇️ Download Full Report (JSON)",
        data=json.dumps(report, indent=2),
        file_name="resume_analysis_report.json",
        mime="application/json",
    )