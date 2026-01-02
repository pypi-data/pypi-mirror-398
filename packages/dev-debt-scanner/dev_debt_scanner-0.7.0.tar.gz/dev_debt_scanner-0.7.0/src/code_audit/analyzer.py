import os
import re

class FileAnalyzer:
    SECRET_PATTERNS = {
        "API Key": r"(?i)(api_key|apikey|api-key)[\s]*[:=][\s]*['\"][\w-]{16,}['\"]",
        "Password": r"(?i)(password|passwd|pwd)[\s]*[:=][\s]*['\"](?![^'\"]*example)[^'\"]{4,}['\"]",
    }

    def __init__(self, filepath): # Fixed: Only 2 args (self, filepath)
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

    def calculate_grade(self, mi):
        if mi > 80: return "A"
        if mi > 60: return "B"
        if mi > 40: return "C"
        if mi > 20: return "D"
        return "F"

    def get_metrics(self):
        try:
            with open(self.filepath, 'r', errors='ignore') as f:
                lines = f.readlines()
        except: return None

        content = "".join(lines)
        loc = len(lines)
        
        # 1. Cyclomatic Complexity
        complexity = len(re.findall(r'\b(if|elif|for|while|with|except|case|default)\b', content))
        
        # 2. Dependency Count
        deps = len(re.findall(r'^(import\s|from\s)', content, re.MULTILINE))
        
        # 3. Duplication (repeated lines > 20 chars)
        seen_lines = set()
        dupes = 0
        for l in lines:
            trimmed = l.strip()
            if len(trimmed) > 20:
                if trimmed in seen_lines: dupes += 1
                seen_lines.add(trimmed)
        dup_ratio = round((dupes / loc * 100), 1) if loc > 0 else 0

        # 4. Maintainability Index
        mi = max(0, min(100, 100 - (complexity * 3) - (loc / 40) - (deps * 2)))
        grade = self.calculate_grade(mi)

        # Leaks
        leaks = []
        for line_num, line_content in enumerate(lines, 1):
            for label, pattern in self.SECRET_PATTERNS.items():
                if re.search(pattern, line_content):
                    leaks.append(f"{label}(L{line_num})")

        risk = (complexity * 0.8) + (deps * 1.5) + (dup_ratio * 0.5) + (80 if leaks else 0)

        return {
            "file": self.filename, "loc": loc, "grade": grade,
            "comp": complexity, "deps": deps, "dup": f"{dup_ratio}%",
            "mi": int(mi), "risk": round(risk, 1), "leaks_count": len(leaks),
            "factor": f"LEAK: {leaks[0]}" if leaks else ("Complex" if complexity > 15 else "Healthy")
        }