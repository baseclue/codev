import logging
import sys
import colorama

LOGLEVELS = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
}


def config_logging(loglevel, formatting):
    handler = logging.StreamHandler(stream=sys.stdout)

    handler.level = loglevel
    handler.formatter = logging.Formatter(formatting)
    logger = logging.getLogger('codev')
    logger.level = loglevel
    logger.addHandler(handler)


def control_logging(loglevel):
    config_logging(loglevel, colorama.Fore.BLUE + '[CONTROL]' + colorama.Fore.RESET + ' [%(levelname)s] %(message)s')


def perform_logging(loglevel):
    config_logging(loglevel, '[%(levelname)s] %(message)s')


class CommandLogger(logging.Logger):
    def __init__(self):
        super(CommandLogger, self).__init__('control', logging.INFO)

    def set_perform_command_output(self):
        perform_debug_handler = logging.StreamHandler(stream=sys.stdout)
        perform_debug_handler.formatter = logging.Formatter('[%(levelname)s] %(message)s')
        self.addHandler(perform_debug_handler)

    def set_control_perform_command_output(self):
        control_perform_handler = logging.StreamHandler(stream=sys.stdout)
        control_perform_handler.formatter = logging.Formatter(colorama.Fore.YELLOW + '[PERFORM]' + colorama.Fore.RESET + ' %(message)s')
        self.addHandler(control_perform_handler)

command_logger = CommandLogger()