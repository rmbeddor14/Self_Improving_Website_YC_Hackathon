#ui_morph_csv.py

import os
import re
from typing import Tuple, Optional
from anthropic import Anthropic
from openai import OpenAI


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


# Example usage for command line (original behavior)
def main():
    """Command line interface - maintains original script behavior"""
    try:
        # Configuration
        HTML_PATH = "/Users/rachelbeddor/Desktop/ML_Learning/simple_site/simple_site.html"
        NEW_PATH = "/Users/rachelbeddor/Desktop/ML_Learning/simple_site/simple_site_new.html"
        CSV_PATH = input("Enter path to your engagement CSV file: ").strip()
        
        # Process files
        enhanced_html = enhance_html_from_files(CSV_PATH, HTML_PATH, NEW_PATH)
        
        print(f"✅ Claude analyzed the CSV and made the decision")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()