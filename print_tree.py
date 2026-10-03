import os

IGNORE = {"venv", ".venv", "node_modules", "__pycache__", ".git"}

def walk(root, prefix=""):
    entries = [e for e in os.listdir(root) if e not in IGNORE]
    entries.sort()
    for i, name in enumerate(entries):
        path = os.path.join(root, name)
        last = (i == len(entries) - 1)
        connector = "└── " if last else "├── "
        print(prefix + connector + name)
        if os.path.isdir(path):
            ext = "    " if last else "│   "
            walk(path, prefix + ext)

print(".")
walk(".")
