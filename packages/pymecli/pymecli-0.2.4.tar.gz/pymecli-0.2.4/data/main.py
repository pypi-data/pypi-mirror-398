from pathlib import Path

if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parent.parent
    print(module_dir)
