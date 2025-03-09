import subprocess
import sys
import os

def install_requirements():
    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        print("requirements.txt not found!")
        sys.exit(1)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print("Error during installation:", e)
        sys.exit(1)

if __name__ == "__main__":
    install_requirements()
