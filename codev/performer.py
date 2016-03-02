from .provider import BaseProvider, ConfigurableProvider
from contextlib import contextmanager


class BaseExecutor(object):
    def check_execute(self, command):
        try:
            self.execute(command)
            return True
        except CommandError:
            return False

    def execute(self, command, logger=None, writein=None):
        raise NotImplementedError()

    def run_scripts(self, scripts, common_arguments={}):
        for script, arguments in scripts:
            arguments.update(common_arguments)
            self.execute(script.format(arguments))


class PerformerError(Exception):
    pass


class CommandError(PerformerError):
    def __init__(self, command, exit_code, error):
        self.command = command
        self.exit_code = exit_code
        self.error = error
        super(CommandError, self).__init__(
            "Command '{command}' failed with exit code '{exit_code}' with error '{error}'".format(
                command=command, exit_code=exit_code, error=error
            )
        )


"""
Output reader
"""
from threading import Thread


class OutputReader(object):
    def __init__(self, output, logger=None):
        self._output_lines = []
        self._output_reader = Thread(target=self._reader, args=(output,), kwargs=dict(logger=logger))
        self._output_reader.start()

    def _reader(self, output, logger=None):
        while True:
            line = output.readline()
            if not line:
                break
            output_line = line.decode('utf-8').rstrip('\n')
            self._output_lines.append(output_line)
            if logger:
                logger.debug(output_line)
        output.close()

    def output(self):
        self._output_reader.join()
        return '\n'.join(self._output_lines)


class BasePerformer(BaseExecutor, ConfigurableProvider):
    def __init__(self, *args, **kwargs):
        self.output_logger = getLogger('command_output')
        super(BasePerformer, self).__init__(*args, **kwargs)

    def send_file(self, source, target):
        raise NotImplementedError()

    @contextmanager
    def get_fo(self, remote_path):
        yield NotImplementedError()


class Performer(BaseProvider):
    provider_class = BasePerformer

"""
background runner
"""

from collections import namedtuple
from time import sleep
from logging import getLogger

Isolation = namedtuple(
    'Isolation', ['output_file', 'error_file', 'exitcode_file', 'command_file', 'pid_file', 'temp_file']
)

OUTPUT_FILE = 'codev.out'
ERROR_FILE = 'codev.err'
EXITCODE_FILE = 'codev.exit'
COMMAND_FILE = 'codev.command'
PID_FILE = 'codev.pid'
TEMP_FILE = 'codev.temp'


class BaseRunner(BaseExecutor):
    def __init__(self, performer, ident=None):
        self.performer = performer
        self.ident = ident


class BackgroundRunner(BaseRunner):
    def __init__(self, *args, **kwargs):
        super(BackgroundRunner, self).__init__(*args, **kwargs)
        self._isolation_cache = None
        self.__isolation_directory = None
        self.logger = getLogger(__name__)

    @property
    def _isolation_directory(self):
        if not self.__isolation_directory:
            if not self.ident:
                ssh_info = self.performer.execute('echo $SSH_CLIENT')
                ip, remote_port, local_port = ssh_info.split()
                self.ident = 'control_{ip}_{remote_port}_{local_port}'.format(
                    ip=ip, remote_port=remote_port, local_port=local_port
                )
            home_dir = self.performer.execute('bash -c "echo ~"')
            self.__isolation_directory = '{home_dir}/{ident}'.format(
                home_dir=home_dir,
                ident=self.ident
            )

        return self.__isolation_directory

    def _create_isolation(self):
        self.performer.execute('mkdir -p %s' % self._isolation_directory)

        output_file, error_file, exitcode_file, command_file, pid_file, temp_file = map(
            lambda f: '%s/%s' % (self._isolation_directory, f),
            [OUTPUT_FILE, ERROR_FILE, EXITCODE_FILE, COMMAND_FILE, PID_FILE, TEMP_FILE]
        )

        return Isolation(
            command_file=command_file,
            output_file=output_file,
            error_file=error_file,
            exitcode_file=exitcode_file,
            pid_file=pid_file,
            temp_file=temp_file
        )

    @property
    def _isolation(self):
        if not self._isolation_cache:
            self._isolation_cache = self._create_isolation()
        return self._isolation_cache

    def _file_exists(self, filepath):
        return self.performer.check_execute('[ -f %s ]' % filepath)

    def _bg_check(self, pid):
        return self.performer.check_execute('ps -p %s -o pid=' % pid)

    def _bg_log(self, logger, skip_lines, omit_last):
        output = self.performer.execute('tail {output_file} -n+{skip_lines}'.format(output_file=self._isolation.output_file, skip_lines=skip_lines))
        if not output:
            return 0
        output_lines = output.splitlines()
        if omit_last:
            output_lines.pop()
        for line in output_lines:
            #TODO remove output logger - refactorize output logging
            (logger or self.output_logger).debug(line)
        return len(output_lines)

    def _bg_stop(self, pid):
        return self.performer.execute('kill %s' % pid)

    def _bg_kill(self, pid):
        return self.performer.execute(
            'kill -9 {pid};rm {exitcode_file}'.format(
                pid=pid,
                exitcode_file=self._isolation.exitcode_file
            )
        )

    def _bg_wait(self, pid, logger=None):
        skip_lines = 1
        while self._bg_check(pid):
            skip_lines += self._bg_log(logger, skip_lines, True)
            sleep(0.5)

        self._bg_log(logger, skip_lines, False)

    def _cat_file(self, catfile):
        return self.performer.execute('cat %s' % catfile)

    def _get_bg_running_pid(self):
        return self._cat_file(self._isolation.pid_file)

    def execute(self, command, logger=None, writein=None):
        isolation = self._isolation

        if self._file_exists(isolation.exitcode_file) and self._cat_file(isolation.exitcode_file) == '':
            if self._file_exists(isolation.pid_file):
                pid = self._cat_file(isolation.pid_file)
                if pid and self._bg_check(pid):
                    raise PerformerError('Another process is running.')

        self.performer.execute('echo "" > {output_file} > {error_file} > {exitcode_file} > {pid_file}'.format(
            **isolation._asdict()
        ))

        self.performer.execute(
            'tee {command_file} > /dev/null && chmod +x {command_file}'.format(
                **isolation._asdict()
            ),
            writein='{command}; echo $? > {exitcode_file}\n'.format(
                command=command,
                exitcode_file=isolation.exitcode_file
            )
        )

        bg_command = 'nohup {command_file} > {output_file} 2> {error_file} & echo $! | tee {pid_file}'.format(
            **isolation._asdict()
        )

        pid = self.performer.execute(bg_command, writein=writein)

        if not pid.isdigit():
            raise ValueError('not a pid %s' % pid)

        self._bg_wait(pid, logger=logger)

        exit_code = int(self._cat_file(isolation.exitcode_file))

        output = self._cat_file(isolation.output_file)

        if exit_code:
            err = self._cat_file(isolation.error_file)
            raise CommandError(command, exit_code, err)

        return output

    def _control(self, method, *args, **kwargs):
        self.logger.debug('SSH Join command')
        try:
            pid = self._get_bg_running_pid()
        except CommandError as e:
            raise PerformerError('No active isolation.')

        if pid:
            try:
                method(pid, *args, **kwargs)
                return True
            except CommandError as e:
                return False
        else:
            return False

    def join(self, logger=None):
        return self._control(self._bg_wait, logger=logger)

    def stop(self):
        return self._control(self._bg_stop)

    def kill(self):
        return self._control(self._bg_kill)
