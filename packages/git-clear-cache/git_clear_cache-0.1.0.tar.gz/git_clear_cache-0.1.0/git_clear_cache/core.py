import git, subprocess, os
from pathlib import Path
from typing import Optional, Union
from dotenv import dotenv_values
from pyundefined import undefined

PathLike = Union[Path, str]
PathNone = Optional[PathLike]
PathsType = Union[list[PathLike], tuple[PathLike], set(PathLike), PathLike]


class GitNotInstalledError(Exception):
    pass


class GitCacheRemover:
    def __init__(self, *paths: PathsType, repository_path: PathNone = None,
                 log_mode: bool = False, env_path: PathNone = None,
                 recursive: bool = False, force: bool = False):
        self.check_git_installed()
        self.paths = self.__paths(paths)
        self.repository_path = self.__repository_path(repository_path, env_path)
        self.repository = git.Repo(self.repository_path)
        self.recursive = recursive
        self.force = force
        # self.debug = debug
        self.log_mode = log_mode

    @staticmethod
    def __paths(paths):
        pre_output = list()
        output = list()
        for path in paths:
            if isinstance(path, PathLike):
                pre_output.append(Path(path))
            else:
                pre_output.extend([Path(p) for p in path])
        for path in pre_output:
            if path.exists():
                output.append(path)
        return output

    @staticmethod
    def __repository_path(repository_path: PathNone = None, env_path: PathNone = undefined) -> Path:
        if env_path is not undefined and repository_path is None:
            repository_path = Path(dotenv_values(env_path).get("REPOSITORY_PATH", None))
        return Path(repository_path).absolute() if repository_path is not None else Path.cwd()

    def log(self, *values, sep: str = ' ', end: str = '\n'):
        if self.log_mode:
            print(*values, sep=sep, end=end)

    def check_git_installed(self):
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True, check=True)
            self.log("Версия git:", result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise GitNotInstalledError("git не установлен")

    @property
    def files(self):
        output = []
        for path in self.paths:
            if path.is_file():
                output.append(path)
        return output

    @property
    def directories(self):
        output = []
        for path in self.paths:
            if path.is_dir():
                output.append(path)
        return output


    def run(self):
        if not self.repository.git_dir:
            raise git.InvalidGitRepositoryError("Директория не является репозиторием")
        args = ['--cached']

        if self.recursive:
            args.append('-r')
        if self.force:
            args.append('-f')

        args.extend(self.paths)
        self.repository.git.rm(*args)
        self.log(f"Файлы ({', '.join(self.files)}) удалены из кеша")
        self.log(f"Папки ({', '.join(self.directories)}) удалены из кеша")
