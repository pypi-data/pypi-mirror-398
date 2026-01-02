import sys
import os
from .scanner import run_audit

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    if not os.path.exists(path):
        print(f"Error: Path {path} not found.")
        sys.exit(1)
    
    print(f"\n--- AUDITING: {os.path.abspath(path)} ---")
    run_audit(path)

if __name__ == "__main__":
    main()