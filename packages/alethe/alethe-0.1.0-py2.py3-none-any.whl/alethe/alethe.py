# alethe.py
import os
import json
import hashlib
import uuid
import sys
from datetime import datetime, timezone
from pathlib import Path

from llm import LocalHFLLM, StubLLM
from prompts import load_explain_prompt
from semantic_diff import semantic_diff

# -------------------- Paths --------------------
AI_DIR = ".alethe"
EXPLAIN_DIR = os.path.join(AI_DIR, "explain")
DIFF_DIR = os.path.join(AI_DIR, "diffs")
INDEX_FILE = os.path.join(AI_DIR, "index.json")
DEFAULT_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

# -------------------- Utilities --------------------
def load_index():
    if not os.path.exists(INDEX_FILE):
        return {}
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_index(index):
    os.makedirs(AI_DIR, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

def compute_file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def ensure_dirs(file_id):
    os.makedirs(os.path.join(EXPLAIN_DIR, file_id), exist_ok=True)
    os.makedirs(os.path.join(DIFF_DIR, file_id), exist_ok=True)

def normalize_path(p):
    return Path(p).resolve().as_posix()

def get_arg(name, default=None):
    if name in sys.argv:
        idx = sys.argv.index(name)
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return default

# -------------------- Core Logic --------------------
def generate_explanation(file_path, llm):
    prompt = load_explain_prompt().replace("{{FILENAME}}", os.path.basename(file_path))
    explanation_md = llm.explain(prompt)
    metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "code_hash": compute_file_hash(file_path),
        "version": None,
    }
    return explanation_md, metadata

def save_explanation(file_path, file_id, explanation_md, metadata, index):
    ensure_dirs(file_id)
    version = index[file_id]["latest_version"] + 1 if file_id in index else 1
    metadata["version"] = version

    md_path = os.path.join(EXPLAIN_DIR, file_id, f"v{version}.md")
    meta_path = os.path.join(EXPLAIN_DIR, file_id, f"v{version}.json")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(explanation_md)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    file_path = normalize_path(file_path)
    if file_id not in index:
        index[file_id] = {"paths": [file_path], "latest_version": version}
    else:
        index[file_id]["latest_version"] = version
        if file_path not in index[file_id]["paths"]:
            index[file_id]["paths"].append(file_path)

    save_index(index)
    return version

def find_file_id(file_path, index):
    file_path = normalize_path(file_path)
    file_hash = compute_file_hash(file_path)

    for fid, meta in index.items():
        if file_path in meta["paths"]:
            return fid

        latest = meta["latest_version"]
        meta_path = os.path.join(EXPLAIN_DIR, fid, f"v{latest}.json")
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                meta_data = json.load(f)
            if meta_data["code_hash"] == file_hash:
                meta["paths"].append(file_path)
                save_index(index)
                return fid
    return None

# -------------------- Commands --------------------
def command_explain(file_path, index, llm):
    """
    Generate a markdown explanation for a file and save it.
    If a previous explanation exists, produce a semantic diff.
    """
    file_id = find_file_id(file_path, index) or str(uuid.uuid4())
    prev_md = None
    latest_version = None

    # Load previous explanation if it exists
    if file_id in index:
        latest_version = index[file_id]["latest_version"]
        prev_md_path = os.path.join(EXPLAIN_DIR, file_id, f"v{latest_version}.md")
        if os.path.exists(prev_md_path):
            prev_md = Path(prev_md_path).read_text(encoding="utf-8")

    # Generate new explanation
    code = Path(file_path).read_text(encoding="utf-8")
    prompt = load_explain_prompt().replace("{{CODE}}", code)
    explanation_md = llm.explain(prompt)

    # Save explanation
    metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "code_hash": compute_file_hash(file_path),
        "version": None
    }
    version = save_explanation(file_path, file_id, explanation_md, metadata, index)
    print(f"Saved explanation v{version} for {file_path}")

    # Generate semantic diff if previous explanation exists
    if prev_md:
        diff_md = semantic_diff(prev_md, explanation_md)
        diff_path = os.path.join(DIFF_DIR, file_id, f"v{latest_version}_v{version}_semantic.md")
        with open(diff_path, "w", encoding="utf-8") as f:
            f.write(diff_md)
        print(f"Semantic diff saved → {diff_path}")

def command_list(file_path, index):
    file_id = find_file_id(file_path, index)
    if not file_id:
        print("File not tracked.")
        return
    folder = os.path.join(EXPLAIN_DIR, file_id)
    for f in sorted(os.listdir(folder)):
        if f.endswith(".json"):
            with open(os.path.join(folder, f), encoding="utf-8") as j:
                meta = json.load(j)
            print(f"{f.replace('.json','')} @ {meta['timestamp']}")

def command_summary(file_path, index):
    file_id = find_file_id(file_path, index)
    if not file_id:
        print("File not tracked.")
        return
    latest = index[file_id]["latest_version"]
    md_path = os.path.join(EXPLAIN_DIR, file_id, f"v{latest}.md")
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
    print(f"--- Latest Explanation v{latest} ---")
    print(content)

def command_diff(file_path, v1, v2, index):
    file_id = find_file_id(file_path, index)
    if not file_id:
        print("File not tracked.")
        return
    path1 = os.path.join(EXPLAIN_DIR, file_id, f"v{v1}.md")
    path2 = os.path.join(EXPLAIN_DIR, file_id, f"v{v2}.md")
    if not os.path.exists(path1) or not os.path.exists(path2):
        print("One of the versions does not exist.")
        return
    with open(path1, encoding="utf-8") as f:
        old_md = f.read()
    with open(path2, encoding="utf-8") as f:
        new_md = f.read()
    diff_md = semantic_diff(old_md, new_md)
    diff_path = os.path.join(DIFF_DIR, file_id, f"v{v1}_v{v2}_semantic.md")
    with open(diff_path, "w", encoding="utf-8") as f:
        f.write(diff_md)
    print(f"Diff saved to {diff_path}")

def command_rename(old_path, new_path, index):
    file_id = find_file_id(old_path, index)
    if not file_id:
        print("File not tracked.")
        return
    new_path = normalize_path(new_path)
    if new_path not in index[file_id]["paths"]:
        index[file_id]["paths"].append(new_path)
    save_index(index)
    print(f"Renamed {old_path} → {new_path}")

def command_getpath(file_id, index):
    if file_id not in index:
        print("File ID not tracked.")
        return
    paths = index[file_id]["paths"]
    print(f"Paths for file ID {file_id}: {paths}")

# -------------------- Entry --------------------
def main():
    model = get_arg("--model") or DEFAULT_MODEL
    device = get_arg("--device") or "cpu"
    try:
        llm = LocalHFLLM(model, device=device)
    except Exception as e:
        print(f"LLM load failed: {e}")
        llm = StubLLM()

    if len(sys.argv) < 3:
        print("Usage: alethe <command> <file_or_id> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]
    file_arg = sys.argv[2]
    index = load_index()

    if cmd == "explain":
        command_explain(file_arg, index, llm)
    elif cmd == "list":
        command_list(file_arg, index)
    elif cmd == "summary":
        command_summary(file_arg, index)
    elif cmd == "diff":
        if len(sys.argv) < 5:
            print("Usage: alethe diff <file> <vX> <vY>")
            sys.exit(1)
        v1, v2 = sys.argv[3], sys.argv[4]
        command_diff(file_arg, v1, v2, index)
    elif cmd == "rename":
        if len(sys.argv) < 4:
            print("Usage: alethe rename <old_path> <new_path>")
            sys.exit(1)
        new_path = sys.argv[3]
        command_rename(file_arg, new_path, index)
    elif cmd == "getpath":
        command_getpath(file_arg, index)
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()
