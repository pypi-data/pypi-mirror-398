#! /usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "cyclopts",
#     "niquests",
#     "wheel-filename",
# ]
# ///

import cyclopts
from hashlib import sha256
import logging
import niquests as requests
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
from urllib.parse import urlparse
# from wheel_filename import parse_wheel_filename


app = cyclopts.App()

@app.default
def build_wheels(
        lockfile: Path,
        destdir: Path = Path("/tmp/wheels"),
        python: str = "3.13",
        ) -> None:
    """Builds wheels for packages that are only available as sdist."""
    destdir.mkdir(0o750, parents=True, exist_ok=True)
    uvl = tomllib.load(open(lockfile, "rb"))
    for p in uvl["package"]:
        p_name = p["name"]
        if "wheels" not in p:
            print(f"no wheel for {p_name}")
            try:
                sdist = p["sdist"]
            except KeyError:
                print(f"no sdist for {p_name}")
                continue
            url = sdist["url"]
            hash = sdist["hash"]
            name = Path(urlparse(url).path).name
            
            # download url → name
            r = requests.get(url)
            if not r.ok:
                print(f"status {r.status_code} for download")
                continue
            
            # check hash
            s = sha256(r.content)
            r_hash = f"sha256:{s.digest().hex()}"
            if hash != r_hash:
                print(f"hash mismatch for package {name}")
                continue
            
            # save sdist source archive
            with open(name, "wb") as f:
                f.write(r.content)
                print(f"created {name}")
            
            # build wheel(s)
            sp = subprocess.run(["uv", "build", "--python", python, "--wheel",
                    name], check=True, capture_output=True)
            
            # discover built wheels and move to destination dir
            for whl in Path("dist").glob("*.whl"):
                destpath = destdir / whl.name
                if destpath.exists():
                    print(f"wheel {whl.name} exists, skipped")
                    whl.unlink()
                    # unfortunately it's hard to know beforehand if the
                    # (right!) wheel is already present;
                    # uv rebuilds, too, even if that wheel is present in dist/
                else:
                    shutil.move(whl, destdir)
                    print(f"moved wheel {whl.name} to {destdir}")

app()
