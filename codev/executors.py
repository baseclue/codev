from .configuration import YAMLConfiguration
from os import unlink

class BaseExecutor(object):
    def __init__(self, configuration):
        self.configuration = configuration

"""
maybe move to command line client part
"""
class Executor(BaseExecutor):
    def __init__(self, configuration, executor_class):
        super(Executor, self).__init__(configuration)
        self.executor = executor_class(self.configuration)

    def __getattr__(self, name):
        return getattr(self.executor, name)
"""
"""


class Perform(BaseExecutor):
    def install(self):
        print('perform')


class Control(BaseExecutor):
    def __init__(self, *args, **kwargs):
        super(Control, self).__init__(*args, **kwargs)
        self.isolation_class = self.configuration.current.environment.isolation

    def install(self):
        #create isolation
        self.isolation = self.isolation_class(self.configuration)

        #install python3 pip
        self.isolation.execute('apt-get install python3-pip -y')

        #install proper version of codev
        self.isolation.execute('pip3 install codev==%s' % self.configuration.version)

        #send configuration file
        YAMLConfiguration.from_configuration(self.configuration).save_to_file('tmp')
        self.isolation.send_file('tmp', '.codev')
        unlink('tmp')

        #predani rizeni
        output, errors = self.isolation.execute('codev install %(environment)s %(infrastructure)s %(version)s -m perform -f' % {
            'environment': self.configuration.current.environment.name,
            'infrastructure': self.configuration.current.infrastructure.name,
            'version': self.configuration.current.version,
        })
        print(output, errors)

