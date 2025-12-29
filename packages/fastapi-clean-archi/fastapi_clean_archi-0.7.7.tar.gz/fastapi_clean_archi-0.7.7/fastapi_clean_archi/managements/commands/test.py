import subprocess

import typer

from fastapi_clean_archi.managements.commands.base import Command


class Test(Command):
    name = "test"
    help = "테스트를 실행합니다."

    def execute(self,
                module_name=typer.Argument("", help="테스트 대상 모듈 이름"),
                test_name=typer.Argument("", help="테스트 파일 및 함수 이름. ex) filename, filename::function_name 형식으로 입력")):
        if not module_name and test_name:
            raise typer.BadParameter("모듈 이름이 필요합니다.")

        specific_params = ""
        if test_name:
            test_filename, *test_function_name = test_name.split("::")
            if not test_filename.endswith(".py"):
                test_filename = f"{test_filename}.py"
            test_function_name = test_function_name and test_function_name[0]
            specific_params = f"{test_filename}::{test_function_name}" if test_function_name else test_filename

        params = f"app/modules/{module_name}/tests/{specific_params}" if module_name else ""

        command = f"pytest {params}".strip()
        subprocess.run(command, shell=True)
        print(f"Pytest Command is \"{command}\"")
