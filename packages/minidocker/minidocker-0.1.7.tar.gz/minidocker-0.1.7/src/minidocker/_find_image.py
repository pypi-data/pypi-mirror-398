import subprocess
from ._util import run_command_for_output


def find_local_image(name):
    # Find the latest tag of an image on local disk,
    # assuming tags are sortable.
    # The sole input is the name of the image, with repository as needed,
    # e.g.
    #     debian
    #     zppz/py3

    if ":" in name:
        if run_command_for_output(["docker", "images", "-q", name]):
            # Exists locally.
            return name

    tags = run_command_for_output(
        ["docker", "image", "ls", name, "--format", '"{{.Tag}}"']
    )
    if not tags:
        return None

    tags = [v.strip('"') for v in tags.split("\n")]
    if "latest" in tags:
        return name + ":latest"

    # Assume tags are named based on datetime; take the latest.
    return name + ":" + max(tags)


def find_remote_image(name):
    NAME = name
    if ":" in NAME:
        tag = NAME.split(":")[-1]
        name = NAME.rstrip(":" + tag)
        url = "https://hub.docker.com/v2/repositories/{}/tags/{}/".format(name, tag)
        if run_command_for_output(["curl", "--silent", "-f", "--head", "-lL", url]):
            # Exists remotely.
            return NAME

    url = "https://hub.docker.com/v2/repositories/{}/tags/".format(NAME)
    try:
        tags = run_command_for_output(["curl", "--silent", "-f", "-lL", url])
    except subprocess.CalledProcessError:
        return None

    tags = (
        tags.replace("{", "")
        .replace("}", "")
        .replace("[", "")
        .replace("]", "")
        .split(",")
    )
    tags = [v for v in tags if '"name"' in v]
    if tags:
        tags = [v.replace('"', "").lstrip("name:") for v in tags]
        return NAME + ":" + max(tags)

    return None


def find_image(name):
    tag_local = find_local_image(name)
    tag_remote = find_remote_image(name)
    if tag_local:
        if tag_remote and tag_remote > tag_local:
            return tag_remote
        return tag_local
    elif tag_remote:
        return tag_remote
    else:
        return None
