from io import StringIO
from pathlib import Path
from pyinfra import host
from pyinfra.facts.files import Directory, File, Link
from pyinfra.operations import apt, files, server, ssh, systemd
from pyinfra_timezone import TimezoneSetting, timezone
import subprocess
from textwrap import dedent
import yaml

from options import deb, dj, web, gen


##################################################################


DJ_USER = "esc"
DJ_HOME = Path("/home") / DJ_USER

# Django options
dj = SN(
    user = DJ_USER,
    home = str(DJ_HOME),
    proj = str(DJ_HOME / "django"),
    venvs = str(DJ_HOME / "venvs"),
    venv_dft = str(DJ_HOME / "venvs" / "default"),
    venv_active = str(DJ_HOME / "venvs" / "active"),
    wheels = str(DJ_HOME / "wheels"),
    wheelhouse_active = str(DJ_HOME / "wheels" / "active"),
    logs = str(DJ_HOME / "logs"),
    ext_res = str(DJ_HOME / "django" / "static_external" / "external"),
    py_version = "3.12",
    )

# Web options
web = SN(
    server_fullname = "www.esc-duesseldorf.de",
    server_basename = "esc-duesseldorf.de",
    app_basedir = dj.proj,
    logdir = dj.logs,
    )

# General options
gen = SN(
    uv_path = "/usr/local/bin/uv",
    )


##################################################################


def get_program_path(cmd: str) -> str:
    """Returns path object for local command."""
    for line in subprocess.getoutput(f"type {cmd}").splitlines():
        words = line.split()
        if len(words) == 3 and words[1] == "is":
            return words[2]
    return ""


# --- Prepare venv management

files.put(
        name="Copy uv tool",
        src=get_local_path("uv"),
        dest=gen.uv_path,
        user="root",
        group="staff",
        mode="755",
        add_deploy_dir=False,
        )

# --- Django: log dir

files.directory(
        name="Create Django log dir",
        path=dj.logs,
        user=dj.user,
        mode="750",
        )

# # conditionally create django_q logs dir XXX

# --- Django: other dirs

files.directory(
        name=f"Create Django subdir {dj.private}",
        path=dj.private,
        user=dj.user,
        mode="750",
        )
for d in (dj.ext_res + "/css", dj.ext_res + "/js", dj.ext_res + "/fonts"):
    files.directory(
            name=f"Create Django subdir {d}",
            path=d,
            user=dj.user,
            mode="751",
            )


# --- Django: make venv

if not host.get_fact(Directory, dj.venv_dft):
    server.shell(
            name="Prepare a standard virtual env for the application",
            commands=[f"uv venv --python {dj.py_version} --prompt {dj.py_version}.std {dj.venv_dft}"],
            )
    server.shell(
            name="Populate the standard virtual env",
            commands=[f"VIRTUAL_ENV={dj.venv_dft} uv pip install django gunicorn"],
            )

if not host.get_fact(Link, dj.venv_active):
    files.link(
            name="Create directory for venvs",
            path="default",
            target=f"{dj.venv_active}",
            force=False,
            force_backup=False,
            )

# --- Django: create gunicorn service

service = files.template(
        name="Create systemd service for gunicorn",
        src="templates/gunicorn.unit.jj",
        dest=f"/etc/systemd/system/{dj.user}.service",
        user="root", group="root", mode="644", create_remote_dir=False,
        var_project="escweb",
        var_module="news",
        dj=dj,
        )
systemd.service(
        name="Run systemd service for gunicorn",
        service="esc",
        enabled=True,
        running=True,
        )

# # conditionally create django_q service XXX
