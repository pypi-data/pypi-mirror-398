# fabriq/wardrobe/runner.py
import os
import sys
import subprocess

def main():
    script_path = os.path.join(os.path.dirname(__file__), "chat_ui.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", script_path])

if __name__ == "__main__":
    main()