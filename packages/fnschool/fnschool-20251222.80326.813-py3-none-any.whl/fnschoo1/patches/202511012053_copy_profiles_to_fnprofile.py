import os
import shutil
import sqlite3
import sys
from pathlib import Path

file_path = Path(__file__)
data_path = Path(file_path.with_suffix("").as_posix() + "_data")
data_name = data_path.stem

patches_path = file_path.parent
fnscho1_path = patches_path.parent

settings_temp_path = data_path / "settings.py"
profiles_path = data_path / "profiles"

src_path = fnscho1_path.parent
db_path = fnscho1_path / "db.sqlite3"

patch_name = file_path.stem
settings_temp_name = f"patches.{data_name}.settings"

conn = sqlite3.connect(db_path.as_posix())
cursor = conn.cursor()
cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
    ("fnprofile_fnuser",),
)
fnprofile_fnuser_exists = cursor.fetchone() is not None
conn.close()

sys_executable = sys.executable


def run():
    if fnprofile_fnuser_exists:
        print(('Patch "{0}" had been applied successfully!').format(patch_name))
        return

    os.system(
        ("{0} manage.py migrate --settings {1}").format(
            sys_executable, settings_temp_name
        )
    )
    os.system(
        ("{0} manage.py makemigrations --settings {1}").format(
            sys_executable, settings_temp_name
        )
    )
    print(('Patch "{0}" applied successfully!').format(patch_name))


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <function_name>")
        sys.exit(1)

    func_name = sys.argv[1]

    function_dict = {
        "run": run,
    }

    if func_name in function_dict:
        function_dict[func_name]()
    else:
        print(f'Error: Function "{func_name}" not found.')


if __name__ == "__main__":
    main()
