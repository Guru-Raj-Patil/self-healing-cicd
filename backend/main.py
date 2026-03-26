from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
from database import init_db, save_analysis, get_history, update_status
from fastapi.responses import HTMLResponse
import sys
import os
import subprocess
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '../ai-engine'))
from analyzer import analyze_logs

app = FastAPI(title="CI/CD Self-Healing API")

class LogPayload(BaseModel):
    job_name: str
    build_number: str
    workspace: str
    logs: str

@app.on_event("startup")
async def startup_event():
    init_db()

def apply_fix_and_retrigger(record_id: str, analysis: dict, workspace: str, job_name: str):
    error_type = analysis.get("error_type")
    
    if error_type == "ModuleNotFoundError" and analysis.get("confidence", 0) > 0.8:
        module_name = analysis.get("module_name")
        if not module_name or module_name == "unknown":
            update_status(record_id, "fix_failed", "No specific module name identified.")
            return

        print(f"Applying auto-fix for {module_name} in {workspace}")
        
        fix_script = os.path.join(os.path.dirname(__file__), '../fix-scripts/fix_missing_dep.py')
        
        steps_taken = [
            "Intercepted failed pipeline logs from Jenkins webhook.",
            f"AI Analyzer confidently identified '{error_type}'.",
            f"Determined missing dependency required: '{module_name}'.",
            "Executed workspace intervention script 'fix_missing_dep.py'."
        ]
        
        try:
            # We pass /workspace/sample-project because it maps to the user's host repo root.
            # This allows the fix to alter the source code and push to GitHub, rather than just the Jenkins sandbox.
            result = subprocess.run(
                ["python3", fix_script, "/workspace/sample-project", module_name],
                capture_output=True, text=True, check=True
            )
            steps_taken.append(f"Script output: {result.stdout.strip()}")
            
            try:
                # Use environment variables for authentication to avoid hardcoding
                jen_user = os.getenv("JENKINS_USER", "admin")
                jen_token = os.getenv("JENKINS_TOKEN", "AUTO_HEAL_TOKEN")
                
                jen_url = f"http://jenkins:8080/job/{job_name}/build?token={jen_token}"
                r = requests.post(jen_url, auth=(jen_user, jen_token))
                print(f"Triggered jenkins: {r.status_code}")
                if r.status_code in [200, 201]:
                    steps_taken.append(f"Successfully re-triggered Jenkins job '{job_name}' to verify the fix.")
                else:
                    steps_taken.append(f"Attempted to trigger Jenkins but received HTTP {r.status_code}.")
            except Exception as e:
                print(f"Failed to trigger jenkins: {e}")
                steps_taken.append("Could not reach Jenkins immediately to re-trigger the job.")
                
            update_status(record_id, "fix_applied_successfully", result.stdout, fix_steps=steps_taken)
            
        except subprocess.CalledProcessError as e:
            steps_taken.append(f"Fix script failed with error: {e.stderr.strip()}")
            update_status(record_id, "fix_failed", e.stderr, fix_steps=steps_taken)
            print(f"Fix script failed: {e.stderr}")
    else:
        update_status(record_id, "manual_fix_required", "Confidence too low or error type not auto-fixable.")

@app.post("/analyze")
async def analyze(payload: LogPayload, background_tasks: BackgroundTasks):
    analysis_result = analyze_logs(payload.logs)
    
    record_id = save_analysis(
        payload.job_name, 
        payload.build_number, 
        payload.workspace,
        analysis_result["error_type"],
        analysis_result["confidence"],
        analysis_result["keywords"],
        analysis_result["explanation"],
        analysis_result["recommended_fix"]
    )
    
    if analysis_result["confidence"] > 0.8:
        background_tasks.add_task(
            apply_fix_and_retrigger, str(record_id), analysis_result, payload.workspace, payload.job_name
        )
    else:
        update_status(str(record_id), "recommendation_only")
        
    return {
        "status": "success",
        "record_id": str(record_id),
        "analysis": analysis_result
    }

@app.get("/history")
async def history():
    return get_history()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open(os.path.join(os.path.dirname(__file__), '../dashboard/index.html'), 'r') as f:
        return f.read(
