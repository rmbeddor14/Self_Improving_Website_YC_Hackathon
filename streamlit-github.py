# streamlit_app.py
import os
import streamlit as st
import tempfile
from git import Repo

from Claude_Morph_Edit_HTML_GH_or_Upload import HTMLEnhancer

st.set_page_config(page_title="HTML Engagement Enhancer", layout="wide")
st.title("📈 HTML Engagement Enhancer")
st.caption("Analyze engagement data and enhance your HTML with AI-powered optimizations")

# API Keys Section (always needed)
with st.expander("🔑 Required API Keys", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        anthropic_key = st.text_input(
            "Anthropic API Key",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            type="password",
            help="Get from console.anthropic.com"
        )
    with col2:
        morph_key = st.text_input(
            "Morph API Key",
            value=os.getenv("MORPH_API_KEY", ""),
            type="password",
            help="Optional - will use fallback if not provided"
        )

# Main workflow selection
st.subheader("🎯 Choose Your Workflow")

workflow = st.radio(
    "How would you like to work with your HTML?",
    ["📁 Upload HTML File", "🐙 Connect to GitHub Repository"],
    help="Upload: Analyze and download enhanced HTML. GitHub: Fetch, analyze, and automatically push changes."
)

# CSV Upload (common to both workflows)
st.subheader("📊 Upload Engagement Data")
csv_file = st.file_uploader(
    "Upload your engagement CSV file",
    type=["csv"],
    help="CSV containing engagement metrics like click rates, hover times, scroll depth, etc."
)

def read_text_file(uploaded_file) -> str:
    """Helper function to read uploaded text files"""
    raw = uploaded_file.read()
    if isinstance(raw, bytes):
        for encoding in ("utf-8", "utf-16", "latin-1"):
            try:
                return raw.decode(encoding)
            except Exception:
                continue
        return raw.decode("utf-8", errors="ignore")
    return str(raw)

# Workflow-specific sections
if workflow == "📁 Upload HTML File":
    st.subheader("📄 Upload HTML File")
    html_file = st.file_uploader(
        "Upload your HTML file",
        type=["html", "htm"],
        help="The HTML file you want to enhance"
    )
    
    # Process button for upload workflow
    if st.button("🔍 Analyze & Enhance HTML", type="primary", use_container_width=True):
        # Validation
        if not csv_file or not html_file:
            st.error("❌ Please upload both CSV and HTML files")
            st.stop()
        
        if not anthropic_key:
            st.error("❌ Anthropic API Key is required")
            st.stop()
        
        # Process
        with st.spinner("🤖 Analyzing engagement data and enhancing HTML..."):
            try:
                csv_content = read_text_file(csv_file)
                html_content = read_text_file(html_file)
                
                enhancer = HTMLEnhancer(
                    anthropic_api_key=anthropic_key,
                    morph_api_key=morph_key or "DUMMY"
                )
                
                enhanced_html, instructions = enhancer.process_content(csv_content, html_content)
                
                st.success("✅ Enhancement completed!")
                
                # Display results
                st.subheader("📋 Enhancement Instructions")
                st.info(instructions)
                
                st.subheader("🎨 Enhanced HTML Preview")
                st.components.v1.html(enhanced_html, height=600, scrolling=True)
                
                # Download button
                st.download_button(
                    "💾 Download Enhanced HTML",
                    data=enhanced_html.encode("utf-8"),
                    file_name=f"enhanced_{html_file.name}",
                    mime="text/html",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

elif workflow == "🐙 Connect to GitHub Repository":
    st.subheader("🔗 GitHub Repository Settings")
    
    # GitHub configuration
    github_col1, github_col2 = st.columns(2)
    
    with github_col1:
        github_token = st.text_input(
            "GitHub Personal Access Token",
            type="password",
            help="PAT with 'repo' permissions"
        )
        github_user = st.text_input(
            "Your GitHub Username",
            help="Your GitHub username"
        )
    
    with github_col2:
        repo_owner = st.text_input(
            "Repository Owner",
            help="Username or org that owns the repo (often same as your username)"
        )
        repo_name = st.text_input(
            "Repository Name",
            help="Name of the repository"
        )
    
    file_path = st.text_input(
        "HTML File Path in Repository",
        value="index.html",
        help="Path to your HTML file (e.g., 'index.html', 'pages/home.html')"
    )
    
    # Auto-fill repo_owner with github_user if empty
    if github_user and not repo_owner:
        repo_owner = github_user
    
    # Show repository preview
    if repo_owner and repo_name:
        repo_url = f"https://github.com/{repo_owner}/{repo_name}"
        st.markdown(f"📍 **Target Repository:** [{repo_owner}/{repo_name}]({repo_url})")
        if file_path:
            file_url = f"{repo_url}/blob/main/{file_path}"
            st.markdown(f"📄 **Target File:** [{file_path}]({file_url})")
    
    # Process and push button for GitHub workflow
    if st.button("🚀 Fetch, Analyze & Push to GitHub", type="primary", use_container_width=True):
        # Validation
        if not csv_file:
            st.error("❌ Please upload a CSV file")
            st.stop()
        
        if not anthropic_key:
            st.error("❌ Anthropic API Key is required")
            st.stop()
        
        github_fields = [github_token, github_user, repo_owner, repo_name, file_path]
        if not all(github_fields):
            st.error("❌ Please fill in all GitHub repository fields")
            st.stop()
        
        # Process with GitHub integration
        with st.spinner("🔄 Fetching HTML from GitHub..."):
            try:
                # First, fetch the current HTML from GitHub
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo_path = os.path.join(temp_dir, repo_name)
                    remote_url = f"https://{github_user}:{github_token}@github.com/{repo_owner}/{repo_name}.git"
                    
                    repo = Repo.clone_from(remote_url, repo_path)
                    html_file_path = os.path.join(repo_path, file_path)
                    
                    if not os.path.exists(html_file_path):
                        st.error(f"❌ File '{file_path}' not found in repository")
                        st.stop()
                    
                    with open(html_file_path, 'r', encoding='utf-8') as f:
                        current_html = f.read()
                    
                    st.success(f"✅ Successfully fetched {file_path} from GitHub")
                        
            except Exception as e:
                st.error(f"❌ Failed to fetch from GitHub: {str(e)}")
                st.stop()
        
        with st.spinner("🤖 Analyzing engagement data and enhancing HTML..."):
            try:
                csv_content = read_text_file(csv_file)
                
                enhancer = HTMLEnhancer(
                    anthropic_api_key=anthropic_key,
                    morph_api_key=morph_key or "DUMMY"
                )
                
                enhanced_html, instructions, push_success = enhancer.process_and_push_to_github(
                    csv_content=csv_content,
                    html_content=current_html,
                    github_token=github_token,
                    github_user=github_user,
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    file_path=file_path
                )
                
                # Display results
                if push_success:
                    st.success("🎉 Enhancement completed and pushed to GitHub!")
                    st.balloons()
                    
                    # Show links
                    repo_url = f"https://github.com/{repo_owner}/{repo_name}"
                    file_url = f"{repo_url}/blob/main/{file_path}"
                    
                    link_col1, link_col2 = st.columns(2)
                    with link_col1:
                        st.markdown(f"🔗 **[View Repository]({repo_url})**")
                    with link_col2:
                        st.markdown(f"📄 **[View Updated File]({file_url})**")
                else:
                    st.error("❌ Enhancement completed but GitHub push failed")
                
                # Show enhancement details
                st.subheader("📋 Enhancement Instructions")
                st.info(instructions)
                
                st.subheader("🎨 Enhanced HTML Preview")
                st.components.v1.html(enhanced_html, height=600, scrolling=True)
                
                # Backup download option
                st.download_button(
                    "💾 Download Enhanced HTML (Backup)",
                    data=enhanced_html.encode("utf-8"),
                    file_name=f"enhanced_{file_path}",
                    mime="text/html",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"❌ Processing error: {str(e)}")

# Help section
with st.expander("❓ Help & Setup Guide"):
    tab1, tab2, tab3 = st.tabs(["🔑 API Keys", "🐙 GitHub Setup", "📊 CSV Format"])
    
    with tab1:
        st.markdown("""
        ### API Key Setup
        
        **Anthropic API Key (Required):**
        1. Visit [console.anthropic.com](https://console.anthropic.com)
        2. Create an account or sign in
        3. Go to API Keys section
        4. Generate a new API key
        5. Copy and paste it above
        
        **Morph API Key (Optional):**
        - Used for advanced code merging
        - If not provided, will use built-in fallback method
        """)
    
    with tab2:
        st.markdown("""
        ### GitHub Personal Access Token Setup
        
        1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
        2. Click **"Generate new token (classic)"**
        3. Give it a descriptive name (e.g., "HTML Enhancer")
        4. Select the **`repo`** scope (full control of private repositories)
        5. Click "Generate token"
        6. **Important:** If your repository is in an organization, authorize SSO for your token
        7. Copy the token immediately (you won't see it again)
        
        **Common GitHub Issues:**
        - **403 Forbidden:** Token lacks permissions or needs SSO authorization
        - **Repository not found:** Check owner/repo names are correct
        - **File not found:** Verify the file path exists in your repository
        """)
    
    with tab3:
        st.markdown("""
        ### Expected CSV Format
        
        Your engagement CSV should contain metrics such as:
        - **Click rates** by element/section
        - **Hover times** and interactions
        - **Scroll depth** percentages
        - **Conversion metrics**
        - **Time spent** on different sections
        - **User behavior patterns**
        
        The AI will analyze this data to determine:
        - Which buttons need to be larger or more prominent
        - Which sections need repositioning
        - What content needs emphasis
        - Where to improve visual hierarchy
        """)

st.markdown("---")
st.caption("🔒 **Privacy:** All processing happens on secure AI servers. GitHub tokens are only used for repository access.")
st.caption("💡 **Tip:** Set environment variables `ANTHROPIC_API_KEY` and `MORPH_API_KEY` for auto-fill")