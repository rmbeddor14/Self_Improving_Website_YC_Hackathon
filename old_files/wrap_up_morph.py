#pip install anthropic 
#pip install openai 

## example : change the ui to so users will scroll more 

import os, re
from anthropic import Anthropic
from openai import OpenAI

# --- CONFIG ---
HTML_PATH = "/Users/rachelbeddor/Desktop/ML_Learning/simple_site/simple_site.html"
NEW_PATH = "/Users/rachelbeddor/Desktop/ML_Learning/simple_site/simple_site_new.html"

# --- LOAD ORIGINAL CODE ---
with open(HTML_PATH, "r", encoding="utf-8") as f:
    initial_code = f.read()

# --- YOU PROMPT CLAUDE ---
user_goal = input("Tell Claude what you want changed (natural language): ").strip()

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

claude_prompt = f"""
Act as a senior frontend engineer.

Your task:
1) Turn the user's goal into a single imperative instruction
2) Produce a minimal HTML/CSS/JS snippet showing ONLY the new/changed code needed

User goal: {user_goal}

Original file context (for reference only):
{initial_code[:40000]}

Return your response in this format:
INSTRUCTION: your single imperative instruction here
CODE_EDIT:
```
your minimal code snippet here (can be multi-line)
```
"""

try:
    msg = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
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
        instructions = lines[0] if lines else "Enhance scrolling experience"
        code_edit = '\n'.join(lines[1:]) if len(lines) > 1 else content_text

    print("Parsed instruction:", instructions)
    print("\nParsed code_edit preview:\n", code_edit[:500])
    if len(code_edit) > 500:
        print("...")
    print("\n" + "="*50 + "\n")

except Exception as e:
    print(f"Claude parsing failed: {e}")
    print(f"Raw response was: {content_text}")
    print("\nTrying fallback approach...")
    
    # Fallback: ask Claude again with simpler format
    fallback_prompt = f"""
User wants: {user_goal}

Give me:
1. One sentence instruction
2. The code to add (just the code, no explanation)
"""
    
    msg = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=800,
        messages=[{"role": "user", "content": fallback_prompt}]
    )
    
    content_text = "".join([b.text for b in msg.content if hasattr(b, "text")])
    lines = content_text.strip().split('\n')
    instructions = lines[0] if lines else "Enhance scrolling experience"
    code_edit = '\n'.join(lines[1:]) if len(lines) > 1 else content_text

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

except Exception as e:
    print(f"Error with Morph API: {e}")
    print("Saving Claude's code edit directly...")
    with open(NEW_PATH, "w", encoding="utf-8") as f:
        f.write(f"<!-- Original instruction: {instructions} -->\n{code_edit}")
    print(f"✅ Saved Claude's edit to: {NEW_PATH}")