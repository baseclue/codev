from logging import getLogger
from .machines import MachinesProvider
from hashlib import md5
from .isolation import Isolation

logger = getLogger(__name__)


class Infrastructure(object):
    def __init__(self, infrastructure_name, configuration):
        self.name = infrastructure_name
        self.configuration = configuration

    def machines_groups(self, performer, create=False):
        machines_groups = {}
        pub_key = '%s\n' % performer.execute('ssh-add -L')
        for machines_name, machines_configuration in self.configuration.machines.items():
            machines_provider = MachinesProvider(
                machines_configuration.provider,
                machines_name, performer, configuration_data=machines_configuration.specific
            )
            machines_groups[machines_name] = machines_provider.machines(create=create, pub_key=pub_key)
        return machines_groups

    def isolation(self, performer, installation, next_installation, ident):
        isolation_configuration = self.configuration.isolation
        return Isolation(
            isolation_configuration.provider,
            isolation_configuration.scripts,
            isolation_configuration.connectivity,
            installation,
            next_installation,
            performer,
            ident=md5(ident.encode()).hexdigest()
        )
