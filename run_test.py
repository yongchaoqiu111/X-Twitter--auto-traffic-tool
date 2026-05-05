import subprocess
import sys

result = subprocess.run([sys.executable, 'test_all_imports.py'], 
                       capture_output=True, 
                       text=True, 
                       cwd='D:\\weibo\\X')

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
