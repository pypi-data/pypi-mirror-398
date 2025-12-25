import importlib

def check_dependency(package, install_cmd=None, guidance="on"):
    """
    Check if a dependency is installed.
    If not installed, prints a friendly warning.

    Example:
        check_dependency("sklearn", "pip install scikit-learn")
    """

    spec = importlib.util.find_spec(package)

    if spec is None:
        if guidance == "on":
            print("⚠️ Missing dependency:", package)
            if install_cmd:
                print(f"   → Install with: `{install_cmd}`")
            print("--------------------------------------------------")
        return False

    return True


def check_core_dependencies(guidance="on"):
    """
    Check the essential dependencies for prepstack.
    """

    missing_any = False

    required = {
        "pandas": "pip install pandas",
        "numpy": "pip install numpy",
        "matplotlib": "pip install matplotlib",
        "scipy": "pip install scipy",
    }

    for pkg, cmd in required.items():
        ok = check_dependency(pkg, cmd, guidance)
        if not ok:
            missing_any = True

    if guidance == "on":
        if not missing_any:
            print("✅ All core dependencies available.")
        print("--------------------------------------------------")

    return not missing_any


def check_ml_dependencies(guidance="on"):
    """
    Dependencies required for modeling & feature selection.
    """

    required = {
        "sklearn": "pip install scikit-learn",
    }

    missing_any = False

    for pkg, cmd in required.items():
        ok = check_dependency(pkg, cmd, guidance)
        if not ok:
            missing_any = True

    if guidance == "on":
        if not missing_any:
            print("✅ ML dependencies available.")
        print("--------------------------------------------------")

    return not missing_any
