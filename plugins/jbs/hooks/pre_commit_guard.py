"""PreToolUse(Bash) 훅: `git commit` 직전에 스테이징된 변경을 점검한다.

- 확실한 위험(개인키, 알려진 토큰 접두사, 비밀 파일, 충돌 마커, 100MB 초과) -> deny
- 애매한 것(token/password 대입, 연결 문자열) -> ask
- 값은 출력하지 않고 파일:줄번호와 종류만 보고한다.
- 우회: 명령 앞에 SKIP_PRECOMMIT_CHECK=1 (사용자가 명시적으로 요청할 때만)
"""
import fnmatch
import json
import os
import re
import subprocess
import sys

COMMIT_RE = re.compile(r"(^|[;&|(]\s*|\s)git\s+(-\S+\s+(\S+\s+)?)*commit\b")
BYPASS_RE = re.compile(r"(^|\s)SKIP_PRECOMMIT_CHECK=1\b")
MAX_BYTES = 100 * 1024 * 1024

SECRET_FILES = [".env", ".env.*", "*.pem", "*.key", "id_rsa*", "credentials*.json"]
SECRET_FILE_OK = [".env.example"]
# 점검 패턴 자체를 담고 있는 파일은 내용 검사에서 제외한다(자기 자신 오탐 방지)
CONTENT_SKIP = {
    "plugins/jbs/hooks/pre_commit_guard.py",
    "plugins/jbs/skills/pre-commit-check/SKILL.md",
}

DENY_PATTERNS = [
    ("개인키", re.compile(r"BEGIN [A-Z ]*PRIVATE KEY")),
    ("알려진 토큰 접두사", re.compile(r"sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|github_pat_|AKIA[0-9A-Z]{12,}|xox[bap]-|AIza[0-9A-Za-z_-]{20,}")),
    ("충돌 마커", re.compile(r"^(<<<<<<< |>>>>>>> )")),
]
ASK_PATTERNS = [
    ("키/비밀번호 대입 의심", re.compile(r"(api_?key|secret|token|passw(or)?d|credential)[^=:]*[=:]", re.I)),
    ("연결 문자열 자격증명", re.compile(r"://[^/\s]+:[^@\s]+@")),
]


def git(args, cwd):
    r = subprocess.run(["git", "-c", "core.quotepath=off"] + args, cwd=cwd,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


def respond(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except ValueError:
        return
    command = (data.get("tool_input") or {}).get("command", "")
    if data.get("tool_name") != "Bash" or not COMMIT_RE.search(command):
        return
    if BYPASS_RE.search(command) or os.environ.get("SKIP_PRECOMMIT_CHECK") == "1":
        return

    cwd = data.get("cwd")
    if not cwd or not os.path.isdir(cwd):
        cwd = os.getcwd()
    deny, ask = [], []

    names = git(["diff", "--cached", "--name-only", "--diff-filter=AM"], cwd).splitlines()
    root = git(["rev-parse", "--show-toplevel"], cwd).strip()
    for name in names:
        base = os.path.basename(name)
        if base not in SECRET_FILE_OK and any(fnmatch.fnmatch(base, p) for p in SECRET_FILES):
            deny.append(f"{name} — 비밀 정보 파일")
        path = os.path.join(root, name) if root else name
        if os.path.isfile(path) and os.path.getsize(path) > MAX_BYTES:
            deny.append(f"{name} — 100MB 초과")

    current, lineno = None, 0
    for line in git(["diff", "--cached", "-U0", "--no-color"], cwd).splitlines():
        if line.startswith("+++ "):
            current = line[4:].split("\t")[0]
            current = current[2:] if current.startswith("b/") else None
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            lineno = int(m.group(1)) if m else 0
        elif line.startswith("+") and current and current not in CONTENT_SKIP:
            text = line[1:]
            hit = False
            for kind, pat in DENY_PATTERNS:
                if pat.search(text):
                    deny.append(f"{current}:{lineno} — {kind} (***)")
                    hit = True
                    break
            if not hit:
                for kind, pat in ASK_PATTERNS:
                    if pat.search(text):
                        ask.append(f"{current}:{lineno} — {kind} (***)")
                        break
            lineno += 1

    if not deny and not ask:
        return
    lines = [f"- [차단] {d}" for d in deny] + [f"- [확인] {a}" for a in ask]
    report = "pre-commit-check 훅 점검 결과:\n" + "\n".join(lines)
    guide = ("\n사용자에게 이 목록을 보여주고 판단을 받을 것. "
             "사용자가 명시적으로 진행을 요청한 경우에만 명령 앞에 SKIP_PRECOMMIT_CHECK=1 을 붙여 다시 실행할 것. "
             "임의로 우회하거나 --no-verify 를 붙이지 말 것.")
    respond("deny" if deny else "ask", report + guide)


if __name__ == "__main__":
    main()
