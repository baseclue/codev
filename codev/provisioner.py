from .provider import Provider, ConfigurableProvider
# from .performer import ProxyPerformer


class Provisioner(Provider, ConfigurableProvider):
    def __init__(self, performer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performer = performer

    def install(self):
        raise NotImplementedError()

    def run(self, infrastructure, script_info, input_vars):
        raise NotImplementedError()

