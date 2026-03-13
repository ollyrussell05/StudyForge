import streamlit as st
import anthropic
import json
import re

st.set_page_config(page_title="StudyForge", page_icon="✦", layout="centered")

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=DM+Mono:wght@300;400&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

.stApp { background-color: #0a0a0f; color: #e8e8f0; }

.logo { font-family: 'DM Mono', monospace; font-size: 13px; letter-spacing: 0.2em;
        text-transform: uppercase; color: #c8f060; margin-bottom: 4px; }

h1 { font-size: 2.6rem !important; font-weight: 800 !important;
     letter-spacing: -0.02em !important; line-height: 1.1 !important; }

.tagline { font-family: 'DM Mono', monospace; font-size: 13px;
           color: #6a6a80; margin-top: 4px; margin-bottom: 32px; }

.stTextArea textarea {
    background: #13131a !important; border: 1px solid #2a2a3a !important;
    color: #e8e8f0 !important; font-family: 'DM Mono', monospace !important;
    font-size: 13px !important; border-radius: 10px !important; }

.stButton > button {
    background: #c8f060 !important; color: #0a0a0f !important;
    font-family: 'Syne', sans-serif !important; font-weight: 800 !important;
    font-size: 15px !important; letter-spacing: 0.05em !important;
    border: none !important; border-radius: 10px !important;
    padding: 14px 32px !important; width: 100% !important; }

.stButton > button:hover { background: #d8ff70 !important; }

.card-box {
    background: #13131a; border: 1px solid #2a2a3a; border-radius: 14px;
    padding: 28px 32px; margin-bottom: 16px; }

.card-box.answer { border-color: #c8f060; background: #1c1c26; }

.badge { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.15em;
         text-transform: uppercase; color: #6a6a80; margin-bottom: 10px; }

.badge.q { color: #60a0f0; }
.badge.a { color: #c8f060; }

.card-text { font-size: 17px; font-weight: 600; line-height: 1.5; }

.opt-btn > button {
    background: #1c1c26 !important; border: 1px solid #2a2a3a !important;
    color: #e8e8f0 !important; font-family: 'Syne', sans-serif !important;
    font-size: 14px !important; font-weight: 500 !important;
    border-radius: 8px !important; text-align: left !important;
    width: 100% !important; padding: 12px 18px !important; }

.correct-ans { background: rgba(96,240,160,0.1); border: 1px solid #60f0a0;
               border-radius: 8px; padding: 12px 18px; color: #60f0a0;
               font-weight: 600; margin-bottom: 8px; }

.wrong-ans { background: rgba(240,96,96,0.1); border: 1px solid #f06060;
             border-radius: 8px; padding: 12px 18px; color: #f06060;
             font-weight: 600; margin-bottom: 8px; }

.explanation { background: rgba(200,240,96,0.06); border-left: 3px solid #c8f060;
               border-radius: 0 8px 8px 0; padding: 12px 16px; margin-top: 12px;
               font-family: 'DM Mono', monospace; font-size: 13px;
               color: #9a9ab0; line-height: 1.6; }

.score-box { background: #13131a; border: 1px solid #c8f060; border-radius: 14px;
             padding: 40px; text-align: center; margin-top: 32px; }

.score-big { font-size: 72px; font-weight: 800; color: #c8f060; line-height: 1; }
.score-sub { font-family: 'DM Mono', monospace; font-size: 13px;
             color: #6a6a80; margin-top: 8px; }

.divider { border: none; border-top: 1px solid #2a2a3a; margin: 32px 0; }
</style>
""", unsafe_allow_html=True)


# ── API client ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


# ── Generation ────────────────────────────────────────────────────────────────
def generate_study_set(notes: str, fc_count: int, quiz_count: int) -> dict:
    client = get_client()
    prompt = f"""You are a study assistant. Given the following lecture notes, generate exactly {fc_count} flashcards and exactly {quiz_count} multiple-choice quiz questions.

Return ONLY a JSON object in this exact format with NO other text:
{{
  "flashcards": [
    {{ "question": "...", "answer": "..." }}
  ],
  "quiz": [
    {{
      "question": "...",
      "options": ["A: ...", "B: ...", "C: ...", "D: ..."],
      "correct": 0,
      "explanation": "..."
    }}
  ]
}}

Rules:
- Flashcards should cover key concepts, definitions, and facts
- Quiz questions should be clear multiple choice with 4 options (correct is index 0-3)
- Keep questions concise and academically rigorous
- Explanations should clarify why the answer is correct
- Return ONLY valid JSON, no markdown, no backticks

LECTURE NOTES:
{notes[:6000]}"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    clean = re.sub(r"```json|```", "", raw).strip()
    return json.loads(clean)


# ── Session state defaults ────────────────────────────────────────────────────
for key, default in [
    ("study_set", None),
    ("fc_index", 0),
    ("fc_flipped", False),
    ("quiz_answers", {}),
    ("quiz_done", False),
    ("view", "upload"),        # upload | results
    ("tab", "flashcards"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<div class="logo">✦ StudyForge</div>', unsafe_allow_html=True)
st.markdown("# Turn your notes into a **study arsenal.**")
st.markdown('<div class="tagline">// paste notes → flashcards + quiz in seconds</div>', unsafe_allow_html=True)
st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD VIEW
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.view == "upload":
    notes = st.text_area(
        "Lecture notes",
        height=300,
        placeholder="Paste your lecture notes, slides, or any study material here...\n\nThe more content you give it, the better your flashcards and quiz will be.",
        label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)
    with col1:
        fc_count = st.select_slider("Flashcards", options=[5, 10, 15], value=10)
    with col2:
        quiz_count = st.select_slider("Quiz questions", options=[5, 8, 12], value=8)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Generate Study Set →"):
        if not notes or len(notes.strip()) < 50:
            st.error("Please paste some lecture notes first (at least a paragraph or two).")
        else:
            with st.spinner("Generating your study set..."):
                try:
                    result = generate_study_set(notes, fc_count, quiz_count)
                    st.session_state.study_set = result
                    st.session_state.fc_index = 0
                    st.session_state.fc_flipped = False
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_done = False
                    st.session_state.view = "results"
                    st.session_state.tab = "flashcards"
                    st.rerun()
                except Exception as e:
                    st.error(f"Something went wrong: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# RESULTS VIEW
# ══════════════════════════════════════════════════════════════════════════════
else:
    data = st.session_state.study_set
    flashcards = data.get("flashcards", [])
    quiz = data.get("quiz", [])

    # Stats row
    c1, c2, c3 = st.columns(3)
    c1.metric("Flashcards", len(flashcards))
    c2.metric("Quiz questions", len(quiz))
    answered = len(st.session_state.quiz_answers)
    c3.metric("Quiz progress", f"{answered}/{len(quiz)}")

    if st.button("← New notes"):
        st.session_state.view = "upload"
        st.session_state.study_set = None
        st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Tabs
    tab1, tab2 = st.tabs(["✦ Flashcards", "✎ Quiz"])

    # ── FLASHCARDS TAB ────────────────────────────────────────────────────────
    with tab1:
        if not flashcards:
            st.warning("No flashcards generated.")
        else:
            idx = st.session_state.fc_index
            card = flashcards[idx]

            st.markdown(f"**Card {idx + 1} of {len(flashcards)}**")
            st.progress((idx + 1) / len(flashcards))
            st.markdown("<br>", unsafe_allow_html=True)

            # Question
            st.markdown(f"""
            <div class="card-box">
                <div class="badge q">Question</div>
                <div class="card-text">{card['question']}</div>
            </div>""", unsafe_allow_html=True)

            # Reveal / hide answer
            flip_label = "Hide answer ↑" if st.session_state.fc_flipped else "Reveal answer ↓"
            if st.button(flip_label, key="flip"):
                st.session_state.fc_flipped = not st.session_state.fc_flipped
                st.rerun()

            if st.session_state.fc_flipped:
                st.markdown(f"""
                <div class="card-box answer">
                    <div class="badge a">Answer</div>
                    <div class="card-text">{card['answer']}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            prev_col, _, next_col = st.columns([1, 2, 1])
            with prev_col:
                if st.button("← Prev", disabled=idx == 0, key="prev"):
                    st.session_state.fc_index -= 1
                    st.session_state.fc_flipped = False
                    st.rerun()
            with next_col:
                if st.button("Next →", disabled=idx == len(flashcards) - 1, key="next"):
                    st.session_state.fc_index += 1
                    st.session_state.fc_flipped = False
                    st.rerun()

    # ── QUIZ TAB ──────────────────────────────────────────────────────────────
    with tab2:
        if not quiz:
            st.warning("No quiz questions generated.")
        else:
            for qi, q in enumerate(quiz):
                st.markdown(f"**Q{qi + 1}.** {q['question']}")

                answered_this = qi in st.session_state.quiz_answers

                if not answered_this:
                    for oi, opt in enumerate(q["options"]):
                        if st.button(opt, key=f"q{qi}_o{oi}"):
                            st.session_state.quiz_answers[qi] = oi
                            if len(st.session_state.quiz_answers) == len(quiz):
                                st.session_state.quiz_done = True
                            st.rerun()
                else:
                    chosen = st.session_state.quiz_answers[qi]
                    for oi, opt in enumerate(q["options"]):
                        if oi == q["correct"]:
                            st.markdown(f'<div class="correct-ans">✓ {opt}</div>', unsafe_allow_html=True)
                        elif oi == chosen and chosen != q["correct"]:
                            st.markdown(f'<div class="wrong-ans">✗ {opt}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='padding: 10px 18px; color: #6a6a80;'>{opt}</div>", unsafe_allow_html=True)

                    if q.get("explanation"):
                        st.markdown(f'<div class="explanation">💡 {q["explanation"]}</div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

            # Score
            if st.session_state.quiz_done:
                correct = sum(
                    1 for qi, chosen in st.session_state.quiz_answers.items()
                    if chosen == quiz[qi]["correct"]
                )
                pct = round((correct / len(quiz)) * 100)
                st.markdown(f"""
                <div class="score-box">
                    <div class="score-big">{pct}%</div>
                    <div class="score-sub">{correct} / {len(quiz)} correct</div>
                </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Retry Quiz"):
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_done = False
                    st.rerun()