from logging import getLogger

from .deployment import Deployment

from .infrastructure import Infrastructure
from .performer import CommandError, ScriptExecutor
from .debug import DebugSettings

logger = getLogger(__name__)


class Configuration(ScriptExecutor):
    def __init__(self, settings, **kwargs):
        performer = kwargs['performer']
        self.settings = settings

        self.performer = LocalPerformer()  # TODO

        self.infrastructure = Infrastructure(performer, self.settings.infrastructure)
        super().__init__(performer=self.performer)

    def deploy(self, status, input_vars):
        status.update(self.status)

        input_vars.update(DebugSettings.settings.load_vars)

        logger.info("Deploying project.")

        scripts = self.settings.scripts

        try:
            self.execute_scripts(scripts.onstart, status)

            deployment = Deployment(self.settings.provisions, performer=self.performer)
            deployment.deploy(self.infrastructure, status, input_vars)

        except CommandError as e:
            self.execute_scripts_onerror(scripts.onerror, status, e, logger=logger)
            return False
        else:
            try:
                self.execute_scripts(scripts.onsuccess, status)
                return True
            except CommandError as e:
                self.execute_scripts_onerror(scripts.onerror, status, e, logger=logger)
                return False

    def execute_script(self, script, arguments=None, logger=None):
        if arguments is None:
            arguments = {}

        arguments.update(self.status)
        return super().execute_script(script, arguments=arguments, logger=arguments)

    @property
    def status(self):
        """
        Information about configuration (and isolation if exists)
        :return: configuration status
        :rtype: dict
        """
        infrastructure_status = self.infrastructure.status

        status = dict(
            infrastructure=infrastructure_status
        )

        return status
