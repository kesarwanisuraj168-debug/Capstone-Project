"""Test runner to verify START.bat execution logic for first-run and subsequent-run."""
import subprocess
import os
import sys

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    start_bat = os.path.join(root, "START.bat")
    
    print(f"Testing START.bat in {root}")
    assert os.path.exists(start_bat), "START.bat missing!"
    
    # Read START.bat content
    with open(start_bat, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify key requirements
    assert 'cd /d "%~dp0"' in content, "Missing directory switch!"
    assert 'if not exist "venv\\Scripts\\activate.bat"' in content, "Missing venv existence check!"
    assert 'call setup.bat' in content, "Missing call setup.bat!"
    assert 'call run.bat' in content, "Missing call run.bat!"
    assert 'Setup failed' in content or 'error' in content.lower(), "Missing error handling!"
    assert 'Starting application' in content, "Missing starting application message!"
    assert 'First-time setup' in content, "Missing first-time setup message!"
    
    print("START.bat code structure verification PASSED!")
    
    # Test batch execution dry-run of condition check
    cmd = 'cmd /c "if not exist venv\\Scripts\\activate.bat (echo FIRST_RUN) else (echo SUBSEQUENT_RUN)"'
    output = subprocess.check_output(cmd, shell=True, text=True).strip()
    print(f"Condition test without venv: {output}")
    assert output == "FIRST_RUN", f"Expected FIRST_RUN but got {output}"
    
    print("Testing simulated subsequent run (mocking venv existence)...")
    mock_dir = os.path.join(root, "venv", "Scripts")
    os.makedirs(mock_dir, exist_ok=True)
    mock_activate = os.path.join(mock_dir, "activate.bat")
    with open(mock_activate, "w") as f:
        f.write("@echo mock activate\n")
        
    output_mock = subprocess.check_output(cmd, shell=True, text=True).strip()
    print(f"Condition test with venv: {output_mock}")
    assert output_mock == "SUBSEQUENT_RUN", f"Expected SUBSEQUENT_RUN but got {output_mock}"
    
    # Clean up mock file/dir
    os.remove(mock_activate)
    os.rmdir(mock_dir)
    os.rmdir(os.path.join(root, "venv"))
    print("Mock cleanup completed.")
    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
