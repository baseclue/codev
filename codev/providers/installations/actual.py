from os import unlink

from codev.configuration import YAMLConfiguration
from codev.installation import Installation, BaseInstallation


class ActualInstallation(BaseInstallation):
    def install(self, performer):
        YAMLConfiguration.from_configuration(self.configuration).save_to_file('tmp')
        performer.send_file('tmp', '.codev')
        unlink('tmp')
        return self.configuration


Installation.register('actual', ActualInstallation)
