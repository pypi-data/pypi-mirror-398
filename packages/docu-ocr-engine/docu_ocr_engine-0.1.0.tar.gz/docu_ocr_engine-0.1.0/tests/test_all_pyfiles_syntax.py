import glob
import os
import py_compile


def test_all_py_files_syntax():
    # Find all .py files in the project (excluding _trash)
    root = os.path.dirname(os.path.dirname(__file__))
    py_files = [
        f
        for f in glob.glob(os.path.join(root, "**", "*.py"), recursive=True)
        if "_trash" not in f
    ]

    errors = []

    for f in py_files:
        try:
            py_compile.compile(f, doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{f}: {exc}")

    assert not errors, (
        "Syntax errors found:\n"
        + "\n".join(errors)
    )
