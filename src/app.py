import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import streamlit as st
from reasoner import Reasoner
st.set_page_config(page_title="Policy Proof",page_icon="📚",layout="wide")
st.title("📚 Policy Proof")
st.caption("Evidence-grounded university policy QA: answered, not covered, or contradiction.")
if "reasoner" not in st.session_state: st.session_state.reasoner=Reasoner()
q=st.text_input("Ask a question about the university policies",placeholder="e.g. Can the committee waive laboratory attendance?")
if st.button("Check policy",type="primary") and q.strip():
    with st.spinner("Retrieving policy evidence…"): result=st.session_state.reasoner.ask(q.strip())
    labels={"answers":"🟢 ANSWERED","silent":"⚪ NOT COVERED","contradiction":"🔴 CONTRADICTION DETECTED"}
    st.subheader(labels[result.state]); st.write(result.answer)
    if result.state=="contradiction": st.warning("The documents contain incompatible provisions. The system is showing both instead of inventing a reconciliation.")
    if result.citations:
        st.markdown("### Evidence")
        for e in result.evidence:
            if e["chunk_id"] in result.citations:
                with st.expander(f"📄 {e['location']}"):
                    st.write(e["text"])
                    st.caption(f"Citation: `{e['chunk_id']}`")
    elif result.state=="silent": st.info("No policy citation is shown because the corpus does not establish the requested fact.")
