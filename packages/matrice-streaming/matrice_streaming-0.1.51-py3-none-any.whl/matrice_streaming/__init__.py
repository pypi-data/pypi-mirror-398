"""Module providing __init__ functionality."""
import multiprocessing

# Only run dependency checks in the main process, NOT in spawned child processes
# (ProcessPoolExecutor workers). Child processes re-import modules which would
# trigger pip install commands, causing crashes with BrokenProcessPool errors.
_is_main_process = multiprocessing.parent_process() is None

if _is_main_process:
    from matrice_common.utils import dependencies_check

    base = [
        "httpx",
        "fastapi", 
        "uvicorn",
        "pillow",
        "confluent_kafka[snappy]",
        "aiokafka",
        "aiohttp",
        "filterpy",
        "scipy",
        "scikit-learn", 
        "matplotlib",
        "scikit-image",
        "python-snappy",
        "pyyaml",
        "imagehash",
        "psutil"
    ]

    # Install base dependencies first
    dependencies_check(base)

    # Helper to attempt installation and verify importability
    def _install_and_verify(pkg: str, import_name: str):
        """Install a package expression and return True if the import succeeds."""
        if dependencies_check([pkg]):
            try:
                __import__(import_name)
                return True
            except ImportError:
                return False
        return False

    if not dependencies_check(["opencv-python"]):
        dependencies_check(["opencv-python-headless"])
