# streamlit_app.py
import os
import streamlit as st

from ui_morph_csv import HTMLEnhancer  # <- your file

st.set_page_config(page_title="HTML Engagement Enhancer", layout="wide")
st.title("📈 HTML Engagement Enhancer")
st.caption("Drag & drop your engagement CSV and corresponding HTML to get an enhanced version.")

with st.expander("🔑 API Keys"):
    c1, c2 = st.columns(2)
    with c1:
        anthropic_key_input = st.text_input(
            "ANTHROPIC_API_KEY",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            type="password",
            help="Used for Claude analysis."
        )
    with c2:
        morph_key_input = st.text_input(
            "MORPH_API_KEY",
            value=os.getenv("MORPH_API_KEY", ""),
            type="password",
            help="Used for Morph merge (falls back to inline merge if unavailable)."
        )

def read_text(uploaded_file) -> str:
    raw = uploaded_file.read()
    if isinstance(raw, bytes):
        for enc in ("utf-8", "utf-16", "latin-1"):
            try:
                return raw.decode(enc)
            except Exception:
                continue
        return raw.decode("utf-8", errors="ignore")
    return str(raw)

lc, rc = st.columns(2)
with lc:
    csv_file = st.file_uploader("📥 Engagement CSV", type=["csv"])
with rc:
    html_file = st.file_uploader("📥 Original HTML", type=["html", "htm"])

run = st.button("🚀 Analyze & Enhance", type="primary", use_container_width=True)

if run:
    if not csv_file or not html_file:
        st.error("Please upload **both** CSV and HTML files.")
        st.stop()

    anthropic_key = anthropic_key_input or os.getenv("ANTHROPIC_API_KEY")
    morph_key = morph_key_input or os.getenv("MORPH_API_KEY") or "DUMMY"

    if not anthropic_key:
        st.error("Missing **ANTHROPIC_API_KEY**.")
        st.stop()

    with st.spinner("Analyzing engagement and applying enhancements..."):
        try:
            csv_text = read_text(csv_file)
            html_text = read_text(html_file)

            enhancer = HTMLEnhancer(anthropic_api_key=anthropic_key, morph_api_key=morph_key)
            enhanced_html, instruction = enhancer.process_content(csv_text, html_text)
        except Exception as e:
            st.exception(e)
            st.stop()

    st.success("Enhancement complete!")
    st.subheader("Instruction from analysis")
    st.code(instruction)

    st.subheader("Enhanced HTML Preview")
    st.components.v1.html(enhanced_html, height=700, scrolling=True)

    st.download_button(
        "💾 Download Enhanced HTML",
        data=enhanced_html.encode("utf-8"),
        file_name="enhanced.html",
        mime="text/html"
    )

st.markdown("---")
st.caption("Tip: store keys in your environment so the inputs auto-fill next time.")
