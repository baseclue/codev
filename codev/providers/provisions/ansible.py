from codev.provision import Provision, BaseProvision
from codev.provider import ConfigurableProvider
from codev.configuration import BaseConfiguration

import configparser

from logging import getLogger
logger = getLogger(__name__)


class AnsibleProvisionConfiguration(BaseConfiguration):
    @property
    def playbook(self):
        return self.data.get('playbook', None)

    @property
    def version(self):
        return self.data.get('version', None)


class AnsibleProvision(BaseProvision, ConfigurableProvider):
    configuration_class = AnsibleProvisionConfiguration

    def install(self):
        self.performer.execute('apt-get install python-dev python-pip -y --force-yes')
        self.performer.execute('pip install --upgrade markupsafe paramiko PyYAML Jinja2 httplib2 six ecdsa==0.11')

        version_add = ''
        if self.configuration.version:
            version_add = '==%s' % self.configuration.version
        self.performer.execute('pip install --upgrade ansible%s' % version_add)

    def run(self, machines_groups):
        logger.debug('machines: %s' % machines_groups)
        playbook = self.configuration.playbook.format(infrastructure=self.infrastructure_name)

        inventory = configparser.ConfigParser(allow_no_value=True, delimiters=('',))
        for name, machines in machines_groups.items():
            inventory.add_section(name)
            for machine in machines:
                inventory.set(name, machine.ip, '')

        inventory_filepath = 'codev.ansible.inventory'

        with open(inventory_filepath, 'w+') as inventoryfile:
            inventory.write(inventoryfile)

        self.performer.execute('ansible-playbook -i {inventory} {playbook}'.format(
            inventory=inventory_filepath,
            playbook=playbook
        ))


Provision.register('ansible', AnsibleProvision)
