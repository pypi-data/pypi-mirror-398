"""
Run all unittests written in dostest style.
"""

# Import standard libraries.
import doctest
import importlib
import pathlib


def run_all_unittests():
    """
    Run all unittests written in doctest style.
    """
    # Loop for all Python script files.
    for path in sorted(pathlib.Path("yadopt").glob("*.py")):

        # Ignore Python files that starts with "_" (e.g. __init__.py).
        if path.name.startswith("_"):
            continue

        # Import Python file as a module.
        target = path.with_suffix("").name
        module = importlib.import_module(f"yadopt.{target}")

        # Run all the test inside the module.
        n_failed, n_total = doctest.testmod(module, name="Unittest", report=True)

        # Exit if filed at least test.
        if n_failed > 0:
            exit(-1)

        print(f"=> module={target}, n_total={n_total}, n_failed={n_failed}")


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
