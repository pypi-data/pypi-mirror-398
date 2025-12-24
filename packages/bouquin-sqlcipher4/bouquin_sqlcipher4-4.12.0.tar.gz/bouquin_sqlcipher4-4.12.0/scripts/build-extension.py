from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]

    env = os.environ.copy()
    env.setdefault("BOUQUIN_SYSTEM_OPENSSL", "1")

    # Build the extension in-place so the .so/.pyd lands under sqlcipher4/
    subprocess.check_call([sys.executable, "setup.py", "build_ext", "--inplace"], cwd=root, env=env)

    # Sanity check: did we actually produce the native module?
    pkg = root / "sqlcipher4"
    built = list(pkg.glob("_sqlite3*.so")) + list(pkg.glob("_sqlite3*.pyd"))
    if not built:
        raise SystemExit("Extension build produced no sqlcipher4/_sqlite3*.so or .pyd. Check setup.py output.")
    print("Built:", ", ".join(p.name for p in built))


if __name__ == "__main__":
    main()

