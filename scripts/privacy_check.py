"""Fail when tracked files would publish private data: run diagnostics, credentials or personal details.

Token patterns are gitleaks' job; this covers what it does not know about this project.
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

# Runner/fallback artifacts and loop logs may contain private code, plans or prompts (see runtime.md).
DIAGNOSTIC_NAMES = {"prompt.txt", "command.json", "stdout.txt", "stderr.txt", "reply.txt", "result.json",
                    "response.json", "snapshot.json", "version-stdout.txt", "version-stderr.txt",
                    "PLAN-REVIEW-LOG.md"}
CREDENTIAL_FILE = re.compile(r"(^|/)(\.env(\..+)?|\.netrc|\.npmrc|\.pypirc|auth\.json|id_(rsa|ecdsa|ed25519)"
                             r"|.+\.(pem|key|p12|pfx|keystore))$", re.I)
HOME_PATH = re.compile(r"(/Users/|/home/|[A-Za-z]:\\+Users\\+)(?!runner\b|USER\b|you\b|<)[A-Za-z0-9._-]+")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}")
ALLOWED_EMAIL = re.compile(r"^noreply@|@(example\.(com|org|net)|[^@\s]*\.(invalid|test|example)"
                           r"|users\.noreply\.github\.com)$", re.I)


def scan(root, paths):
    errors = []
    for rel in paths:
        if Path(rel).name in DIAGNOSTIC_NAMES:
            errors.append(f"{rel}: run diagnostics/logs must not be committed")
        if CREDENTIAL_FILE.search(rel):
            errors.append(f"{rel}: credential-style file must not be committed")
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if HOME_PATH.search(line):
                errors.append(f"{rel}:{number}: absolute home-directory path")
            for match in EMAIL.finditer(line):
                if not ALLOWED_EMAIL.search(match.group()):
                    errors.append(f"{rel}:{number}: email address {match.group()}")
    return errors


if __name__ == "__main__":
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    failures = scan(ROOT, [p for p in tracked.stdout.decode().split("\0") if p])
    print("\n".join(failures) if failures else "Privacy check passed.")
    sys.exit(bool(failures))
