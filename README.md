# AI-Based CI/CD Failure Self-Healing System

A complete end-to-end system that detects CI/CD pipeline failures, analyzes logs using Explainable AI, and automatically applies fixes with pipeline re-execution.

## 🛠 Architecture
- **CI/CD**: Jenkins (via Docker)
- **Backend API**: FastAPI (Python)
- **Database**: MongoDB
- **Explainable AI Engine**: Rule-based logic (easily extensible to Scikit-learn/ML models)
- **Dashboard**: Vanilla JS + HTML dashboard served by FastAPI

## 🚀 Setup Instructions

1. **Start the Environment**
   Open a terminal in this directory and run:
   ```bash
   docker-compose up -d --build
   ```

2. **Access the Services**
   - Dashboard & API: [http://localhost:8000](http://localhost:8000)
   - Jenkins: [http://localhost:8080](http://localhost:8080)
   
3. **Configure Jenkins**
   - Head to [http://localhost:8080](http://localhost:8080).
   - Get the initial password by opening a terminal and running:
     ```bash
     docker exec -it self-healing-cicd-jenkins-1 cat /var/jenkins_home/secrets/initialAdminPassword
     ```
   - Install suggested plugins.
   - Create an admin user.
   - Go to **Manage Jenkins -> Security -> Authorization**: Check **"Anonymous users can do anything"** temporarily for the demo to allow the backend API to easily trigger jenkins re-builds without complex token configurations. Click Save.
   
4. **Create the Jenkins Pipeline**
   - Click **New Item** -> Name it `sample-job` -> Select **Pipeline** -> Click OK.
   - Scroll down to the Pipeline section, select **Pipeline script from SCM**.
   - SCM: `Git`
   - Repository URL: `/workspace/sample-project` (Jenkins uses this mapped volume path)
   - Branches to build: Make sure it's `*/master`
   - Script Path: `Jenkinsfile`
   - Click Save.
   - **Important:** Make sure you ran `git init`, `git add .`, and `git commit -m "initial"` inside the `sample-project` directory from your host machine!

5. **Run the Demo**

   - **Scenario 1: Auto-Healing (Missing Dependency)**
     - Go to Jenkins, manually click **Build Now** on `sample-job`.
     - The build will fail because `requests` is missing from `requirements.txt`.
     - The Jenkinsfile automatically POSTs the logs to the Backend.
     - The AI determines it's a `ModuleNotFoundError` with 95% confidence!
     - The backend triggers the auto-fix script, which adds `requests` to `requirements.txt`.
     - The backend then **automatically triggers a new build** in Jenkins. You will see a second build start itself!
     - Check the Dashboard at [http://localhost:8000](http://localhost:8000) to see a comprehensive explanation of what happened!

   - **Scenario 2: Suggestion-only (Syntax Error)**
     - Edit `sample-project/app.py` and introduce a syntax error (e.g. `prnt("Test")`).
     - Commit the change via terminal: `cd sample-project && git commit -am "broken code"`.
     - Go to Jenkins and hit **Build Now**.
     - It fails. The AI engine catches the syntax error and explains it on the Dashboard, but skips auto-fixing because it's marked as unsafe (confidence < 0.8).

   - **Scenario 3: Suggestion-only (Test Failure)**
     - Fix the syntax error, but sabotage the unit test in `test_app.py` (e.g., `assert app.get_status() == "FAIL"`).
     - Commit and build.
     - The AI determines it's an `AssertionError` and tells you on the Dashboard what test failed!
