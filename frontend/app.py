import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Medical FAQ (Token-Efficient)", page_icon="💬", layout="centered")
st.title("Token-Efficient Medical FAQ")
st.caption("Informational only. Not a diagnosis or treatment.")

with st.form("ask_form"):
    query = st.text_input(
        "Ask a general medical question (non-diagnostic):",
        placeholder="e.g., What could cause a mild sore throat?",
    )
    submitted = st.form_submit_button("Ask")

if submitted:
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Retrieving and generating..."):
            try:
                resp = requests.post(f"{BACKEND_URL}/ask", json={"query": query}, timeout=60)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                st.error(f"Error contacting backend: {e}")
                st.stop()

        st.subheader("Answer")
        st.write(data.get("answer", ""))

        st.subheader("Verification")
        st.write("Verified" if data.get("verified") else "Rewritten to ensure factual consistency")

        st.subheader("Retrieved Facts (Compressed)")
        facts = data.get("retrieved_facts", [])
        for f in facts:
            with st.expander(f"{f['id']} · {f['symptom']}"):
                st.markdown(f"- Symptom: {f['symptom']}")
                st.markdown(f"- Cause: {f['cause']}")
                st.markdown(f"- Treatment: {f['treatment']}")
                st.markdown(f"- Precaution: {f['precaution']}")

        st.subheader("Token / Size Hints")
        tokens = data.get("tokens_used", {})
        st.write(tokens)

st.markdown("---")
st.caption("If symptoms are urgent (e.g., chest pain, breathing difficulty), seek emergency care.")