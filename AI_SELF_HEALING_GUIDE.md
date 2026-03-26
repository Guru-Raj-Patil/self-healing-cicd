# AI-Based Self-Healing CI/CD System Guide

This guide explains how your self-healing CI/CD pipeline is currently built, how to test various pipeline failures, and how you can significantly enhance your AI model to make it more capable and autonomous.

---

## 1. System Architecture & How It Works

Your project orchestrates a complete lifecycle from code commit to failure analysis and resolution:

1. **Jenkins Pipeline (The Trigger):**
   When code is pushed, Jenkins automatically clones your repository and attempts to build/test it.
   - **If it passes (Green):** The pipeline succeeds, no errors are recorded, and the dashboard remains empty.
   - **If it fails (Red):** The `post { failure { ... } }` block in the Jenkinsfile activates. It runs a script to extract the raw build logs and sends them via an HTTP POST request to your FastAPI backend payload.

2. **FastAPI Backend (The Orchestrator):**
   The backend at `backend/main.py` receives the Jenkins logs. It then passes these logs to the AI Engine for analysis. Once analyzed, it stores the results (error string, confidence score, recommended fixes) in **MongoDB**.

3. **AI Engine (The Analyzer):**
   The `ai-engine/analyzer.py` parses the text logs. Currently, it uses a highly efficient, deterministic rule-based evaluation (using regex) to detect common Python errors like:
   - `ModuleNotFoundError` (Missing pip packages)
   - `SyntaxError` (Bad Python code)
   - `AssertionError` (Failing unit tests)

4. **Fix Scripts (The Healers):**
   If the AI Engine returns an error that is configured for "Auto-Heal" (e.g., `ModuleNotFoundError`) and the confidence score is high (>80%), the backend executes `fix-scripts/fix_missing_dep.py`. This script automatically modifies the developer's workspace to fix the issue (such as adding the missing package to `requirements.txt`). Finally, the backend attempts to automatically re-trigger the Jenkins pipeline to verify the fix.

5. **Analytical Dashboard:**
   Served via `dashboard/index.html`, this single-page app pulls the history from MongoDB. Any failure intercepted by the backend is displayed here along with the AI's explanation and recommended fix.

---

## 2. Testing Your Model (Failure Scenarios)

To fully stress-test the system, you must intentionally introduce failures to see how the AI responds to different categories of errors. 

### Scenario A: Auto-Heal Test (Missing Dependency)
This tests the full automated loop—the system will detect the error, modify files, and report success.
1. **Action:** Open `sample-project/requirements.txt` and delete the word `requests`. Commit and push to GitHub.
2. **Expected Result:**
   - Jenkins will fail at the "Build & Install" stage because `app.py` imports `requests` which is missing.
   - The AI Analyzer will detect `ModuleNotFoundError` with >90% confidence.
   - The backend will recognize this as an **Auto-Fixable** error and run the `fix_missing_dep.py` script.
   - The system will attempt to append `requests` back to `requirements.txt`.
   - The dashboard will show `fix_applied_successfully` or similar status.

### Scenario B: Manual Intervention Test (Broken Logic)
This verifies that the system correctly refuses to blindly alter application logic.
1. **Action:** Open `sample-project/test_app.py` and change the assertion to fail (e.g., `assert app.get_status() == "FAIL"`). Commit and push.
2. **Expected Result:**
   - Jenkins will fail at the `pytest` stage.
   - The AI Analyzer will detect `AssertionError` with a moderate confidence score.
   - The backend will return `manual_fix_required` because rewriting software logic auto-magically is too destructive to authorize. 
   - The dashboard will display the failure and suggest the developer review the failing test.

### Scenario C: Syntax Error Detection
1. **Action:** Break the syntax in `app.py` (e.g., remove a colon `:` from a function definition). Commit and push.
2. **Expected Result:**
   - Jenkins fails immediately when attempting to import the application.
   - Dashboard will flag a `SyntaxError` and provide the exact context to the developer.

---

## 3. How to Make the Best Possible Use of the "Model"

Right now, your AI is technically an "Expert System" pattern—meaning it works off rigid, hard-coded rules (`re.search("ModuleNotFoundError")`). While highly accurate and fast, it lacks the ability to understand novel, unstructured errors.

**Here is how you turn this into a truly intelligent self-healing system:**

### Phase 1: Integrate a Large Language Model (LLM) API
Instead of using Regex strings in `analyzer.py`, forward the Jenkins build logs to an LLM provider (e.g., OpenAI API, Anthropic, or a locally hosted model like `Ollama`).
* **Implementation:** Modify `analyzer.py` to send a prompt like:
  *"You are an expert DevOps engineer. Here are the Jenkins build logs. Respond with a JSON object containing `error_type`, `explanation`, `confidence_score`, and `exact_terminal_command_to_fix`."*
* **Benefit:** The system will dynamically understand complex errors like permissions, failing docker builds, networking timeouts, or complex dependency conflicts.

### Phase 2: Create a Sandboxed Shell Agent
Currently, you have exactly one hard-coded script (`fix_missing_dep.py`).
* **Implementation:** If your LLM returns a terminal command (e.g., `npm audit fix` or `chmod +x run.sh`), you can allow your backend to dynamically execute that shell command within the Jenkins Workspace.
* **Benefit:** Absolute autonomy to fix virtually any environment-based failure.

### Phase 3: Implement Automated Git Push
Currently, the fix scripts only modify the local Jenkins workspace. When Jenkins checks out the repo again, the fixes are lost.
* **Implementation:** Ensure your `fix_scripts` run standard Git commands after they alter a file:
  ```bash
  git config user.name "AI Self Healer"
  git commit -am "AI Automated Pipeline Fix"
  git push origin HEAD:main
  ```
* **Benefit:** True Self-Healing. The AI fixes code permanently and commits it back to the developer's repository, fully resolving the pipeline failure permanently.
