
## make sure to export your PAT personal access token 
## change the local to be your path  
## that PAT only works for simple_site https://github.com/rmbeddor14/simple_site

import os, sys, requests
from git import Repo, GitCommandError

# --- Config (env vars) ---
USER = os.getenv("GH_USER")           # e.g., rmbeddor14
TOKEN = os.getenv("GITHUB_TOKEN")     # PAT with repo write
OWNER = "rmbeddor14"                  # org/user that owns the repo
REPO  = "simple_site"                 # repo name
LOCAL = "/Users/rachelbeddor/Desktop/ML_Learning/simple_site"

if not USER or not TOKEN:
    sys.exit("Set **GH_USER** and **GITHUB_TOKEN** env vars.")

# --- 1) Validate PAT ---
u = "https://api.github.com/user"
r = requests.get(u, headers={"Authorization": f"token {TOKEN}"}, timeout=15)
if r.status_code != 200:
    sys.exit(f"PAT check failed ({r.status_code}). **Recreate with repo scope** and **authorize SSO** if needed.")

# --- 2) Prepare repo & remote ---
repo = Repo(LOCAL)
branch = repo.active_branch.name if not repo.head.is_detached else "main"
remote_url = f"https://{USER}:{TOKEN}@github.com/{OWNER}/{REPO}.git"

if "origin" not in [rm.name for rm in repo.remotes]:
    repo.create_remote("origin", remote_url)
else:
    repo.remote("origin").set_url(remote_url)

# --- 3) Commit & push ---
repo.git.add(A=True)
if repo.is_dirty(index=True, working_tree=True, untracked_files=True):
    repo.index.commit("Automated commit via PAT")

try:
    repo.git.push("origin", branch, set_upstream=True)
    print("✅ **Push complete**.")
except GitCommandError as e:
    msg = str(e)
    if "403" in msg or "The requested URL returned error: 403" in msg:
        print("❌ **403 Forbidden**.")
        print("- Ensure PAT has **repo:write** (classic) or **fine-grained write**.")
        print("- If repo is in an **org**, **Authorize SSO** for this token.")
        print("- Confirm you have **push permission** to the repo.")
        print(f"- Remote used: {remote_url.replace(TOKEN, '***')}")
    else:
        print("❌ Git error:", msg)
    sys.exit(1)
