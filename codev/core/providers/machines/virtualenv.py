from contextlib import contextmanager

from codev.core.machines import BaseMachine
from codev.core.settings import SettingsError, BaseSettings


class DirectoryBaseMachine(BaseMachine):

    def _get_base_dir(self):
        return '~/.share/codev/virtualenv/{ident}/'.format(ident=self.ident.as_file())

    def exists(self):
        return self.inherited_executor.exists_directory(self._get_base_dir())

    def create(self):
        self.inherited_executor.execute(
            'mkdir -p {}'.format(self._get_base_dir())
        )

    def execute_command(self, command):
        command = command.change_directory(
            self._get_base_dir()
        )
        return super().execute_command(command)

    @contextmanager
    def get_fo(self, remote_path):
        with self.change_directory(self._get_base_dir()):
            with super().get_fo(remote_path) as fo:
                yield fo


class VirtualenvBaseMachineSettings(BaseSettings):
    @property
    def python_version(self):
        python_version = self.data.get('python', None)
        if not python_version:
            return 3
        elif python_version == '2' or python_version.startswith('2.'):
            return python_version
        else:
            raise SettingsError('Unsupported python version for virtualenv isolation.')


class VirtualenvBaseMachine(DirectoryBaseMachine):
    settings_class = VirtualenvBaseMachineSettings

    def exists(self):
        return self.inherited_executor.exists() and self.inherited_executor.exists_directory('env')

    def create(self):
        self.inherited_executor.create()

        python_version = self.settings.python_version
        self.inherited_executor.execute('virtualenv -p python{python_version} env'.format(
            python_version=python_version
        ))

    def is_started(self):
        return True

    def destroy(self):
        self.inherited_executor.execute('rm -rf env')

    def execute_command(self, command):
        command = command.wrap(
            'source env/bin/activate && {command}'
        )
        return super().execute_command(command)
