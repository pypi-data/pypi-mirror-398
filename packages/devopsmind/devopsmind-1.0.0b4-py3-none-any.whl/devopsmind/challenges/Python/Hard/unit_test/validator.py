import os
import importlib.util

def validate():
    if not os.path.exists("utils.py"):
        return False, "utils.py missing."

    try:
        spec = importlib.util.spec_from_file_location("utils", "./utils.py")
        utils = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(utils)
    except Exception as e:
        return False, f"Failed to import utils.py: {e}"

    if not hasattr(utils, "multiply"):
        return False, "Function multiply(a, b) is missing."

    tests = [
        (2, 3, 6),
        (-2, 5, -10),
        (0, 7, 0),
    ]

    for a, b, expected in tests:
        try:
            if utils.multiply(a, b) != expected:
                return False, f"multiply({a}, {b}) returned wrong result."
        except Exception as e:
            return False, f"Error calling multiply({a}, {b}): {e}"

    return True, "All tests passed!"
