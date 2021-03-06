from json import dumps
from logging import getLogger

from codev.core import Codev
from codev.core.debug import DebugSettings
from codev.core.executor import CommandError
from codev.core.machines import BaseMachine
from codev.core.provider import Provider
from .log import logging_config

# from codev.core.isolator import Isolator

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')

# FIXME
"""
protocol:

call: codev-source {source_name}:{source_option} -- {source_settings_data}
return: .codev

codev-perform run {configuration_name}:{configuration_option} --force
"""


class Isolation(Provider, BaseMachine):

    def __init__(self, *args, configuration_name, configuration_option, **kwargs):
        self.configuration_name = configuration_name
        self.configuration_option = configuration_option
        super().__init__(*args, **kwargs)

    def install_codev(self, source):
        pass

    def perform(self, codev, input_vars):

        # FIXME
        # version = self.executor.execute('pip3 show codev | grep ^Version | cut -d " " -f 2')
        # logger.info("Run 'codev {version}' in isolation.".format(version=version))

        load_vars = {**codev.configuration.loaded_vars, **input_vars}

        load_vars.update(DebugSettings.settings.load_vars)

        if DebugSettings.perform_settings:
            perform_debug = ' '.join(
                (
                    '--debug {key} {value}'.format(key=key, value=value)
                    for key, value in DebugSettings.perform_settings.data.items()
                )
            )
        else:
            perform_debug = ''

        logging_config(control_perform=True)
        try:
            self.execute(
                'codev-perform run {configuration_name}:{configuration_option} --force {perform_debug}'.format(
                    configuration_name=self.configuration_name,
                    configuration_option=self.configuration_option,
                    perform_debug=perform_debug
                ), output_logger=command_logger, writein=dumps(input_vars)
            )
        except CommandError as e:
            command_logger.error(e.error)
            logger.error("Installation failed.")
            return False
        else:
            logger.info("Installation has been successfully completed.")
            return True
        finally:
            logger.info("Setting up connectivity.")
            # self.connect()
            # FIXME

    @property
    def status(self):

        return ''  # FIXME


class PrivilegedIsolation(Isolation):

    source_directory = 'repository'

    def install_codev(self, source):
        self.execute('rm -rf {directory}'.format(directory=self.source_directory))
        self.execute('mkdir -p {directory}'.format(directory=self.source_directory))
        with self.change_directory(self.source_directory):
            source.install(self)
            with self.open_file('.codev') as codev_file:
                codev = Codev.from_yaml(codev_file, configuration_name=self.configuration_name, configuration_option=self.configuration_option)

        self._install_codev(codev.version)
        return codev

    def _install_codev(self, version):

        self.execute('pip3 install setuptools')

        # uninstall previous version of codev (ignore if not installed)
        self.check_execute('pip3 uninstall codev -y')

        # install proper version of codev
        # TODO requirements - 'python3-pip', 'libffi-dev', 'libssl-dev'
        if not DebugSettings.settings.distfile:
            logger.debug("Install codev version '{version}' to isolation.".format(version=version))
            self.execute('pip3 install --upgrade codev=={version}'.format(version=version))
        else:
            distfile = DebugSettings.settings.distfile.format(version=version)
            debug_logger.info('Install codev {distfile}'.format(distfile=distfile))

            from os.path import basename
            remote_distfile = '/tmp/{distfile}'.format(distfile=basename(distfile))

            self.send_file(distfile, remote_distfile)
            self.execute('pip3 install --upgrade {distfile}'.format(distfile=remote_distfile))

    def perform(self, source, input_vars):
        with self.change_directory(self.source_directory):
            super().perform(source, input_vars)




# class IsolationX(object):
#     def __init__(self, isolation_settings, infrastructure_settings, source, next_source, executor, ident):
#
#         ident = ':'.join(ident) if ident else str(time())
#         ident_hash = sha256(ident.encode()).hexdigest()
#
#         self.isolator = Isolator(
#             isolation_settings.provider,
#             executor=executor,
#             settings_data=isolation_settings.settings_data,
#             ident=ident_hash
#         )
#         self.settings = isolation_settings
#         self.source = source
#         self.next_source = next_source
#         self.current_source = self.next_source if self.next_source and self.exists() else self.source
#
#         self.infrastructure = Infrastructure(self.isolator, infrastructure_settings)
#
#     def connect(self):
#         """
#         :param isolation:
#         :return:
#         """
#         for machine_ident, connectivity_conf in self.settings.connectivity.items():
#             machine = self.infrastructure.get_machine_by_ident(machine_ident)
#
#             for source_port, target_port in connectivity_conf.items():
#                 self.isolator.redirect(machine.ip, source_port, target_port)
#
#     def _install_codev(self, codev_file):
#         version = YAMLSettingsReader().from_yaml(codev_file).version
#         self.isolator.execute('pip3 install setuptools')
#
#         # uninstall previous version of codev (ignore if not installed)
#         self.isolator.check_execute('pip3 uninstall codev -y')
#
#         # install proper version of codev
#         # TODO requirements - 'python3-pip', 'libffi-dev', 'libssl-dev'
#         if not DebugSettings.settings.distfile:
#             logger.debug("Install codev version '{version}' to isolation.".format(version=version))
#             self.isolator.execute('pip3 install --upgrade codev=={version}'.format(version=version))
#         else:
#             distfile = DebugSettings.settings.distfile.format(version=version)
#             debug_logger.info('Install codev {distfile}'.format(distfile=distfile))
#
#             from os.path import basename
#             remote_distfile = '/tmp/{distfile}'.format(distfile=basename(distfile))
#
#             self.isolator.send_file(distfile, remote_distfile)
#             self.isolator.execute('pip3 install --upgrade {distfile}'.format(distfile=remote_distfile))
#
#     # def execute_script(self, script, arguments=None, logger=None):
#     #     if DebugSettings.perform_settings:
#     #         perform_debug = ' '.join(
#     #             (
#     #                 '--debug {key} {value}'.format(key=key, value=value)
#     #                 for key, value in DebugSettings.perform_settings.data.items()
#     #             )
#     #         )
#     #     else:
#     #         perform_debug = ''
#     #     arguments.update(self.status)
#     #     codev_script = 'codev-perform execute {environment}:{configuration} {perform_debug} -- {script}'.format(
#     #         script=script,
#     #         environment=arguments['environment'],
#     #         configuration=arguments['configuration'],
#     #         source=arguments['source'],
#     #         source_option=arguments['source_option'],
#     #         perform_debug=perform_debug
#     #     )
#     #     with self.change_directory(self.current_source.directory):
#     #         super().execute_script(codev_script, arguments=arguments, logger=logger)
#
#     def _install_project(self):
#         # TODO refactorize
#         self.current_source.install(self.isolator)
#
#         # load .codev file from source and install codev with specific version
#         with self.current_source.open_codev_file(self.isolator) as codev_file:
#             self._install_codev(codev_file)
#
#     def install(self, status):
#         # TODO refactorize - divide?
#         if not self.isolator.exists():
#             logger.info("Creating isolation...")
#             self.isolator.create()
#             created = True
#         else:
#             if not self.isolator.is_started():
#                 self.isolator.start()
#             created = False
#
#         if created or not self.next_source:
#             logger.info("Install project from source to isolation...")
#             self.current_source = self.source
#             self._install_project()
#
#             # self.execute_scripts(self.settings.scripts.oncreate, status, logger=command_logger)
#         else:  # if not created and self.next_source
#             logger.info("Transition source in isolation...")
#             self.current_source = self.next_source
#             self._install_project()
#
#         logger.info("Entering isolation...")
#         # TODO
#         # self.execute_scripts(self.settings.scripts.onenter, status, logger=command_logger)
#
#     def run(self, status, input_vars):
#
#         # copy and update loaded_vars
#         load_vars = {**self.settings.loaded_vars, **input_vars}
#
#         version = self.isolator.execute('pip3 show codev | grep ^Version | cut -d " " -f 2')
#         logger.info("Run 'codev {version}' in isolation.".format(version=version))
#
#         if DebugSettings.perform_settings:
#             perform_debug = ' '.join(
#                 (
#                     '--debug {key} {value}'.format(key=key, value=value)
#                     for key, value in DebugSettings.perform_settings.data.items()
#                 )
#             )
#         else:
#             perform_debug = ''
#
#         logging_config(control_perform=True)
#         try:
#             configuration = '{configuration}:{configuration_option}'.format(
#                 **status
#             )
#             with self.isolator.change_directory(self.current_source.directory):
#                 self.isolator.execute(
#                     'codev-perform run {configuration} --force {perform_debug}'.format(
#                         configuration=configuration,
#                         perform_debug=perform_debug
#                     ), logger=command_logger, writein=dumps(load_vars))
#         except CommandError as e:
#             command_logger.error(e.error)
#             logger.error("Installation failed.")
#             return False
#         else:
#             logger.info("Installation has been successfully completed.")
#             return True
#         finally:
#             logger.info("Setting up connectivity.")
#             self.connect()
#
#     def destroy(self):
#         if self.isolator.is_started():
#             self.isolator.stop()
#         return self.isolator.destroy()
#
#     def exists(self):
#         return self.isolator.exists()
#
#     @property
#     def status(self):
#         if self.exists() and self.isolator.is_started():
#             infrastructure_status = self.infrastructure.status
#         else:
#             infrastructure_status = {}
#
#         status = dict(
#             current_source=self.current_source.name,
#             current_source_option=self.current_source.option,
#             infrastructure=infrastructure_status
#         )
#         if self.isolator.exists():
#             status.update(dict(ident=self.isolator.ident, ip=self.isolator.ip))
#         return status
