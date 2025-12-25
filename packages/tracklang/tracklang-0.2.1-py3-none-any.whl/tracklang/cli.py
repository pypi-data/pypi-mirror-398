import sys
from .translator import translate


def main():
    if len(sys.argv) != 2:
        print("Usage: tracklang <file.tm>")
        sys.exit(1)

    path = sys.argv[1]

    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    python_code = translate(source)
    exec(python_code, {})


if __name__ == "__main__":
    main()
