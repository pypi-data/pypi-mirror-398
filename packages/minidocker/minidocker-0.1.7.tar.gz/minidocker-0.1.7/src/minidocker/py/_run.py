import getpass
import pathlib
import platform
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .._util import run_command


def parse_args(args):
    imagename = None
    cmd = "bash"  # the command to be run within the container
    cmdargs = []  # args to `command`
    opts = []  # args to `docker run`
    nb_port = 8888
    # gpu_devices=all
    gpu_devices = None

    # You can specify specific GPUs to use, e.g.
    # -e NVIDIA_VISIBLE_DEVICES=none
    # -e NVIDIA_VISIBLE_DEVICES=0,1,3
    # -e NVIDIA_VISIBLE_DEVICES=all

    # To restrict memory usage, do something like
    # --memory=8g
    # Default is unlimited.
    #
    # See https://georgeoffley.com/blog/shared-memory-in-docker.html

    # Parse arguments.
    # There are two sets of arguments: those before image-name, and those after.
    # For those before, some are parsed; the rest are forwarded to `docker run` as is.
    # For those after, the first is the command to be executed within the container;
    # the rest are arguments to the command.
    while args:
        head = args.pop(0)
        if head == "-v":
            # volume mapping, e.g.
            #   -v /tmp/data:/home/docker-user/data
            opts.extend([head, args.pop(0)])
        elif head == "-p":
            # Port forwarding, e.g.
            #   -p 8080:8080
            opts.extend([head, args.pop(0)])
        elif head == "-e":
            # Set env var, e.g.
            #   -e MYNAME=abc
            val = args.pop(0)
            if head.startswith("NVIDIA_VISIBLE_DEVICES="):
                gpu_devices = val.lstrip("NVIDIA_VISIBLE_DEVICES=")
            else:
                opts.extend([head, val])
        elif head == "--nb_port":
            # Port number for Jupyter Notebook.
            # Use this to avoid "port is being used" error.
            nb_port = args.pop(0)
        elif head.startswith("--nb_port="):
            nb_port = head.lstrip("--nb_port=")
        elif head.startswith("-"):
            # Every other argument is captured and passed on to `docker run`.
            # For example, if there is an option called `--volume` which sets
            # something called 'volume', you may specify it like this
            #
            #   --volume=30
            #
            # You can not do
            #
            #   --volume 30
            #
            # because `run-docker` does not explicitly capture this option,
            # hence it does not know this option has two parts.
            # The same idea applies to other options.
            opts.append(head)
        else:
            imagename = head
            if args:
                cmd = args[0]
                cmdargs = args[1:]
            break

    if not imagename:
        usage = """\
Usage:

run-docker [options] <image-name>[:tag] [<cmd> [cmd-args]]

where

`image-name` is either the a source repo name (optionally with appended ":dev") in `~/work/src/` or the full image name (with path and tag).

`cmd` is the command to be run within the container, followed by arguments to the command.
(Default: bash)
"""
        raise Exception("image name is missing.\n" + usage)

    return {
        "imagename": imagename,
        "cmd": cmd,
        "cmdargs": cmdargs,
        "opts": opts,
        "nb_port": nb_port,
        "gpu_devices": gpu_devices,
    }


def main(args):
    kwargs = parse_args(args)
    imagename = kwargs["imagename"]
    imageversion = None
    name = ""  # container's name
    IMAGENAME = None
    command = kwargs["cmd"]
    args = kwargs["cmdargs"]  # args to `command`
    opts = kwargs["opts"]  # args to `docker run`
    nb_port = kwargs["nb_port"]
    gpu_devices = kwargs["gpu_devices"]

    HOSTWORKDIR = pathlib.Path.home() / "work"
    DOCKERHOMEDIR = "/home/docker-user"
    host_user = getpass.getuser()
    host_os = platform.system()
    host_ip = socket.gethostbyname(socket.gethostname())

    if ":" not in imagename and "/" not in imagename:
        # The image name is a single word: no namespace, no tag.
        # If it is the name of a repo in `~/work/src/`, then
        # use the local dev image for the repo.
        # The image must have been built previously using
        # the script `run` in the repo directory.
        if (HOSTWORKDIR / "src" / imagename).is_dir():
            # It is a source repo.
            imagename = imagename + ":dev"
        else:
            raise Exception(
                'Cannot find source directory "{}" for image "{}"'.format(
                    HOSTWORKDIR / 'src' / imagename,
                    imagename,
                )
            )

    if imagename.endswith(":dev"):
        # 'dev' is a special tag used by local dev images.
        IMAGENAME = imagename
        imagename = IMAGENAME.rstrip(":dev")  # remove the ':dev" tag
        imageversion = "dev"
        PROJ = imagename

        HOSTSRCDIR = HOSTWORKDIR / 'src' / PROJ
        if not HOSTSRCDIR.is_dir():
            raise Exception(
                'Cannot find source directory "{}" for image "{}:dev"'.format(
                    HOSTSRCDIR,
                    imagename,
                )
            )

        DOCKERSRCDIR = f"{DOCKERHOMEDIR}/{PROJ}"
        if platform.system() == "Windows":
            # On Windows, convert the path to a form that Docker can understand.
            # See https://www.google.com/search?q=docker+run+volume+mapping+does+not+work+in+git-bash+terminal+on+windoes&oq=docker+run+volume+mapping+does+not+work+in+git-bash+terminal+on+windoes&gs_lcrp=EgRlZGdlKgYIABBFGDkyBggAEEUYOTIHCAEQ6wcYQNIBCTIwMTAzajBqMagCALACAA&sourceid=chrome&ie=UTF-8
    
            d = HOSTSRCDIR.drive
            p = HOSTSRCDIR.as_posix().lstrip(d)
            hostsrcdir = f"/{d.rstrip(':').lower()}{p}"
        else:
            hostsrcdir = str(HOSTSRCDIR)
        opts.extend(
            [
                "-v",
                f"{hostsrcdir}:{DOCKERSRCDIR}",
                f"--workdir={DOCKERSRCDIR}",
            ]
        )
        opts.extend(["-e", f"PYTHONPATH={DOCKERSRCDIR}/src"])
    else:
        # `imagename` is the full name.
        IMAGENAME = imagename

        imageversion = IMAGENAME[
            (IMAGENAME.index(":") + 1) :
        ]  # remove the longest substr from front
        imagename = IMAGENAME[
            : IMAGENAME.index(":")
        ]  # remove the shortest substr from back
        imagename = imagename[
            : imagename.rfind("/")
        ]  # remove namespace, keeping the last word only
        PROJ = ""

    # `IMAGENAME` is the full name including url, namespace, etc.
    # ${IMAGENAME}=[namespace.../]${imagename}:${imageversion}
    # `$imagename` contains neither namespace nor tag.

    DATAVOLUME = "docker-data-volume"
    MOUNTPOINT = "{}/mnt".format(DOCKERHOMEDIR)
    opts.extend(["--mount", "source={},target={}".format(DATAVOLUME, MOUNTPOINT)])

    if not args and command in (
        "/bin/bash",
        "/bin/sh",
        "/usr/bin/bash",
        "/usr/bin/sh",
        "bash",
        "sh",
        "python",
        "ptpython",
        "ptipython",
        "ipython",
    ):
        opts.append("-it")

    if not any(v.startswith("--name=") for v in opts):
        # User did not specify a name for the container.
        name = "{}-{}-utc".format(
            host_user, datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        )
        opts.append("--name={}".format(name))

    if not any(v.startswith("--shm-size=") for v in opts):
        # User did not specify shared memory size.
        opts.append("--shm-size=2gb")

    if not any(v.startswith("--restart=") for v in opts) and "-d" not in opts:
        opts.append("--rm")
        # User did not specify '--restart=' or '-d'

    if gpu_devices is not None:
        if subprocess.run(["which", "nvidia-smi"]).returncode == 0:
            opts.extend(
                [
                    "--runtime=nvidia",
                    "-e",
                    "NVIDIA_VISIBLE_DEVICES={}".format(gpu_devices),
                ]
            )
            # or --gpus=all ?
            # TODO: look into the option `--gpus` to `docker run`.

    opts.extend(
        [
            "-e",
            "HOST_OS=" + host_os,
            "-e",
            "HOST_USER=" + host_user,
            "-e",
            "HOST_IP=" + host_ip,
        ]
    )

    if command == "notebook":
        opts.extend(
            [
                "--expose=" + nb_port,
                "-p",
                "{}:{}".format(nb_port, nb_port),
                "-e",
                "JUPYTER_DATA_DIR={}/tmp/.jupyter/data".format(MOUNTPOINT),
                "-e",
                "JUPYTER_RUNTIME_DIR={}/tmp/.jupyter/runtime".format(MOUNTPOINT),
                "-e",
                "JUPYTERLAB_WORKSPACES_DIR={}/tmp/.jupyter/workspaces".format(
                    MOUNTPOINT
                ),
                "-e",
                "JUPYTERLAB_SETTINGS_DIR={}/tmp/.jupyter/settings".format(MOUNTPOINT),
            ]
        )
        # command="jupyter lab --port={} --no-browser --ip=0.0.0.0 --NotebookApp.notebook_dir='{}/{}' --NotebookApp.token=''".format(nb_port, DOCKERHOMEDIR, PROJ)
        command = "jupyter lab --port={} --no-browser --ip=0.0.0.0 --NotebookApp.token=''".format(
            nb_port
        )

    opts.extend(
        [
            "--user=docker-user",
            "-e",
            "IMAGE_NAME=" + imagename,
            "-e",
            "IMAGE_VERSION=" + imageversion,
            "-e",
            "TZ=America/Los_Angeles",
            "--init",
        ]
    )

    run_command(["docker", "run"] + opts + [IMAGENAME, command] + args)
