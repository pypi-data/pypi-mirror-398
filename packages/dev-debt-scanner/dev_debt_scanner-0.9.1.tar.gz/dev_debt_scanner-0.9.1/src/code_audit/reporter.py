def print_table(data):
    if not data:
        print("No supported files found to audit.")
        return

    header = f"{'FILE':<18} {'GRD':<4} {'LOC':<6} {'COMP':<5} {'DEP':<4} {'DUP%':<7} {'MI':<4} {'RISK':<6} {'FACTOR'}"
    print("\n" + header)
    print("-" * len(header))
    
    total_risk = 0
    total_leaks = 0
    grades = []

    for r in data:
        print(f"{r['file']:<18} [{r['grade']}]  {r['loc']:<6} {r['comp']:<5} {r['deps']:<4} {r['dup']:<7} {r['mi']:<4} {r['risk']:<6} {r['factor']}")
        total_risk += r['risk']
        total_leaks += r['leaks_count']
        grades.append(r['mi'])

    # --- Summary Section (New Feature) ---
    avg_mi = sum(grades) / len(grades)
    avg_risk = total_risk / len(data)
    
    # Calculate Project Grade
    if avg_mi > 80: project_grade = "A (Healthy)"
    elif avg_mi > 50: project_grade = "B/C (Needs Cleanup)"
    else: project_grade = "D/F (High Debt)"

    print("-" * len(header))
    print(f"SUMMARY STATISTICS:")
    print(f"  > Project Health Grade: {project_grade}")
    print(f"  > Average File Risk:    {avg_risk:.1f}")
    print(f"  > Critical Leaks Found: {total_leaks}")
    print(f"  > Files Audited:        {len(data)}")
    print("-" * len(header))