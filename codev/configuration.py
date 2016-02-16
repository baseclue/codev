from .info import VERSION
from os import path
import yaml

from collections import OrderedDict
from .logging import LOGLEVELS

"""
YAML OrderedDict mapping
http://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
"""
_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())


def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))


yaml.add_representer(OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)
"""
"""


class BaseConfiguration(object):
    def __init__(self, data):
        self.data = data


class ProviderConfiguration(BaseConfiguration):
    @property
    def provider(self):
        return self.data.get('provider')

    @property
    def specific(self):
        return self.data.get('specific', {})


class DictConfiguration(OrderedDict):
    def __init__(self, cls, data):
        super(DictConfiguration, self).__init__()
        for name, itemdata in data.items():
            self[name] = cls(itemdata)


class DebugConfiguration(BaseConfiguration):
    @property
    def loglevel(self):
        return LOGLEVELS[self.data.get('loglevel', 'info').lower()]

    @property
    def distfile(self):
        return self.data.get('distfile', '')

    @property
    def perform_command_output(self):
        return bool(self.data.get('perform_command_output', False))

    @property
    def show_client_exception(self):
        return bool(self.data.get('show_client_exception', False))


class InfrastructureConfiguration(BaseConfiguration):
    @property
    def machines(self):
        return DictConfiguration(ProviderConfiguration, self.data.get('machines', {}))

    @property
    def provision(self):
        return ProviderConfiguration(self.data.get('provision', {}))


class EnvironmentConfiguration(BaseConfiguration):
    @property
    def performer(self):
        return ProviderConfiguration(self.data.get('performer', {}))

    @property
    def isolation_provider(self):
        return self.data.get('isolation')

    @property
    def infrastructures(self):
        return DictConfiguration(InfrastructureConfiguration, self.data.get('infrastructures', {}))

    @property
    def installations(self):
        return self.data.get('installations', [])


class Configuration(BaseConfiguration):

    def __init__(self, data=None):
        super(Configuration, self).__init__(self.default_data)
        if data:
            self.data.update(data)
        self.current_data = None

    @property
    def default_data(self):
        return OrderedDict((
            ('version', VERSION),
            ('project', path.basename(path.abspath(path.curdir))),
            ('environments', {})
        ))

    @property
    def version(self):
        return self.data['version']

    @property
    def project(self):
        return self.data['project']

    @property
    def debug(self):
        return DebugConfiguration(self.data.get('debug', {}))

    @property
    def environments(self):
        return DictConfiguration(EnvironmentConfiguration, self.data['environments'])

    @property
    def repository(self):
        return self.data.get('repository', None)


class YAMLConfiguration(Configuration):
    @classmethod
    def from_configuration(cls, configuration):
        return cls(configuration.data)

    @classmethod
    def from_file(cls, filepath):
        return cls.from_yaml(open(filepath))

    @classmethod
    def from_yaml(cls, yamldata):
        return cls(yaml.load(yamldata))

    def save_to_file(self, filepath):
        yaml.dump(self.data, open(filepath, 'w+'))

