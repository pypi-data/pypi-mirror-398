# 🔪 dev-debt-scanner

**dev-debt-scanner** is a precision CLI tool designed to dissect your codebase and reveal hidden technical debt. It performs a deep-dive audit across **Python, JavaScript, HTML, and CSS** files to provide a comprehensive health report and security audit.
---

## 🚀 Features

dev-debt-scanner analyzes your project's "rot" using several advanced metrics:

* **Multi-Language Analysis:** Deep-dive support for `.py`, `.js`, `.html`, and `.css`.
* **Maintainability Index (MI):** A composite score indicating how easy your code is to support.
* **Cyclomatic Complexity:** Measures the number of linearly independent paths through your source code.
* **Security Audit:** Automatic detection of hardcoded **API Keys, Passwords, and Tokens**.
* **Git Insights:** Tracks **Churn** (modification frequency) to identify "danger zones" in your history.
* **Redundancy Detection:** Identifies duplicated code blocks that increase maintenance costs.
* **Risk Scoring:** A proprietary formula that ranks files from **LOW** to **CRITICAL** based on debt.

---

## 🛠 How to Run

### 1. Installation


1. Installation
   ```bash
   pip install dev-debt-scanner
   ```

2. Execution
   ```bash
   dev-debt .
   ```

3. Analyze a Specific Path
   ```bash
   dev-debt C:\Users\ravan\Desktop\my-other-project
   ```

##  Contributors

- [Visha Yadav](https://github.com/vishayadav) 
- [Viraj Ravani](https://github.com/v3ravani)


##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



