import abc
import os
import subprocess
from abc import ABC
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def validate_database_url(database_url: str) -> bool:
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


class Command(ABC):
    name: str = None
    help: str = None

    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError


def edit_file(filename, remove_line_words, add_lines, line_number):
    path = Path(filename)
    lines = path.read_text().splitlines()

    for index in range(len(lines)):
        for x in remove_line_words:
            if lines[index].startswith(x):
                lines[index] = ""
    if line_number >= 0:
        path.write_text("\n".join(lines[:line_number] + add_lines + lines[line_number:]))
    else:
        path.write_text("\n".join(lines + add_lines))


def run_alembic(alembic_command: str):
    subprocess.run(alembic_command.split(" "))


def copy_file(file_path, new_file_path, **kwargs):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read().format(**kwargs)

    with open(new_file_path, 'w', encoding='utf-8') as f:
        f.write(data)
    print(f"✅ Created {file_path}")


def copy_files(source_dir, target_dir, **kwargs):
    for file_path in source_dir.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(source_dir)
            relative_path = relative_path.with_suffix(".py")
            new_file_path = target_dir / relative_path

            if os.path.isfile(new_file_path):
                print(f"⚠️  {file_path} already exists, skipping")
                continue

            new_file_path.parent.mkdir(parents=True, exist_ok=True)
            copy_file(file_path, new_file_path, **kwargs)
