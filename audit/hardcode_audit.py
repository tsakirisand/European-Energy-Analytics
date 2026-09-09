import os
import re

def run_hardcode_audit():
    print("==================================================")
    print("HARD-CODE AUDIT — EUROPEAN ENERGY ANALYTICS")
    print("==================================================")
    
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    suspicious_patterns = [
        re.compile(r'renewable_share\s*=\s*\d+(\.\d+)?', re.IGNORECASE),
        re.compile(r'germany\s*renewables?\s*=\s*\d+', re.IGNORECASE),
        re.compile(r'greece\s*generation\s*=\s*\d+', re.IGNORECASE),
        re.compile(r'total_gwh\s*=\s*\d{4,}', re.IGNORECASE),
        re.compile(r'fake_' + r'data|sample_' + r'data', re.IGNORECASE)
    ]

    violations = []
    
    for dirpath, _, filenames in os.walk(root_dir):
        if "venv" in dirpath or ".git" in dirpath or "raw" in dirpath or "__pycache__" in dirpath:
            continue
        for fname in filenames:
            if fname.endswith(".py") or fname.endswith(".sql"):
                fpath = os.path.join(dirpath, fname)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        for pat in suspicious_patterns:
                            if pat.search(line):
                                violations.append((fpath, idx, line.strip()))

    print(f"Total Source Code Files Scanned.")
    if violations:
        print(f"❌ FAIL: Found {len(violations)} suspicious hardcoded factual numbers:")
        for v in violations:
            print(f"  {v[0]}:{v[1]} -> {v[2]}")
        return False
    else:
        print("✅ PASS: 0 hardcoded factual numbers found in source codebase!")
        print("==================================================")
        return True

if __name__ == "__main__":
    run_hardcode_audit()
