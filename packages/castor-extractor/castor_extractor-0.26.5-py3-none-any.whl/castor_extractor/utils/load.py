from os import path as op


def load_file(path: str, calling_file: str) -> str:
    """Loads the given file using path relative to the calling file"""
    filepath = op.join(op.dirname(calling_file), path)
    with open(filepath) as f:
        return f.read()
