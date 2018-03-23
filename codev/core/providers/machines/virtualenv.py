from contextlib import contextmanager
from typing import IO

from codev.core.executor import Command
from codev.core.machines import BaseMachine
from codev.core.settings import BaseSettings


class DirectoryBaseMachine(BaseMachine):

    def _get_base_dir(self) -> str:
        return '~/.share/codev/virtualenv/{ident}/'.format(ident=self.ident.as_file())

    def exists(self) -> bool:
        return self.executor.exists_directory(self._get_base_dir())

    def create(self) -> None:
        self.executor.create_directory(self._get_base_dir())

    def execute_command(self, command: Command) -> str:
        command = command.change_directory(
            self._get_base_dir()
        )
        return super().execute_command(command)

    @contextmanager
    def open_file(self, remote_path: str) -> IO:
        with self.change_directory(self._get_base_dir()):
            with super().open_file(remote_path) as fo:
                yield fo


class VirtualenvBaseMachineSettings(BaseSettings):
    @property
    def python_version(self) -> str:
        return str(self.data.get('python', 3))


class VirtualenvBaseMachine(BaseMachine):
    settings_class = VirtualenvBaseMachineSettings
    executor_class = DirectoryBaseMachine
    executor_class_forward = ['ident']

    def exists(self) -> bool:
        return self.executor.exists() and self.executor.exists_directory('env')

    def create(self) -> None:
        self.executor.create()

        python_version = self.settings.python_version
        self.executor.execute(f'virtualenv -p python{python_version} env')
        # FIXME pip install -U pip

    def is_started(self) -> bool:
        return True

    def destroy(self) -> None:
        self.executor.delete_path('env')

    def execute_command(self, command: Command) -> str:
        command = command.wrap(
            'source env/bin/activate && {command}'
        )
        return super().execute_command(command)
