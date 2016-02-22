import re
from contextlib import contextmanager

from time import sleep
from codev.configuration import BaseConfiguration
from codev.machines import MachinesProvider, BaseMachinesProvider
from codev.provider import ConfigurableProvider
from codev.performer import CommandError

from logging import getLogger
logger = getLogger(__name__)


class LXCMachine(object):
    def __init__(self, perfomer, ident, distribution, release, architecture):
        self.performer = perfomer
        self.ident = ident
        self.distribution = distribution
        self.release = release
        self.architecture = architecture
        self._container_directory = None

    def exists(self):
        output = self.performer.execute('lxc-ls')
        return self.ident in output.split()

    def is_started(self):
        output = self.performer.execute('lxc-info -n {name} -s'.format(
            name=self.ident,
        ))

        r = re.match('^State:\s+(.*)$', output.strip())
        if r:
            state = r.group(1)
        else:
            raise ValueError('o:%s:o' % output)

        if state == 'RUNNING':
            return True
        elif state == 'STOPPED':
            return False
        else:
            raise ValueError('s:%s:s' % state)

    def create(self):
        if not self.exists():
            self.performer.execute('lxc-create -t download -n {name} -- --dist {distribution} --release {release} --arch {architecture}'.format(
                name=self.ident,
                distribution=self.distribution,
                release=self.release,
                architecture=self.architecture
            ))
            return True
        else:
            return False

    def start(self):
        if not self.is_started():
            self.performer.execute('lxc-start -n {name}'.format(
                name=self.ident,
            ))

            while not self.ip:
                sleep(0.5)

            return True
        else:
            return False

    @property
    def ip(self):
        output = self.performer.execute('lxc-info -n {name} -i'.format(
            name=self.ident,
        ))

        for line in output.splitlines():
            r = re.match('^IP:\s+([0-9\.]+)$', line)
            if r:
                return r.group(1)

        return None

    @property
    def host(self):
        return self.ip

    def send_file(self, source, target):
        with self.performer.send_to_temp_file(source) as tempfile:
            #TODO direct access over share directory or with lxc-usernsexec
            self.performer.execute('cat {tempfile} | lxc-attach -n {name} -- tee {target} > /dev/null'.format(
                name=self.ident,
                tempfile=tempfile,
                target=target
            ))

    # def get_file(self, source, target):
    #     with self.performer.get_temp_file(target) as tempfile:
    #         #TODO direct access over share directory or with lxc-usernsexec
    #         self.performer.execute('lxc-attach -n {name} -- cat {source} > {tempfile}'.format(
    #             name=self.ident,
    #             tempfile=tempfile,
    #             source=source
    #         ))

    @contextmanager
    def get_fo(self, source):
        with self.performer.get_temp_fo() as (tempfile, opener):
            #TODO direct access over share directory or with lxc-usernsexec
            self.performer.execute('lxc-attach -n {name} -- cat {source} > {tempfile}'.format(
                name=self.ident,
                tempfile=tempfile,
                source=source
            ))
            with opener() as fo:
                yield fo

    @property
    def container_directory(self):
        if not self._container_directory:
            is_root = int(self.performer.execute('id -u')) == 0
            if is_root:
                container_directory = '/var/lib/lxc/{container_name}/'
            else:
                container_directory = '.local/share/lxc/{container_name}/'
            self._container_directory = container_directory.format(container_name=self.ident)
        return self._container_directory

    def check_execute(self, command):
        try:
            self.execute(command)
            return True
        except CommandError:
            return False

    def execute(self, command):
        ssh_auth_sock = self.performer.execute('echo $SSH_AUTH_SOCK')
        if ssh_auth_sock and self.performer.check_execute('[ -S %s ]' % ssh_auth_sock):

            self.performer.execute('rm -f {isolation_ident}/share/ssh-agent-sock && ln $SSH_AUTH_SOCK {isolation_ident}/share/ssh-agent-sock && chmod 7777 {isolation_ident}/share/ssh-agent-sock'.format(
                  isolation_ident=self.ident
            ))

            #possible solution via socat
            #https://gist.github.com/mgwilliams/4d929e10024912670152 or https://gist.github.com/schnittchen/a47e40760e804a5cc8b9

            env_vars = '-v SSH_AUTH_SOCK=/share/ssh-agent-sock'
        else:
            env_vars = ''

        output = self.performer.execute('lxc-attach {env_vars} -n {container_name} -- {command}'.format(
            container_name=self.ident,
            command=command,
            env_vars=env_vars
        ))
        return output


class LXCMachinesConfiguration(BaseConfiguration):
    @property
    def distribution(self):
        return self.data.get('distribution')

    @property
    def release(self):
        return self.data.get('release')

    @property
    def architecture(self):
        return self.data.get('architecture')

    @property
    def number(self):
        return int(self.data.get('number'))


class LXCMachinesProvider(BaseMachinesProvider, ConfigurableProvider):
    configuration_class = LXCMachinesConfiguration

    def create_machines(self):
        machines = []
        for i in range(1, self.configuration.number + 1):
            ident = '%s_%000d' % (self.machines_name, i)
            machine = LXCMachine(
                self.performer,
                ident,
                self.configuration.distribution,
                self.configuration.release,
                self.configuration.architecture
            )
            machine.create()
            machine.start()
            machines.append(machine)
        return machines

MachinesProvider.register('lxc', LXCMachinesProvider)
