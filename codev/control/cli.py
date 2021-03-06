import click
from colorama import Fore as color, Style as style
from functools import wraps

from codev.core.cli import configuration_with_option, nice_exception, path_option, bool_exit_enable, main
from codev.core.utils import parse_options
from codev.core.debug import DebugSettings

from . import CodevControl


def source_transition(codev_control_status):
    """
    :param installation_status:
    :return:
    """
    # TODO deploy vs destroy (different highlighted source in transition)
    next_source_available = bool(codev_control_status.next_source)
    isolation_exists = bool(codev_control_status.isolation)

    color_options = dict(
        color_source=color.GREEN,
        color_reset=color.RESET + style.RESET_ALL
    )

    if next_source_available:
        if not isolation_exists:
            color_source = color.GREEN + style.BRIGHT
            color_next_source = color.GREEN
        else:
            color_source = color.GREEN
            color_next_source = color.GREEN + style.BRIGHT

        color_options.update(dict(
            color_source=color_source,
            color_next_source=color_next_source,
        ))

        transition = ' -> {color_next_source}{next_source}:{next_source.option}{color_reset}'.format(
            **codev_control_status, **color_options
        )
    else:
        transition = ''

    return '{color_source}{source.name}:{source.option}{color_reset}{transition}'.format(
        transition=transition,
        **codev_control_status, **color_options
    )


def confirmation_message(message):
    def decorator(f):
        @wraps(f)
        def confirmation_wrapper(codev_control, force, **kwargs):
            if not force:
                if not click.confirm(
                        message.format(
                            source_transition=source_transition(codev_control.status),
                            configuration_with_option=configuration_with_option(
                                codev_control.status.configuration.name, codev_control.status.configuration.option
                            ),
                            **codev_control.status
                        )
                ):
                    raise click.Abort()
            return f(codev_control, **kwargs)

        return click.option(
            '-f',
            '--force',
            is_flag=True,
            help='Force to run the command. Avoid the confirmation.'
        )(confirmation_wrapper)

    return decorator


def codev_control_options(func):
    @wraps(func)
    def codev_control_wrapper(
            configuration,
            source,
            next_source,
            **kwargs):

        source_name, source_option = parse_options(source)
        next_source_name, next_source_option = parse_options(next_source)
        configuration_name, configuration_option = parse_options(configuration)

        codev_control = CodevControl.from_file(
            '.codev',
            configuration_name=configuration_name,
            configuration_option=configuration_option,
            source_name=source_name,
            source_option=source_option,
            next_source_name=next_source_name,
            next_source_option=next_source_option
        )
        return func(codev_control, **kwargs)

    f = click.argument(
        'configuration',
        metavar='<configuration:option>',
        required=True)(codev_control_wrapper)

    f = click.option(
        '-s', '--source',
        default='',
        metavar='<source>',
        help='Source')(f)

    return click.option(
        '-t', '--next-source',
        default='',
        metavar='<next source>',
        help='Next source')(f)


def debug_option(func):
    @wraps(func)
    def debug_wrapper(debug, debug_perform, **kwargs):
        if debug:
            DebugSettings.settings = DebugSettings(dict(debug))

        if debug_perform:
            DebugSettings.perform_settings = DebugSettings(dict(debug_perform))

        return func(**kwargs)

    f = click.option(
        '--debug-perform',
        type=click.Tuple([str, str]),
        multiple=True,
        metavar='<variable> <value>',
        help='Debug perform options.'
    )

    return f(
        click.option(
            '--debug',
            type=click.Tuple([str, str]),
            multiple=True,
            metavar='<variable> <value>',
            help='Debug options.'
        )(debug_wrapper)
    )


def command(confirmation=None, bool_exit=True, **kwargs):
    def decorator(func):
        if confirmation:
            func = confirmation_message(confirmation)(func)
        func = codev_control_options(func)
        func = nice_exception(func)
        func = path_option(func)
        func = debug_option(func)
        if bool_exit:
            func = bool_exit_enable(func)
        func = main.command(**kwargs)(func)
        return func
    return decorator
