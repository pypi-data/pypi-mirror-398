import argparse
import sys

from ._util import (
    make_date_version,
    make_datetime_version,
    get_project_name,
    get_git_branch,
)
from ._find_image import find_image, find_local_image, find_remote_image


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subparser")
    p_find_image = subparsers.add_parser("find-image")
    p_find_image.add_argument("image_name")
    p_find_local_image = subparsers.add_parser("find-local-image")
    p_find_local_image.add_argument("local_image_name")
    p_find_remote_image = subparsers.add_parser("find-remote-image")
    p_find_remote_image.add_argument("remote_image_name")
    p_make_date_version = subparsers.add_parser("make-date-version")
    p_make_date_version = subparsers.add_parser("make-datetime-version")
    p_get_proj_name = subparsers.add_parser("get-project-name")
    p_get_git_branch = subparsers.add_parser("get-git-branch")
    args = parser.parse_args()

    cmd = args.subparser
    if cmd == "find-image":
        z = find_image(args.image_name)
        if z:
            print(z)
        else:
            sys.exit('Can not find image "%s"' % args.image_name)
    elif cmd == "find-local-image":
        z = find_local_image(args.local_image_name)
        if z:
            print(z)
        else:
            sys.exit('Can not find local image "%s"' % args.local_image_name)
    elif cmd == "find-remote-image":
        z = find_remote_image(args.remote_image_name)
        if z:
            print(z)
        else:
            sys.exit('Can not find remote image "%s"' % args.remote_image_name)
    elif cmd == "make-date-version":
        print(make_date_version())
    elif cmd == "make-datetime-version":
        print(make_datetime_version())
    elif cmd == "get-project-name":
        print(get_project_name())
    elif cmd == "get-git-branch":
        print(get_git_branch())
    else:
        sys.exit('Unknown sub-command "%s"' % cmd)
