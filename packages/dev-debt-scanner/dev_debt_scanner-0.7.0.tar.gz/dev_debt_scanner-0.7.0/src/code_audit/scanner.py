import os
from .analyzer import FileAnalyzer
from .reporter import print_table

def run_audit(root_dir):
    results = []
    # Simplified extensions
    exts = ('.py', '.html', '.htm', '.js', '.txt', '.css')
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(exts):
                full_path = os.path.join(root, file)
                # Fixed: Match the new __init__ signature
                analyzer = FileAnalyzer(full_path)
                res = analyzer.get_metrics()
                if res:
                    results.append(res)
    
    results.sort(key=lambda x: x['risk'], reverse=True)
    print_table(results)