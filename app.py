# app.py — Streamlit frontend for Scholaris

import streamlit as st   
import requests          

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Scholaris — Academic AI",
    page_icon="🎓",
    layout="centered",
)

# ── Custom CSS — professional dark-academic aesthetic ─────────────────────────
st.markdown("""
<style>
  /* Import refined serif + mono pairing */
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Source+Sans+3:wght@300;400;600&family=JetBrains+Mono:wght@400&display=swap');

  /* Global reset */
  html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
    background-color: #0e0f14;
    color: #d6cfc4;
  }

  /* Hide default Streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }

  /* Hero title */
  .hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: #e8dfd0;
    letter-spacing: 0.03em;
    margin-bottom: 0.1rem;
    text-align: center;
  }
  .hero-sub {
    text-align: center;
    font-size: 0.9rem;
    color: #8a8070;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 2.2rem;
  }

  /* Scope badge row */
  .badge-row {
    display: flex;
    justify-content: center;
    gap: 0.6rem;
    margin-bottom: 2rem;
  }
  .badge {
    padding: 0.3rem 0.85rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .badge-math    { background: #1c2b3a; color: #6ab0f5; border: 1px solid #2a4a6a; }
  .badge-bio     { background: #1a2e1a; color: #72c472; border: 1px solid #2a4a2a; }
  .badge-history { background: #2e1f0e; color: #d4935a; border: 1px solid #5a3a1a; }

  /* Text area */
  textarea {
    background-color: #161820 !important;
    color: #d6cfc4 !important;
    border: 1px solid #2e2d3a !important;
    border-radius: 6px !important;
    font-family: 'Source Sans 3', sans-serif !important;
    font-size: 0.95rem !important;
  }
  textarea:focus { border-color: #c9a96e !important; box-shadow: none !important; }

  /* Submit button */
  div.stButton > button {
    width: 100%;
    background: #c9a96e;
    color: #0e0f14;
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border: none;
    padding: 0.65rem 0;
    border-radius: 5px;
    transition: background 0.2s;
  }
  div.stButton > button:hover { background: #e0c080; }

  /* Result card */
  .result-card {
    background: #161820;
    border: 1px solid #2e2d3a;
    border-left: 3px solid #c9a96e;
    border-radius: 6px;
    padding: 1.4rem 1.6rem;
    margin-top: 1.4rem;
  }
  .result-agent {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
  }
  .agent-math    { color: #6ab0f5; }
  .agent-biology { color: #72c472; }
  .agent-history { color: #d4935a; }
  .agent-oos     { color: #e07070; }

  .result-text {
    font-size: 0.97rem;
    line-height: 1.75;
    color: #cdc6bc;
    font-family: 'Source Sans 3', sans-serif;
    white-space: pre-wrap;   /* preserve line breaks in step-by-step answers */
  }

  /* Error card */
  .error-card {
    background: #1e1014;
    border: 1px solid #4a2020;
    border-left: 3px solid #e07070;
    border-radius: 6px;
    padding: 1.2rem 1.6rem;
    margin-top: 1.4rem;
    color: #e07070;
    font-size: 0.93rem;
  }

  /* Divider */
  hr { border-color: #2e2d3a; margin: 1.8rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Backend URL ───────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000/query"   # FastAPI endpoint

# ── Agent label map ───────────────────────────────────────────────────────────
# Maps internal agent names to display-friendly labels and CSS classes
AGENT_LABELS = {
    "math_agent":    ("∑ Math Agent",    "agent-math"),
    "biology_agent": ("🧬 Biology Agent", "agent-biology"),
    "history_agent": ("📜 History Agent", "agent-history"),
    "out_of_scope":  ("⛔ Out of Scope",  "agent-oos"),
    "supervisor":    ("🤖 Supervisor",    "agent-math"),
}

# ── UI Layout ─────────────────────────────────────────────────────────────────

st.markdown('<div class="hero-title">SCHOLARIS</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Intelligent Academic Q&amp;A · Powered by AI Agents</div>', unsafe_allow_html=True)

# Subject scope badges
st.markdown("""
<div class="badge-row">
  <span class="badge badge-math">∑ Mathematics</span>
  <span class="badge badge-bio">🧬 Biology</span>
  <span class="badge badge-history">📜 History</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# Query input — max_chars mirrors the guardrail cap
query = st.text_area(
    label="Your question",
    placeholder="e.g.  What is the derivative of x³ + 2x?   |   Explain how mitosis works.   |   Who was Napoleon Bonaparte?",
    max_chars=500,           
    height=120,
    label_visibility="collapsed",
)

# Submit button
submitted = st.button("Ask Scholaris →")

# ── Query handling ────────────────────────────────────────────────────────────
if submitted:
    if not query.strip():
        
        st.warning("Please enter a question before submitting.")
    else:
        with st.spinner("Routing query to the right expert…"):
            try:
               
                response = requests.post(
                    API_URL,
                    json={"query": query.strip()},
                    timeout=60,   
                )

                if response.status_code == 200:
                    
                    data = response.json()
                    agent_key   = data.get("agent", "supervisor")
                    answer_text = data.get("answer", "No answer returned.")

                    
                    label, css_class = AGENT_LABELS.get(agent_key, ("AI Agent", "agent-math"))

                    
                    st.markdown(f"""
                    <div class="result-card">
                      <div class="result-agent {css_class}">{label}</div>
                      <div class="result-text">{answer_text}</div>
                    </div>
                    """, unsafe_allow_html=True)

                elif response.status_code == 400:
                    
                    detail = response.json().get("detail", "Query was rejected.")
                    st.markdown(f'<div class="error-card">🚫 {detail}</div>', unsafe_allow_html=True)

                else:
                    
                    st.markdown('<div class="error-card">⚠️ An unexpected server error occurred. Please try again.</div>', unsafe_allow_html=True)

            except requests.exceptions.ConnectionError:
                
                st.markdown(
                    '<div class="error-card">🔌 Cannot connect to the Scholaris API. '
                    'Make sure the backend is running:<br><code>uvicorn main:app --reload</code></div>',
                    unsafe_allow_html=True,
                )
            except requests.exceptions.Timeout:
                st.markdown('<div class="error-card">⏱️ Request timed out. The model may be under load — please retry.</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    '<p style="text-align:center;font-size:0.75rem;color:#4a4540;letter-spacing:0.08em;">'
    'SCHOLARIS · Math · Biology · History · Powered by LangGraph + GPT-4o-mini'
    '</p>',
    unsafe_allow_html=True,
)
