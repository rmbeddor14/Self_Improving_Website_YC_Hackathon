#Claude_Morph_Edit_HTML_GH_or_Upload

import os
import re
import tempfile
import shutil
from typing import Tuple, Optional
from anthropic import Anthropic
from openai import OpenAI
import requests
from git import Repo, GitCommandError


class HTMLEnhancer:
    """Main class for analyzing CSV data and enhancing HTML based on engagement metrics"""
    
    def __init__(self, anthropic_api_key: str, morph_api_key: str):
        """Initialize with API keys"""
        self.anthropic_client = Anthropic(api_key=anthropic_api_key)
        self.morph_client = OpenAI(
            api_key=morph_api_key,
            base_url="https://api.morphllm.com/v1"
        )
    
    def load_file(self, file_path: str) -> str:
        """Load content from a file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {e}")
    
    def load_file_content(self, content: str) -> str:
        """Load content directly from string (for drag-and-drop scenarios)"""
        return content
    
    def preview_csv_data(self, csv_data: str, preview_length: int = 500) -> None:
        """Print a preview of CSV data"""
        print("CSV data loaded:")
        print(csv_data[:preview_length])
        print("..." if len(csv_data) > preview_length else "")
        print("\n" + "="*50 + "\n")
    
    def analyze_engagement_with_claude(self, csv_data: str, html_content: str) -> Tuple[str, str]:
        """
        Analyze engagement data with Claude and get enhancement instructions
        
        Returns:
            Tuple of (instructions, code_edit)
        """
        claude_prompt = f"""
Act as a senior frontend engineer and data analyst.

Your task:

1) pretend you're a senior UX UI engineer specializing in conversion and rate optimization 
based on the engagement data make lots of changes even if they seem dramatic, change the text if needed, make buttons bigger if needed, rearrange elements on the hero section especially 
2) Create the CSS/HTML code to implement that enhancement
3) Provide a single imperative instruction

Here's the engagement data:
{csv_data}

Original HTML file (for reference):
{html_content[:35000]}

INSTRUCTION: your single imperative instruction here
CODE_EDIT:
```
your CSS/HTML code here
```

Analyze the data and make buttons bigger if button engagement is low/needs improvement, or make images bigger if image engagement needs improvement.
"""

        try:
            msg = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": claude_prompt}]
            )

            content_text = "".join([b.text for b in msg.content if hasattr(b, "text")])
            print("Raw Claude response:")
            print(content_text)
            print("\n" + "="*50 + "\n")
            
            return self._parse_claude_response(content_text)
            
        except Exception as e:
            raise Exception(f"Claude API failed: {e}")
    
    def _parse_claude_response(self, content_text: str) -> Tuple[str, str]:
        """Parse Claude's structured response"""
        instruction_match = re.search(r'INSTRUCTION:\s*(.*?)(?=\nCODE_EDIT:|\n```|$)', content_text, re.DOTALL)
        code_match = re.search(r'CODE_EDIT:\s*```(?:\w+)?\s*(.*?)\s*```', content_text, re.DOTALL)
        
        if instruction_match and code_match:
            instructions = instruction_match.group(1).strip()
            code_edit = code_match.group(1).strip()
        else:
            # Fallback parsing
            lines = content_text.strip().split('\n')
            instructions = lines[0] if lines else "Enhance UI based on engagement data"
            code_edit = '\n'.join(lines[1:]) if len(lines) > 1 else content_text

        print("Parsed instruction:", instructions)
        print("\nParsed code_edit preview:\n", code_edit[:500])
        if len(code_edit) > 500:
            print("...")
        print("\n" + "="*50 + "\n")
        
        return instructions, code_edit
    
    def merge_with_morph(self, instructions: str, original_html: str, code_edit: str) -> str:
        """Use Morph API to merge the code changes"""
        print("Sending to Morph for merging...")
        
        try:
            resp = self.morph_client.chat.completions.create(
                model="morph-v3-large",
                messages=[{
                    "role": "user",
                    "content": f"<instruction>{instructions}</instruction>\n<code>{original_html}</code>\n<update>{code_edit}</update>"
                }],
            )
            
            return resp.choices[0].message.content
            
        except Exception as e:
            print(f"Error with Morph API: {e}")
            print("Falling back to direct CSS insertion...")
            return self._fallback_merge(original_html, code_edit)
    
    def _fallback_merge(self, html_content: str, code_edit: str) -> str:
        """Fallback method to merge CSS directly into HTML"""
        if '<head>' in html_content:
            enhanced_html = html_content.replace('</head>', f'<style>\n{code_edit}\n</style>\n</head>')
        else:
            enhanced_html = f'<style>\n{code_edit}\n</style>\n{html_content}'
        
        # Add comment with analysis
        enhanced_html = f'<!-- Enhancement based on CSV analysis -->\n{enhanced_html}'
        return enhanced_html
    
    def save_enhanced_html(self, enhanced_html: str, output_path: str) -> None:
        """Save the enhanced HTML to a file"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(enhanced_html)
            print(f"✅ Enhanced HTML saved to: {output_path}")
        except Exception as e:
            raise Exception(f"Error saving file: {e}")
    
    def validate_github_pat(self, token: str) -> bool:
        """Validate GitHub Personal Access Token"""
        try:
            headers = {"Authorization": f"token {token}"}
            response = requests.get("https://api.github.com/user", headers=headers, timeout=15)
            return response.status_code == 200
        except Exception:
            return False
    
    def push_to_github(self, 
                      enhanced_html: str, 
                      github_token: str, 
                      github_user: str,
                      repo_owner: str, 
                      repo_name: str, 
                      file_path: str,
                      commit_message: str = "Enhanced HTML based on engagement analysis") -> bool:
        """
        Push enhanced HTML directly to GitHub repository
        
        Args:
            enhanced_html: The enhanced HTML content
            github_token: GitHub Personal Access Token
            github_user: GitHub username
            repo_owner: Repository owner (can be same as user)
            repo_name: Repository name
            file_path: Path to the HTML file in the repo (e.g., 'index.html', 'pages/home.html')
            commit_message: Commit message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate PAT first
            if not self.validate_github_pat(github_token):
                raise Exception("Invalid GitHub Personal Access Token")
            
            # Create temporary directory for cloning
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = os.path.join(temp_dir, repo_name)
                remote_url = f"https://{github_user}:{github_token}@github.com/{repo_owner}/{repo_name}.git"
                
                print(f"Cloning repository: {repo_owner}/{repo_name}")
                
                # Clone the repository
                try:
                    repo = Repo.clone_from(remote_url, repo_path)
                except Exception as e:
                    raise Exception(f"Failed to clone repository: {e}")
                
                # Write the enhanced HTML to the specified file
                html_file_path = os.path.join(repo_path, file_path)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(html_file_path), exist_ok=True)
                
                with open(html_file_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_html)
                
                print(f"Updated file: {file_path}")
                
                # Add, commit, and push changes
                repo.git.add(A=True)
                
                if repo.is_dirty(index=True, working_tree=True, untracked_files=True):
                    repo.index.commit(commit_message)
                    print("Changes committed")
                    
                    # Push to origin
                    origin = repo.remote('origin')
                    branch = repo.active_branch.name if not repo.head.is_detached else "main"
                    origin.push(branch)
                    
                    print("✅ Successfully pushed changes to GitHub")
                    return True
                else:
                    print("No changes to commit")
                    return True
                    
        except GitCommandError as e:
            error_msg = str(e)
            if "403" in error_msg:
                raise Exception("403 Forbidden: Check your PAT permissions and SSO authorization")
            else:
                raise Exception(f"Git error: {error_msg}")
        except Exception as e:
            raise Exception(f"GitHub push failed: {e}")
    
    def process_files(self, csv_path: str, html_path: str, output_path: str) -> str:
        """
        Main processing function for file-based workflow
        
        Args:
            csv_path: Path to CSV file
            html_path: Path to original HTML file
            output_path: Path for enhanced HTML output
            
        Returns:
            Enhanced HTML content
        """
        # Load files
        csv_data = self.load_file(csv_path)
        html_content = self.load_file(html_path)
        
        # Preview CSV
        self.preview_csv_data(csv_data)
        
        # Analyze with Claude
        instructions, code_edit = self.analyze_engagement_with_claude(csv_data, html_content)
        
        # Merge changes
        enhanced_html = self.merge_with_morph(instructions, html_content, code_edit)
        
        # Save result
        self.save_enhanced_html(enhanced_html, output_path)
        
        return enhanced_html
    
    def process_content(self, csv_content: str, html_content: str) -> Tuple[str, str]:
        """
        Main processing function for content-based workflow (drag-and-drop)
        
        Args:
            csv_content: CSV data as string
            html_content: HTML content as string
            
        Returns:
            Tuple of (enhanced_html_content, analysis_instructions)
        """
        # Preview CSV
        self.preview_csv_data(csv_content)
        
        # Analyze with Claude
        instructions, code_edit = self.analyze_engagement_with_claude(csv_content, html_content)
        
        # Merge changes
        enhanced_html = self.merge_with_morph(instructions, html_content, code_edit)
        
        return enhanced_html, instructions
    
    def process_and_push_to_github(self, 
                                  csv_content: str, 
                                  html_content: str,
                                  github_token: str,
                                  github_user: str,
                                  repo_owner: str,
                                  repo_name: str,
                                  file_path: str) -> Tuple[str, str, bool]:
        """
        Process content and push directly to GitHub
        
        Returns:
            Tuple of (enhanced_html_content, analysis_instructions, push_success)
        """
        # Process the content first
        enhanced_html, instructions = self.process_content(csv_content, html_content)
        
        # Push to GitHub
        try:
            push_success = self.push_to_github(
                enhanced_html=enhanced_html,
                github_token=github_token,
                github_user=github_user,
                repo_owner=repo_owner,
                repo_name=repo_name,
                file_path=file_path,
                commit_message=f"Enhanced HTML based on engagement analysis: {instructions[:100]}..."
            )
        except Exception as e:
            print(f"GitHub push failed: {e}")
            push_success = False
            
        return enhanced_html, instructions, push_success


# Convenience functions for easy integration
def create_enhancer_from_env() -> HTMLEnhancer:
    """Create HTMLEnhancer using environment variables for API keys"""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    morph_key = os.getenv("MORPH_API_KEY")
    
    if not anthropic_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    if not morph_key:
        raise ValueError("MORPH_API_KEY environment variable not set")
    
    return HTMLEnhancer(anthropic_key, morph_key)


def enhance_html_from_files(csv_path: str, html_path: str, output_path: str) -> str:
    """
    Convenience function to enhance HTML from file paths
    
    Args:
        csv_path: Path to engagement CSV file
        html_path: Path to original HTML file
        output_path: Path for enhanced HTML output
        
    Returns:
        Enhanced HTML content
    """
    enhancer = create_enhancer_from_env()
    return enhancer.process_files(csv_path, html_path, output_path)


def enhance_html_from_content(csv_content: str, html_content: str) -> Tuple[str, str]:
    """
    Convenience function to enhance HTML from content strings (for drag-and-drop UI)
    
    Args:
        csv_content: CSV data as string
        html_content: HTML content as string
        
    Returns:
        Tuple of (enhanced_html_content, analysis_instructions)
    """
    enhancer = create_enhancer_from_env()
    return enhancer.process_content(csv_content, html_content)


def enhance_and_push_to_github(csv_content: str, 
                              html_content: str,
                              github_token: str,
                              github_user: str,
                              repo_owner: str,
                              repo_name: str,
                              file_path: str) -> Tuple[str, str, bool]:
    """
    Convenience function to enhance HTML and push directly to GitHub
    
    Returns:
        Tuple of (enhanced_html_content, analysis_instructions, push_success)
    """
    enhancer = create_enhancer_from_env()
    return enhancer.process_and_push_to_github(
        csv_content, html_content, github_token, github_user, 
        repo_owner, repo_name, file_path
    )


# Example usage for command line (enhanced with GitHub support)
def main():
    """Enhanced CLI interface with GitHub integration"""
    print("🚀 HTML Engagement Enhancer CLI")
    print("="*50)
    
    try:
        # Get GitHub credentials
        github_token = input("Enter your GitHub Personal Access Token: ").strip()
        github_user = input("Enter your GitHub username: ").strip()
        repo_owner = input("Enter repository owner (press Enter to use your username): ").strip() or github_user
        repo_name = input("Enter repository name: ").strip()
        file_path = input("Enter HTML file path in repo (e.g., index.html): ").strip()
        
        # Get CSV data
        csv_option = input("\nChoose CSV source:\n1) File path\n2) Paste CSV data\nEnter choice (1 or 2): ").strip()
        
        if csv_option == "1":
            csv_path = input("Enter path to your engagement CSV file: ").strip()
            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
        elif csv_option == "2":
            print("Paste your CSV data (press Ctrl+D or Ctrl+Z when done):")
            csv_lines = []
            try:
                while True:
                    line = input()
                    csv_lines.append(line)
            except EOFError:
                pass
            csv_content = "\n".join(csv_lines)
        else:
            raise ValueError("Invalid choice. Please enter 1 or 2.")
        
        print("\n" + "="*50)
        print("🔍 Starting analysis and GitHub workflow...")
        
        # Create enhancer
        enhancer = create_enhancer_from_env()
        
        # First, we need to get the current HTML from GitHub
        print(f"📥 Fetching current HTML from GitHub: {repo_owner}/{repo_name}/{file_path}")
        
        # Clone repo to get current HTML
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, repo_name)
            remote_url = f"https://{github_user}:{github_token}@github.com/{repo_owner}/{repo_name}.git"
            
            try:
                repo = Repo.clone_from(remote_url, repo_path)
                html_file_path = os.path.join(repo_path, file_path)
                
                if not os.path.exists(html_file_path):
                    raise FileNotFoundError(f"File {file_path} not found in repository")
                
                with open(html_file_path, 'r', encoding='utf-8') as f:
                    current_html = f.read()
                    
                print(f"✅ Successfully fetched {file_path}")
                
            except Exception as e:
                raise Exception(f"Failed to fetch HTML from GitHub: {e}")
        
        # Process the enhancement
        enhanced_html, instructions, push_success = enhancer.process_and_push_to_github(
            csv_content=csv_content,
            html_content=current_html,
            github_token=github_token,
            github_user=github_user,
            repo_owner=repo_owner,
            repo_name=repo_name,
            file_path=file_path
        )
        
        if push_success:
            print("\n🎉 SUCCESS!")
            print(f"📋 Enhancement Applied: {instructions}")
            print(f"🔗 Repository: https://github.com/{repo_owner}/{repo_name}")
            print(f"📄 Updated File: https://github.com/{repo_owner}/{repo_name}/blob/main/{file_path}")
            
            # Offer to save local copy
            save_local = input("\nSave enhanced HTML locally? (y/n): ").strip().lower()
            if save_local == 'y':
                local_path = input("Enter local file path (e.g., enhanced.html): ").strip()
                enhancer.save_enhanced_html(enhanced_html, local_path)
        else:
            print("\n❌ GitHub push failed, but enhancement was created.")
            print(f"📋 Enhancement: {instructions}")
            
            # Save locally since GitHub push failed
            local_path = input("Save enhanced HTML locally? Enter file path (or press Enter to skip): ").strip()
            if local_path:
                enhancer.save_enhanced_html(enhanced_html, local_path)
        
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("- Ensure your GitHub PAT has 'repo' permissions")
        print("- If repo is in an organization, authorize SSO for your token")
        print("- Check that the repository and file path exist")
        print("- Verify your ANTHROPIC_API_KEY is set in environment variables")


if __name__ == "__main__":
    main()