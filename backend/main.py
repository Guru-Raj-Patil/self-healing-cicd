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
        
        try:
            result = subprocess.run(
                ["python3", fix_script, workspace, module_name],
                capture_output=True, text=True, check=True
            )
            update_status(record_id, "fix_applied_successfully", result.stdout)
            
            # Use Jenkins API without authentication (assuming anonymous build is enabled)
            # or configure Jenkins to allow remote builds with a specific token.
            # In a local demo, since we control jenkins, we will trigger it.
            # If CSRF is enabled, this might need a crumb, but let's try a simple POST.
            try:
                # We can also use Jenkins CLI or standard POST
                jen_url = f"http://jenkins:8080/job/{job_name}/build"
                r = requests.post(jen_url)
                print(f"Triggered jenkins: {r.status_code}")
            except Exception as e:
                print(f"Failed to trigger jenkins: {e}")
                
        except subprocess.CalledProcessError as e:
            update_status(record_id, "fix_failed", e.stderr)
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
        return f.read()
