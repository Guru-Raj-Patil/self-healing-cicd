import re

def preprocess_logs(logs: str) -> str:
    # Remove any Jenkins timestamps or known noise
    cleaned = re.sub(r'\[\d{4}-\d{2}-\d{2}T.*?\]', '', logs)
    return cleaned

def analyze_logs(logs: str) -> dict:
    cleaned_logs = preprocess_logs(logs)
    
    result = {
        "error_type": "Unknown",
        "confidence": 0.0,
        "keywords": [],
        "explanation": "Could not conclusively identify the error.",
        "recommended_fix": "Manual intervention required.",
        "module_name": None
    }
    
    # 1. ModuleNotFoundError
    if "ModuleNotFoundError" in cleaned_logs or "No module named" in cleaned_logs:
        match = re.search(r"No module named '(.+?)'", cleaned_logs)
        module_name = match.group(1) if match else "unknown"
        result.update({
            "error_type": "ModuleNotFoundError",
            "confidence": 0.95,
            "keywords": ["ModuleNotFoundError", "No module named"],
            "explanation": f"The build failed because the required Python module '{module_name}' is not installed.",
            "recommended_fix": f"pip install {module_name}",
            "module_name": module_name
        })
        return result
        
    # 2. SyntaxError
    if "SyntaxError" in cleaned_logs:
        result.update({
            "error_type": "SyntaxError",
            "confidence": 0.7,
            "keywords": ["SyntaxError", "invalid syntax"],
            "explanation": "There is a syntax error in the Python code.",
            "recommended_fix": "Fix the syntax error in the source code."
        })
        return result
        
    # 3. AssertionError (Test Failure)
    if "AssertionError" in cleaned_logs or "FAILED test_" in cleaned_logs:
        result.update({
            "error_type": "AssertionError",
            "confidence": 0.6,
            "keywords": ["AssertionError", "FAILED"],
            "explanation": "One or more unit tests failed an assertion.",
            "recommended_fix": "Review the failing test output and modify the code to pass the assertion."
        })
        return result

    return result
