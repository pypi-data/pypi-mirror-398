try:
    import tomllib as toml
except ImportError:
    import toml


def parse_pyproject():
    return toml.load(open("pyproject.toml", "rb"))
