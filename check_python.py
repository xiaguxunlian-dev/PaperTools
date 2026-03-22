import subprocess, sys
result = subprocess.run(
    ['python', '--version'],
    capture_output=True, text=True,
    shell=True
)
print(result.stdout or result.stderr)
