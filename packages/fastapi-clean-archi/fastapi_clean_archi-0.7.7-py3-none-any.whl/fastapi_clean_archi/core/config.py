import os

from pydantic.v1 import BaseSettings


class AbstractSettings(BaseSettings):
    DATABASE = {
        "driver": "sqlite",
        "name": "sqlite.db",
        "user": "",
        "password": "",
        "host": "",
        "port": "",
    }

    @property
    def DATABASE_URL(self) -> str:
        db = self.DATABASE
        if db["driver"] == "sqlite":
            return f"{db['driver']}:///{db['name']}"
        return (
            f"{db['driver']}://{db['user']}:{db['password']}"
            f"@{db['host']}:{db['port']}/{db['name']}"
        )

    def export(self):
        data = self.dict()
        data["DATABASE_URL"] = self.DATABASE_URL
        return data

    class Config:
        env_file = os.environ.get("SETTINGS_ENV", ".env")
