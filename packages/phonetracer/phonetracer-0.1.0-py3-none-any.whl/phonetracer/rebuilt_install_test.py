import subprocess
import sys
import shutil
import glob
import os


def run(cmd, shell=False):
    print(f"\n>>> {cmd}")
    result = subprocess.run(
        cmd,
        shell=shell,
        text=True
    )
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    python = sys.executable

    # 1. Uninstall existing package (ignore failure)
    run([python, "-m", "pip", "uninstall", "phonetracer", "-y"])

    # 2. Clean build artifacts
    for path in ["dist", "build"]:
        if os.path.exists(path):
            print(f"Removing {path}/")
            shutil.rmtree(path)

    for egg in glob.glob("*.egg-info"):
        print(f"Removing {egg}")
        shutil.rmtree(egg)

    # 3. Build package
    run([python, "-m", "build"])

    # 4. Install the newly built wheel
    wheels = glob.glob("dist/*.whl")
    if not wheels:
        print("❌ No wheel found in dist/")
        sys.exit(1)

    run([python, "-m", "pip", "install", wheels[0]])

    # 5. Test CLI
    print("\n=== Running phonetracer CLI ===")
    run(["phonetracer"], shell=True)


if __name__ == "__main__":
    main()
