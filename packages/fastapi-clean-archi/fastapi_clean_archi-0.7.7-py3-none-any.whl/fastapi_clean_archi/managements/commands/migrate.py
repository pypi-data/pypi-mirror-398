from fastapi_clean_archi.managements.commands.base import run_alembic, Command


class Migrate(Command):
    name = "migrate"
    help = "db migration 을 진행합니다."

    def execute(self):
        run_alembic("alembic upgrade head")
