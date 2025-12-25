import os
import sys
import subprocess
import argparse
import platform
import shutil

VENV = ".venv"

def is_windows():
    return platform.system() == "Windows"

def py():
    """Return path to venv python executable"""
    if is_windows():
        return os.path.join(VENV, "Scripts", "python.exe")
    return os.path.join(VENV, "bin", "python")

def pip():
    """Return path to venv pip executable"""
    if is_windows():
        return os.path.join(VENV, "Scripts", "pip.exe")
    return os.path.join(VENV, "bin", "pip")

def exec(cmd):
    """Execute a subprocess command, failing if it errors"""
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

def init(args):
    """Initialize the environment: create venv, upgrade pip, install reqs"""
    print(f"checking {VENV}...")
    if not os.path.exists(VENV):
        print(f"creating virtualenv at {VENV}...")
        subprocess.run([sys.executable, "-m", "venv", VENV], check=True)
    else:
        print(f"{VENV} already exists.")

    print("upgrading pip...")
    # Use the venv's python to run pip to avoid path issues on some platforms
    exec([py(), "-m", "pip", "install", "--upgrade", "pip"])

    if not args.no_req and os.path.exists("requirements.txt"):
        print("installing requirements.txt...")
        exec([pip(), "install", "-r", "requirements.txt"])
    
    print("✨ pylax environment ready.")

def run(args):
    """Run a command inside the venv"""
    if not os.path.exists(py()):
        print(f"Error: {VENV} not found. Run 'pylax init' first.")
        sys.exit(1)
        
    # args.command is a list, e.g. ['app.py'] or ['python', 'app.py']
    # If the first arg is not a path to an executable in venv (like 'python' or 'pip'), 
    # we assume python execution if it ends in .py, OR we just run it directly.
    # The user manual says "pylax run app.py" -> .venv/bin/python app.py
    
    cmd = args.command
    if not cmd:
        return

    # Special handling: if command starts with 'python' or 'pip', map to venv versions
    # actually, purely based on user request: "pylax run app.py" -> "python app.py" logic
    # But usually 'run' commands might be arbitrary.
    # The mental model: "A friendly dispatcher".
    # If I type 'pylax run foo.py', I expect 'python foo.py' using venv python.
    # If I type 'pylax run pip list', I expect 'pip list' using venv pip.
    
    prog = cmd[0]
    rest = cmd[1:]

    target_executable = prog

    # Auto-resolve common python tools to the venv versions if they exist
    if prog == "python" or prog == "python3":
        target_executable = py()
    elif prog == "pip" or prog == "pip3":
        target_executable = pip()
    elif prog.endswith(".py"):
        # Implicitly run with python if it's a script file
        target_executable = py()
        rest = [prog] + rest
    else:
        # Check if the executable exists in the venv bin/Scripts dir
        venv_bin = os.path.dirname(py())
        potential_path = os.path.join(venv_bin, prog)
        if os.path.exists(potential_path):
            target_executable = potential_path
            
    exec([target_executable] + rest)

def shell(args):
    """Spawn a shell with venv bin in path"""
    if not os.path.exists(py()):
        print(f"Error: {VENV} not found. Run 'pylax init' first.")
        sys.exit(1)

    venv_bin = os.path.dirname(py())
    
    # Copy current environment
    env = os.environ.copy()
    
    # Prepend venv bin to PATH
    old_path = env.get("PATH", "")
    env["PATH"] = f"{venv_bin}{os.pathsep}{old_path}"
    
    # Set VIRTUAL_ENV legacy variable so prompts might pick it up
    env["VIRTUAL_ENV"] = os.path.abspath(VENV)
    # Remove PYTHONHOME if it exists to avoid conflicts
    env.pop("PYTHONHOME", None)

    # Determine shell to run
    shell_cmd = os.environ.get("SHELL", "bash")
    if is_windows():
        shell_cmd = os.environ.get("COMSPEC", "cmd.exe")

    print(f"Spawning shell interactively with {VENV} in PATH...")
    try:
        cmd = [shell_cmd]
        # For zsh/bash, we might not drastically change prompt without sourcing activate,
        # but the PATH is correct.
        subprocess.run(cmd, env=env)
    except Exception as e:
        print(f"Error spawning shell: {e}")

def main():
    parser = argparse.ArgumentParser(prog="pylax", description="Zero-friction Python environment orchestrator")
    subparsers = parser.add_subparsers(dest="subcommand", help="Command to run")

    # init
    parser_init = subparsers.add_parser("init", help="Initialize/update the .venv")
    parser_init.add_argument("--no-req", action="store_true", help="Skip installing requirements.txt")
    
    # run
    parser_run = subparsers.add_parser("run", help="Run a script or command in the venv")
    parser_run.add_argument("command", nargs=argparse.REMAINDER, help="Script or command to run")

    # shell
    parser_shell = subparsers.add_parser("shell", help="Spawn a shell within the venv")

    args = parser.parse_args()

    if args.subcommand == "init":
        init(args)
    elif args.subcommand == "run":
        run(args)
    elif args.subcommand == "shell":
        shell(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
