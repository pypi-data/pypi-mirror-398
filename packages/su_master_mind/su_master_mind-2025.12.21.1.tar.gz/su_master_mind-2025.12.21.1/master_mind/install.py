import logging
import shutil
import subprocess
import sys


def get_pip_command():
    """Detect and return the appropriate pip command (uv or pip)"""
    if shutil.which("uv"):
        return ["uv", "pip", "install"]
    return [sys.executable, "-m", "pip", "install"]


def install_courses(courses):
    """Install su_master_mind with the specified course extras

    Performs all pre-flight checks and then installs all courses in a single command.

    Args:
        courses: List of course names to install (e.g., ['rl', 'deepl'])
    """
    if not courses:
        logging.info("No courses to install")
        return

    # Deduplicate and sort courses
    unique_courses = sorted(set(courses))

    # Perform all pre-flight checks before installing
    # Check for swig if RL course is in the list
    if "rl" in unique_courses:
        if sys.platform == "win32":
            has_swig = shutil.which("swig.exe")
        else:
            has_swig = shutil.which("swig")

        if not has_swig:
            logging.error(
                "swig n'est pas installé: sous linux utilisez le "
                "gestionnaire de paquets:\n - sous windows/conda : "
                "conda install swig\n - sous ubuntu: sudo apt install swig"
            )
            sys.exit(1)

    # Build the package specification with extras
    extras = ",".join(unique_courses)
    package_spec = f"su_master_mind[{extras}]"

    # Get the pip command
    pip_cmd = get_pip_command()

    # Install the package with extras (single command for all courses)
    cmd = pip_cmd + [package_spec]
    logging.info(f"Installing courses {extras}: {' '.join(cmd)}")

    try:
        subprocess.check_call(cmd)
        logging.info(f"Successfully installed {package_spec}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install {package_spec}: {e}")
        sys.exit(1)
