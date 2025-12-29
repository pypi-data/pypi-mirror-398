import subprocess

def run(cmd, check=True) -> None:
    subprocess.run(cmd, check=check)

def check(cmd) -> bool:
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False
