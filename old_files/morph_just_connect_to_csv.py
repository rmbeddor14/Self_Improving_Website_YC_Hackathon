#pip install anthropic 
#pip install openai 
## Look at this engagement CSV data and decide whether to make buttons bigger OR images bigger


import os, re
from anthropic import Anthropic
from openai import OpenAI

# --- CONFIG ---
HTML_PATH = "/Users/rachelbeddor/Desktop/ML_Learning/simple_site/simple_site.html"
NEW_PATH = "/Users/rachelbeddor/Desktop/ML_Learning/simple_site/simple_site_new.html"
CSV_PATH = input("Enter path to your engagement CSV file: ").strip()

# --- LOAD ORIGINAL CODE ---
with open(HTML_PATH, "r", encoding="utf-8") as f:
    initial_code = f.read()

# --- LOAD CSV DATA (UNSTRUCTURED) ---
with open(CSV_PATH, "r", encoding="utf-8") as f:
    csv_data = f.read()

print("CSV data loaded:")
print(csv_data[:500])  # Preview first 500 chars
print("..." if len(csv_data) > 500 else "")
print("\n" + "="*50 + "\n")

# --- LET CLAUDE ANALYZE AND DECIDE ---
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

claude_prompt = f"""
Act as a senior frontend engineer and data analyst.

Your task:
1) Look at this engagement CSV data and decide whether to make buttons bigger OR images bigger
2) Create the CSS/HTML code to implement that enhancement
3) Provide a single imperative instruction

Here's the engagement data:
{csv_data}

Original HTML file (for reference):
{initial_code[:35000]}

Based on the engagement data, decide whether buttons or images need to be enhanced, then return your response in this format:

INSTRUCTION: your single imperative instruction here
CODE_EDIT:
```
your CSS/HTML code here
```

Analyze the data and make buttons bigger if button engagement is low/needs improvement, or make images bigger if image engagement needs improvement.
"""

try:
    msg = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1500,
        messages=[{"role": "user", "content": claude_prompt}]
    )

    content_text = "".join([b.text for b in msg.content if hasattr(b, "text")])
    print("Raw Claude response:")
    print(content_text)
    print("\n" + "="*50 + "\n")
    
    # Parse the structured response format
    instruction_match = re.search(r'INSTRUCTION:\s*(.*?)(?=\nCODE_EDIT:|\n```|$)', content_text, re.DOTALL)
    code_match = re.search(r'CODE_EDIT:\s*```(?:\w+)?\s*(.*?)\s*```', content_text, re.DOTALL)
    
    if instruction_match and code_match:
        instructions = instruction_match.group(1).strip()
        code_edit = code_match.group(1).strip()
    else:
        # Fallback: try to parse as if it's just the instruction and code without markers
        lines = content_text.strip().split('\n')
        instructions = lines[0] if lines else "Enhance UI based on engagement data"
        code_edit = '\n'.join(lines[1:]) if len(lines) > 1 else content_text

    print("Parsed instruction:", instructions)
    print("\nParsed code_edit preview:\n", code_edit[:500])
    if len(code_edit) > 500:
        print("...")
    print("\n" + "="*50 + "\n")

except Exception as e:
    print(f"Claude API failed: {e}")
    exit(1)

# --- SEND TO MORPH TO MERGE ---
print("Sending to Morph for merging...")

morph = OpenAI(
    api_key=os.getenv("MORPH_API_KEY"),
    base_url="https://api.morphllm.com/v1"
)

try:
    resp = morph.chat.completions.create(
        model="morph-v3-large",
        messages=[{
            "role": "user",
            "content": f"<instruction>{instructions}</instruction>\n<code>{initial_code}</code>\n<update>{code_edit}</update>"
        }],
    )

    final_code = resp.choices[0].message.content

    # --- WRITE TO NEW FILE ---
    with open(NEW_PATH, "w", encoding="utf-8") as f:
        f.write(final_code)

    print(f"✅ Merged and saved to: {NEW_PATH}")
    print(f"✅ Claude's decision based on CSV data")

except Exception as e:
    print(f"Error with Morph API: {e}")
    print("Saving Claude's code edit directly...")
    
    # Insert CSS into the HTML
    if '<head>' in initial_code:
        enhanced_html = initial_code.replace('</head>', f'<style>\n{code_edit}\n</style>\n</head>')
    else:
        enhanced_html = f'<style>\n{code_edit}\n</style>\n{initial_code}'
    
    # Add comment with analysis
    enhanced_html = f'<!-- Enhancement based on CSV analysis -->\n{enhanced_html}'
    
    with open(NEW_PATH, "w", encoding="utf-8") as f:
        f.write(enhanced_html)
    print(f"✅ Enhanced HTML saved to: {NEW_PATH}")
    print(f"✅ Claude analyzed the CSV and made the decision")