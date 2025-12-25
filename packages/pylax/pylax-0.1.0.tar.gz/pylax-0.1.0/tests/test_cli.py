import os
import shutil
import subprocess
import sys
import pytest

# Ensure we can import pylax
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pylax.cli import init, run, py as get_py

TEST_ENV = "test_env"

@pytest.fixture
def clean_env():
    """Setup and teardown a clean test environment"""
    # Use a custom VENV name for tests would require patching VENV in cli.py
    # or running in a temp dir. Let's run in a temp dir.
    orig_cwd = os.getcwd()
    tmp_dir = os.path.join(orig_cwd, TEST_ENV)
    
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    os.chdir(tmp_dir)
    
    yield tmp_dir
    
    os.chdir(orig_cwd)
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

def test_init_creates_venv(clean_env):
    """Test that init command creates .venv"""
    # Call init via subprocess to simulate CLI usage
    # We use subprocess to test the actual entry point mechanism if installed,
    # but since it's not installed, we run module.
    
    cmd = [sys.executable, "-m", "pylax.cli", "init", "--no-req"]
    subprocess.run(cmd, check=True)
    
    assert os.path.exists(".venv")
    assert os.path.exists(os.path.join(".venv", "bin", "python")) or \
           os.path.exists(os.path.join(".venv", "Scripts", "python.exe"))

def test_run_executes_script(clean_env):
    """Test that run command executes a script with venv python"""
    # First init
    subprocess.run([sys.executable, "-m", "pylax.cli", "init", "--no-req"], check=True)
    
    # Create a test script
    with open("check_py.py", "w") as f:
        f.write("import sys; print(sys.executable)")
        
    # Run it via pylax
    result = subprocess.run(
        [sys.executable, "-m", "pylax.cli", "run", "check_py.py"], 
        capture_output=True, 
        text=True, 
        check=True
    )
    
    # Verify the output path contains .venv
    assert ".venv" in result.stdout

def test_run_dispatches_pip(clean_env):
    """Test that pylax run pip dispatches to venv pip"""
    subprocess.run([sys.executable, "-m", "pylax.cli", "init", "--no-req"], check=True)
    
    result = subprocess.run(
        [sys.executable, "-m", "pylax.cli", "run", "pip", "--version"],
        capture_output=True,
        text=True,
        check=True
    )
    
    assert ".venv" in result.stdout
