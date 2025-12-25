import subprocess
import sys
from pathlib import Path

def test_cli_runs_example_yaml():
    repo_root = Path(__file__).resolve().parents[1]
    yaml_path = repo_root / "examples" / "suites" / "orders_dq.yml"
    cmd = [sys.executable, "-m", "sparkdq.cli.main", "run", "--yaml", str(yaml_path),
           "--format", "text",]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "DQ Suite" in (proc.stdout + proc.stderr)