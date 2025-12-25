# run_unimeth.py
import subprocess

if __name__ == "__main__":
    subprocess.run(["accelerate", "launch", "unimeth/unimeth.py"])