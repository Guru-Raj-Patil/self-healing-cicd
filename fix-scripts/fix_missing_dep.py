import sys
import os

def fix_missing_dependency(workspace, module_name):
    req_file = os.path.join(workspace, 'requirements.txt')
    
    # Simple heal: append the module name to requirements.txt
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            content = f.read()
            
        if module_name not in content:
            with open(req_file, 'a') as f:
                f.write(f"\n{module_name}\n")
            print(f"Successfully appended {module_name} to {req_file}")
        else:
            print(f"{module_name} is already in {req_file}")
    else:
        with open(req_file, 'w') as f:
            f.write(f"{module_name}\n")
        print(f"Created {req_file} and added {module_name}")

    # Try Git push
    import subprocess
    print("Initiating automated Git commit & push...")
    try:
        os.chdir(workspace)
        subprocess.run(["git", "config", "user.name", "AI Self-Healer"])
        subprocess.run(["git", "config", "user.email", "ai@self-healing.local"])
        subprocess.run(["git", "add", "requirements.txt"])
        subprocess.run(["git", "commit", "-m", f"AI Auto-heal: adding missing {module_name} dependency"])
        
        res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
        if res.returncode == 0:
            print("Successfully pushed auto-healed code to GitHub.")
        else:
            print(f"Git push failed (Tokens missing in docker container). Please push manually.")
    except Exception as e:
        print(f"Git automation encountered an error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: fix_missing_dep.py <workspace_path> <module_name>")
        sys.exit(1)
        
    ws_path = sys.argv[1]
    mod_name = sys.argv[2]
    
    fix_missing_dependency(ws_path, mod_name)
