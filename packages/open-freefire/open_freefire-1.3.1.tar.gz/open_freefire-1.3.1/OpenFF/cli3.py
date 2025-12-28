import os

def main():
    # Get the path to this file
    path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"Error reading README.md: {e}")
