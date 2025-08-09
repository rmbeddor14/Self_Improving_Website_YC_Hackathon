# HTML Engagement Enhancer

Analyze a CSV of engagement metrics and **auto‑enhance HTML**. Run locally as a **Streamlit** app or call the core class directly.

## Requirements
- Python 3.9+
- `pip install -r requirements.txt` (see below)

### Python packages
```
streamlit
gitpython
anthropic
openai
requests
```
> Optional extras: any CSV tool you prefer; the app accepts raw text CSV.

## Environment Variables (required/optional)
- **`ANTHROPIC_API_KEY`** *(required)* — API key from Anthropic console.
- **`MORPH_API_KEY`** *(required)* — API key for Morph.
- No GitHub env vars are required; the Streamlit UI asks for **GitHub token**, **username**, **owner**, **repo**, **branch**, and **file path** when you choose the GitHub workflow.

> GitHub token scopes: `repo` (private or public). If the org uses SSO, be sure to **authorize the token for that org**. 403 errors usually mean missing scope or SSO not enabled.

## Run (Streamlit UI)
```bash
# from the project root
streamlit run streamlit-github.py
```
1) Open the app in your browser (Streamlit prints the URL).
2) Expand **Required API Keys** and paste your keys (pre-fills from env if set).
3) Choose a workflow:
   - **Upload HTML File** → upload CSV + HTML, then **Analyze & Enhance** → download result.
   - **GitHub Repository** → enter repo details; the app will fetch, enhance, and **push** a commit.

## Programmatic Use
```python
from Claude_Morph_Edit_HTML_GH_or_Upload import create_enhancer_from_env

enhancer = create_enhancer_from_env()  # uses ANTHROPIC_API_KEY and MORPH_API_KEY
html = Path("page.html").read_text()
csv  = Path("metrics.csv").read_text()

# returns (enhanced_html, edit_summary)
enhanced, summary = enhancer.enhance_html_with_data(csv, html)
Path("page.enhanced.html").write_text(enhanced)
```

## Troubleshooting
- **403 when pushing to GitHub** → check PAT scopes and SSO org authorization.
- **Missing keys** → ensure `ANTHROPIC_API_KEY` and `MORPH_API_KEY` are set or pasted in the UI.
- **CSV issues** → ensure it’s plain‑text CSV (UTF‑8 preferred).

## Example `.env`
```
ANTHROPIC_API_KEY=sk-ant-...
MORPH_API_KEY=sk-morph-...
```
