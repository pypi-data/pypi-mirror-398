# semantic_diff.py
from llm import LocalHFLLM, StubLLM

DEFAULT_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

def semantic_diff(old_md: str, new_md: str, model_name=DEFAULT_MODEL) -> str:
    """
    Compare old and new markdown explanations.
    Returns markdown summary of semantic changes.
    """
    prompt = f"""
You are an AI code reviewer.

OLD EXPLANATION:
{old_md}

NEW EXPLANATION:
{new_md}

TASK:
Describe all meaningful semantic changes in the new explanation.
Use markdown with headings, bullet points, and summaries.
Output ONLY markdown.
"""
    try:
        llm = LocalHFLLM(model_name)
    except Exception:
        llm = StubLLM()

    return llm.generate(prompt)
