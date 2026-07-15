#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Open a rendered ERP report when the local environment allows it.")
    ap.add_argument("html")
    args = ap.parse_args()
    path = Path(args.html).resolve()
    if not path.exists():
        print("OPEN_FAILED: file does not exist")
        raise SystemExit(1)
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=True)
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
        print("OPEN_OK")
    except Exception as exc:
        print(f"OPEN_FAILED: {exc}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
