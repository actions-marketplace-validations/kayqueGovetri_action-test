import os
import pathlib
from argparse import Namespace


class Build:
    def __init__(self, args: Namespace):
        self._args = args

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, args: Namespace):
        if not isinstance(args, Namespace):
            raise ValueError(f"Value is not a Namespace")
        self._args = args

    def run(self):
        file_name = self.get_file_name()

        sh = self.get_sh(file_name=file_name)

        self.set_permission(sh=sh)

        path = pathlib.Path(self.args.path)

        file_path = self.get_file_path(path=path)

        self.set_command(sh=sh, file_path=file_path, path=path)

        return file_path

    def get_file_name(self):
        technology = self.args.technology.upper()

        if not technology:
            raise Exception(f"Technology {technology} not found.")

        file_name = f"{technology.lower()}.sh"

        return file_name

    def get_sh(self, file_name: str):
        sh = os.path.join(os.path.abspath('build'), file_name)
        print(f'SH is = {sh}')
        return sh

    def set_permission(self, sh: str):
        os.system(command=f'chmod +x {sh}')

    def get_file_path(self, path: pathlib.Path):
        if not path.is_dir():
            raise Exception(f"Not found path: {path}")

        file_path = f"{pathlib.Path().absolute()}/bot.zip"

        return file_path

    def set_command(self, sh: str, path: pathlib.Path, file_path: str):
        command = f'{sh} -p "{path}" -a "{file_path}"'
        print(command)
        os.system(command=command)