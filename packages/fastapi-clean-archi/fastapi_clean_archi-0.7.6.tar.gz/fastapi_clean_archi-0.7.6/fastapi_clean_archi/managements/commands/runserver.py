import importlib
import os

import typer
import uvicorn

from fastapi_clean_archi.managements.commands.base import Command, validate_database_url


class Runserver(Command):
    name = "runserver"
    help = "FastAPI server 가 실행됩니다."

    def execute(self,
                host_port=typer.Argument("localhost:8000", help="호스트와 포트를 지정합니다. 예: localhost:8000"),
                settings_env=typer.Option(".env", "--settings-env")):
        host, port = host_port.split(":")

        os.environ.setdefault("SETTINGS_ENV", settings_env)
        try:
            module = importlib.import_module("app.core.config")
            settings = module.settings.dict()
        except ModuleNotFoundError:
            raise ModuleNotFoundError("app.core.config 모듈을 찾을 수 없습니다.")

        if not settings["DATABASE_URL"] or not validate_database_url(settings["DATABASE_URL"]):
            raise ConnectionError("데이터베이스에 연결할 수 없습니다. DATABASE_URL 설정을 확인해주세요.")

        app_name = settings["APP_NAME"]
        print(f"{app_name}")
        uvicorn.run("main:app", host=host, port=int(port), reload=True)
