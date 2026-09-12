import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from reasoner import Reasoner


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Policy Proof",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        /* ---------- GLOBAL ---------- */
        .stApp {
            background:
                radial-gradient(circle at 15% 10%, rgba(37, 99, 235, 0.12), transparent 28%),
                radial-gradient(circle at 85% 20%, rgba(14, 165, 233, 0.08), transparent 25%),
                #07111f;
            color: #e5edf7;
        }

        .main .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        /* ---------- SIDEBAR ---------- */
        section[data-testid="stSidebar"] {
            background: #050d18;
            border-right: 1px solid rgba(148, 163, 184, 0.12);
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 2rem;
        }

        .sidebar-brand {
            padding: 14px 4px 24px 4px;
        }

        .sidebar-brand h2 {
            margin: 0;
            color: #f8fafc;
            font-size: 1.45rem;
            font-weight: 700;
        }

        .sidebar-brand p {
            margin-top: 6px;
            color: #8fa3bb;
            font-size: 0.85rem;
        }

        .sidebar-card {
            background: rgba(15, 27, 44, 0.75);
            border: 1px solid rgba(96, 165, 250, 0.12);
            border-radius: 14px;
            padding: 15px;
            margin: 12px 0;
        }

        .sidebar-label {
            color: #7f93aa;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 5px;
        }

        .sidebar-value {
            color: #dbeafe;
            font-size: 0.92rem;
            font-weight: 600;
        }

        /* ---------- HERO ---------- */
        .hero {
            padding: 28px 32px;
            border-radius: 22px;
            background:
                linear-gradient(
                    135deg,
                    rgba(15, 39, 70, 0.96),
                    rgba(8, 23, 41, 0.92)
                );
            border: 1px solid rgba(96, 165, 250, 0.18);
            box-shadow: 0 20px 55px rgba(0, 0, 0, 0.25);
            margin-bottom: 25px;
        }

        .hero-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 999px;
            background: rgba(37, 99, 235, 0.15);
            border: 1px solid rgba(96, 165, 250, 0.2);
            color: #93c5fd;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .hero h1 {
            font-size: 2.55rem;
            line-height: 1.1;
            margin: 0;
            color: #f8fafc;
            letter-spacing: -0.03em;
        }

        .hero p {
            margin: 12px 0 0 0;
            color: #9fb1c6;
            font-size: 1rem;
            max-width: 760px;
            line-height: 1.6;
        }

        /* ---------- INPUT ---------- */
        div[data-testid="stTextInput"] input {
            background: rgba(9, 22, 38, 0.95);
            border: 1px solid rgba(100, 116, 139, 0.35);
            border-radius: 13px;
            color: #f8fafc;
            padding: 15px;
            font-size: 1rem;
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.35);
        }

        /* ---------- BUTTON ---------- */
        div.stButton > button {
            border-radius: 12px;
            border: 1px solid rgba(96, 165, 250, 0.25);
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            font-weight: 700;
            min-height: 45px;
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.2);
            transition: all 0.2s ease;
        }

        div.stButton > button:hover {
            border-color: #60a5fa;
            transform: translateY(-1px);
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.3);
        }

        /* ---------- STATUS CARDS ---------- */
        .status-card {
            border-radius: 16px;
            padding: 18px 20px;
            margin: 18px 0;
            border: 1px solid;
        }

        .status-answered {
            background: rgba(22, 101, 52, 0.13);
            border-color: rgba(74, 222, 128, 0.25);
        }

        .status-silent {
            background: rgba(100, 116, 139, 0.12);
            border-color: rgba(148, 163, 184, 0.2);
        }

        .status-contradiction {
            background: rgba(127, 29, 29, 0.16);
            border-color: rgba(248, 113, 113, 0.3);
        }

        .status-title {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 800;
            margin-bottom: 6px;
        }

        .status-answer {
            color: #e5edf7;
            font-size: 1.05rem;
            line-height: 1.65;
        }

        /* ---------- EVIDENCE ---------- */
        .section-title {
            color: #f1f5f9;
            font-size: 1.15rem;
            font-weight: 750;
            margin: 28px 0 12px 0;
        }

        .evidence-card {
            background: rgba(12, 27, 45, 0.72);
            border: 1px solid rgba(96, 165, 250, 0.12);
            border-radius: 14px;
            padding: 16px;
            margin: 10px 0;
        }

        .evidence-location {
            color: #93c5fd;
            font-weight: 700;
            font-size: 0.88rem;
            margin-bottom: 8px;
        }

        .evidence-text {
            color: #cbd5e1;
            line-height: 1.6;
            font-size: 0.91rem;
        }

        .citation {
            display: inline-block;
            margin-top: 10px;
            padding: 4px 8px;
            border-radius: 6px;
            background: rgba(37, 99, 235, 0.12);
            color: #93c5fd;
            font-family: monospace;
            font-size: 0.72rem;
        }

        /* ---------- EMPTY STATE ---------- */
        .empty-state {
            text-align: center;
            padding: 55px 20px;
            margin-top: 20px;
            border-radius: 18px;
            border: 1px dashed rgba(100, 116, 139, 0.25);
            background: rgba(8, 20, 34, 0.45);
        }

        .empty-icon {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }

        .empty-title {
            color: #e2e8f0;
            font-size: 1.15rem;
            font-weight: 700;
        }

        .empty-text {
            color: #7f93aa;
            max-width: 600px;
            margin: 8px auto 0 auto;
            line-height: 1.6;
        }

        /* ---------- FOOTER ---------- */
        .footer {
            margin-top: 55px;
            padding-top: 18px;
            border-top: 1px solid rgba(148, 163, 184, 0.1);
            color: #64748b;
            text-align: center;
            font-size: 0.75rem;
        }

        /* ---------- HIDE STREAMLIT BRANDING ---------- */
        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        header {
            background: transparent !important;
        }

        /* ---------- MOBILE ---------- */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem;
            }

            .hero {
                padding: 22px;
            }

            .hero h1 {
                font-size: 2rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <h2>📚 Policy Proof</h2>
            <p>Evidence-grounded policy intelligence</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-label">System</div>
            <div class="sidebar-value">● Online</div>
        </div>

        <div class="sidebar-card">
            <div class="sidebar-label">Knowledge Retrieval</div>
            <div class="sidebar-value">ChromaDB</div>
        </div>

        <div class="sidebar-card">
            <div class="sidebar-label">Embeddings</div>
            <div class="sidebar-value">all-MiniLM-L6-v2</div>
        </div>

        <div class="sidebar-card">
            <div class="sidebar-label">LLM</div>
            <div class="sidebar-value">Groq · GPT-OSS 120B</div>
        </div>

        <div class="sidebar-card">
            <div class="sidebar-label">Response Policy</div>
            <div class="sidebar-value">Evidence first · No guessing</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            margin-top: 25px;
            color: #64748b;
            font-size: 0.72rem;
            line-height: 1.6;
        ">
        Policy Proof classifies policy questions into three outcomes:
        <br><br>
        🟢 Answered<br>
        ⚪ Not Covered<br>
        🔴 Contradiction
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# HERO
# ---------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">Policy Intelligence System</div>
        <h1>Ask the rulebook.<br>Get evidence, not guesses.</h1>
        <p>
            Policy Proof retrieves relevant university regulations and determines
            whether the requested information is supported, absent from the corpus,
            or contradicted by multiple provisions.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# REASONER
# ---------------------------------------------------------
if "reasoner" not in st.session_state:
    st.session_state.reasoner = Reasoner()


# ---------------------------------------------------------
# QUERY AREA
# ---------------------------------------------------------
st.markdown(
    '<div class="section-title">Ask a policy question</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns([5, 1])

with col1:
    q = st.text_input(
        "Policy question",
        placeholder="e.g. Can the committee waive laboratory attendance?",
        label_visibility="collapsed",
    )

with col2:
    check_policy = st.button(
        "Check Policy",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------
# EMPTY STATE
# ---------------------------------------------------------
if not q.strip() and not check_policy:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">🔎</div>
            <div class="empty-title">Ready to verify a policy</div>
            <div class="empty-text">
                Ask about attendance, examinations, fees, hostel rules,
                academic procedures, eligibility, or other provisions
                contained in the policy corpus.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# QUERY EXECUTION
# ---------------------------------------------------------
if check_policy and q.strip():

    with st.spinner("Retrieving policy evidence…"):
        result = st.session_state.reasoner.ask(q.strip())

    # ---------------------------------------------
    # STATUS
    # ---------------------------------------------
    if result.state == "answers":
        st.markdown(
            f"""
            <div class="status-card status-answered">
                <div class="status-title">🟢 Answered</div>
                <div class="status-answer">{result.answer}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif result.state == "silent":
        st.markdown(
            f"""
            <div class="status-card status-silent">
                <div class="status-title">⚪ Not Covered</div>
                <div class="status-answer">{result.answer}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.info(
            "No policy citation is shown because the corpus does not "
            "establish the requested fact."
        )

    elif result.state == "contradiction":
        st.markdown(
            f"""
            <div class="status-card status-contradiction">
                <div class="status-title">🔴 Contradiction Detected</div>
                <div class="status-answer">{result.answer}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.warning(
            "The documents contain incompatible provisions. "
            "Policy Proof shows the conflicting evidence instead of "
            "inventing a reconciliation."
        )

    # ---------------------------------------------
    # EVIDENCE
    # ---------------------------------------------
    if result.citations:

       st.markdown("### 📑 Evidence")

       for e in result.evidence:

             if e["chunk_id"] in result.citations:

                st.markdown(f"**📄 {e['location']}**")
                st.write(e["text"])
                st.caption(f"Citation: `{e['chunk_id']}`")

                st.divider()

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown(
    """
    <div class="footer">
        Policy Proof · Evidence-grounded university policy QA
        · Retrieval + citation validation · No unsupported claims
    </div>
    """,
    unsafe_allow_html=True,
)