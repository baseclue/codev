from codev.core.executor import HasExecutor
from codev.core.provider import Provider
from codev.core.settings import HasSettings


class Task(Provider, HasSettings, HasExecutor):

    def prepare(self):
        raise NotImplementedError()

    def run(self, infrastructure, input_vars):
        raise NotImplementedError()

