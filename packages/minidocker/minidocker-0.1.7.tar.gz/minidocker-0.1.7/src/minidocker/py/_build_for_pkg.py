import os
import string
import subprocess
import argparse
import shutil


from .._util import get_project_name, run_command, get_git_branch
from ._util import (
    parse_pyproject,
)


DOCKER_SRCDIR = "/tmp/src"
# Copy project repo to this location in the image.

PYPROJECT = parse_pyproject()
PROJ = get_project_name()
try:
    PKG = PYPROJECT['tool']['flit']['module']['name']
except KeyError:
    PKG = PYPROJECT['project']['name'].lower().replace('-', '_')

def dev_dockerfile(*, parent, docker_srcdir):
    t = string.Template("""\
FROM ${PARENT}
USER root

ENV PARENT_IMAGE=${PARENT}

# If the repo needs non-Python dependencies, will need a mechanism
# to insert a block to install other things, or use user-defined Dockerfile.

# Install the package of the current repo along with all its required and optional
# dependencies. Then, uninstall the project package itself,
# leaving the dependencies in place. The source code is left in the image in order to run tests;
# otherwise it will be largely forgotten.
# Dev and test within the container will use volume-mapped live code.

COPY --chown=docker-user:docker-user . ${DOCKER_SRCDIR}

RUN pip-install ${DOCKER_SRCDIR}/[${EXTRAS}] \\
    && python -m pip uninstall -y ${NAME} \\
    && rm -rf ${DOCKER_SRCDIR}

USER docker-user
""")

    pyproj = PYPROJECT["project"]
    name = pyproj["name"]
    try:
        deps = pyproj["optional-dependencies"]
        extras = ",".join(deps.keys())
    except KeyError:
        extras = ""

    return t.substitute(
        PARENT=parent, DOCKER_SRCDIR=docker_srcdir, EXTRAS=extras, NAME=name
    )


def build_dev(*, parent, tag):
    dockerfile = dev_dockerfile(parent=parent, docker_srcdir=DOCKER_SRCDIR)
    run_command(
        ["docker", "build", "--no-cache", "-t", tag, "-f", "-", "."],
        input=dockerfile.encode(),
    )


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", required=True, help="full tag of parent image")
    args, more_args = parser.parse_known_args(args)

    return vars(args), more_args


def build(args):
    kwargs, extra_args = parse_args(args)
    devimg = PROJ + ":dev"
    build_dev(parent=kwargs["parent"], tag=devimg)
    branch = get_git_branch()
    if branch in ("main", "master", "release"):
        run_command(["bash", ".githooks/pre-commit"])
        run_command(
            [
                "docker",
                "run",
                "--rm",
                "-e",
                "IMAGE_NAME=" + PROJ,
                "-e",
                "IMAGE_VERSION=dev",
                "-e",
                "PKG=" + PKG,
                "-e",
                "PROJ=" + PROJ,
                "--workdir",
                DOCKER_SRCDIR,
                "-e",
                "PYTHONPATH=" + DOCKER_SRCDIR + "/src",
                *extra_args,
                devimg,
                "py.test",
                "--cov={}".format(PKG),
                "tests",
            ]
        )
        if branch == "release":
            try:
                shutil.rmtree("dist")
            except FileNotFoundError:
                pass
            subprocess.run(["docker", "rm", PROJ + "-release"], capture_output=True)
            run_command(
                [
                    "docker",
                    "run",
                    "--workdir",
                    DOCKER_SRCDIR,
                    "--name",
                    PROJ + "-release",
                    devimg,
                    "python",
                    "-m",
                    "build",
                    ".",
                ]
            )
            run_command(
                ["docker", "cp", "{}-release:{}/dist".format(PROJ, DOCKER_SRCDIR), "./"]
            )
            run_command(["docker", "rm", PROJ + "-release"])
            print('Release artifacts are saved in "dist/"')
            # Successful release will create a `dist/*.tar.gz` and a `dist/*.whl`.
            # Outside of Docker, upload the package to PyPI by
            #   $ python3 -m twine upload dist/*
    else:
        # Take a free ride to config githooks.
        # Do this only when in a development branch.
        if not os.path.isfile(".githooks/pre-commit"):
            # pkg_root = importlib.util.find_spec(__name__.split(".")[0]).origin
            # hook_file = os.path.join(
            # os.path.dirname(pkg_root), "githooks", "pre-commit"
            # )
            try:
                os.mkdir(".githooks")
            except FileExistsError:
                pass
            # shutil.copyfile(hook_file, ".githooks/pre-commit")
            with open(".githooks/pre-commit", "w") as file:
                file.write("""\
#!/usr/bin/env bash

# Run in a subshell so that directory changes do not take effect for the user.
(
    thisfile="${BASH_SOURCE[0]}"
    cd "$(dirname "${thisfile}")"
    cd ..
    bash <(curl -s https://raw.githubusercontent.com/zpz/minidocker/main/src/minidocker/py/githooks/pre-commit) $@
)
""")
            run_command(["chmod", "+x", ".githooks/pre-commit"])
            run_command(["git", "config", "--local", "core.hooksPath", ".githooks/"])
