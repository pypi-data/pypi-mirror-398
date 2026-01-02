import os
from pathlib import Path

def load_explain_prompt() -> str:
    if os.path.exists("alethe.explain.prompt.md"):
        return Path("alethe.explain.prompt.md").read_text(encoding="utf-8")
    
    return """You are an AI code explainer.

Explain the following Python code thoroughly in markdown with these sections:

# Purpose
# Inputs
# Outputs
# Assumptions
# Side Effects
# Failure Modes
# Risk Level

Code:
{{CODE}}

Output ONLY markdown, no JSON or code blocks (Do not repeat the prompt).
"""



def load_diff_prompt(old_md: str, new_md: str) -> str:
    return f"""
You are an AI code reviewer.

OLD EXPLANATION:
{old_md}

NEW EXPLANATION:
{new_md}

TASK:
Describe all meaningful semantic changes in the new explanation.
Use markdown with headings, bullet points, and summaries.
Output ONLY markdown, no JSON or code blocks.
"""
