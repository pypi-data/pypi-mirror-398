"""Django's command-line utility for administrative tasks."""

import os
import platform
import random
import sys
from pathlib import Path

FNSCHOOL_PATH = Path(__file__).parent
if FNSCHOOL_PATH.as_posix() not in sys.path:
    sys.path.insert(0, FNSCHOOL_PATH.as_posix())

system_name = platform.system()
is_linux = False
is_windows = False
is_macos = False

if system_name == "Linux":
    is_linux = True
elif system_name == "Windows":
    is_windows = True
elif system_name == "Darwin":
    is_macos = True

sys_executable = sys.executable


def run_patches():
    if "202511012053_copy_profiles_to_fnprofile" in sys.argv:
        patche_path = (
            FNSCHOOL_PATH
            / "patches"
            / "202511012053_copy_profiles_to_fnprofile.py"
        )
        patche_path = patche_path.as_posix()
        os.system(f"{sys_executable} {patche_path} run")
        sys.exit()


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fnschool.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    os.chdir(FNSCHOOL_PATH)
    sys.argv[0] = "manage.py"

    run_patches()

    if len(sys.argv) < 2:
        local_port = "8230"
        local_url = "http://127.0.0.1:" + local_port
        sys.argv.append("runserver")
        sys.argv.append(str(local_port))

        if is_windows:
            os.startfile(local_url)
        else:
            os.system("open " + local_url + "&")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
