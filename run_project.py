"""One-command runner for the complete portfolio analytics case study."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

result = subprocess.run(
    [sys.executable, str(SRC / "finalize_project.py")],
    cwd=SRC,
    check=False,
)

if result.returncode != 0:
    raise SystemExit(result.returncode)

print("\nProject run completed successfully.")
print(f"Reports and charts: {ROOT / 'outputs'}")
