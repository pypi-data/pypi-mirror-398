#!/usr/bin/env python3
import os
import importlib.util
import sys

def validate():
    if not os.path.exists("calc.py"):
        return False, "calc.py is missing."

    try:
        spec = importlib.util.spec_from_file_location("calc", "./calc.py")
        calc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(calc)
    except Exception as e:
        return False, f"Failed to import calc.py: {e}"

    if not hasattr(calc, "add"):
        return False, "Function add(a, b) is missing in calc.py."

    try:
        res = calc.add(2, 3)
    except Exception as e:
        return False, f"Error calling add(): {e}"

    if res == 5:
        return True, "add(a, b) works correctly."
    else:
        return False, f"Expected add(2,3) to return 5 but got {res}."

