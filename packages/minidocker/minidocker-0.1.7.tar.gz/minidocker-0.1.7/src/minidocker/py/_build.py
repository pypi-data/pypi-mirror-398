import pathlib

from . import _build_for_pkg, _build_for_proj


def main(args):
    if pathlib.Path("docker").is_dir():
        _build_for_proj.build(args)
    else:
        _build_for_pkg.build(args)
