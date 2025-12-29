import os
from importlib import resources
from pathlib import Path

import typer

from fastapi_clean_archi.managements.commands.base import Command, copy_files, copy_file, edit_file

template_dir = resources.files("fastapi_clean_archi.managements.templates")


class AddModule(Command):
    name = "add_module"
    help = "구조화된 모듈을 추가합니다."

    def execute(self, module_name=typer.Argument(...)):
        class_name = module_name.capitalize()
        module_name = module_name.lower()

        copy_files(source_dir=Path(f"{template_dir}/app_module"),
                   target_dir=Path(f"./app/modules/{module_name}"),
                   module_name=module_name,
                   module_class=class_name)

        if not os.path.exists("./app/modules/__init__.py"):
            copy_file(file_path=Path(f"{template_dir}/__init__.tmpl"),
                      new_file_path=Path("./app/modules/__init__.py"))
        print(f"✅ Module '{module_name}' has been created successfully.")