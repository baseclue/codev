from .provider import BaseProvider, ConfigurableProvider


class BaseInstallation(ConfigurableProvider):
    def __init__(self, options, *args, **kwargs):
        self.process_options(options)
        self.options = options
        super(BaseInstallation, self).__init__(*args, **kwargs)

    @property
    def ident(self):
        return '{provider_name}_{ident}'.format(
            provider_name=self.__class__.provider_name,
            ident=self.id
        )

    def install(self, performer):
        raise NotImplementedError()

    def process_options(self, options):
        raise NotImplementedError()

    @property
    def id(self):
        raise NotImplementedError()

    @property
    def directory(self):
        return 'repository'


class Installation(BaseProvider):
    provider_class = BaseInstallation