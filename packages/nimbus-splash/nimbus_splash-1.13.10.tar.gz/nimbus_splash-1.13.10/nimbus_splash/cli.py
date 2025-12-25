import argparse
import subprocess
import os
import pathlib
import warnings
import sys

from . import job
from . import utils as ut
from . import config as cfg
from .__version__ import __version__


DEFAULT_ORCA_VERSION = ut.get_envvar('SPLASH_ORCA_VERSION')
if not len(DEFAULT_ORCA_VERSION):
    DEFAULT_ORCA_VERSION = '6.1.0'

DEFAULT_INSTANCE = ut.get_envvar('SPLASH_DEFAULT_INSTANCE')
if DEFAULT_INSTANCE not in cfg.ORCA_SUPPORTED_INSTANCES:
    DEFAULT_INSTANCE = 'spot-fsv2-16'


def custom_formatwarning(msg, *args, **kwargs):
    # ignore everything except the message
    return ut.cstring(str(msg) + '\n', 'black_yellowbg')


warnings.formatwarning = custom_formatwarning


def orca_modules_func(uargs):
    '''
    Wrapper for CLI orca_modules call

    Parameters
    ----------
    uargs : argparser object
        User arguments

    Returns
    -------
    None
    '''

    # Print orca versions

    ut.cprint(
        f'    ORCA MODULES KNOWN TO NIMBUS_SPLASH V{__version__}',
        'green'
    )

    for instance, options in cfg.ORCA_MODULES.items():
        ut.cprint('*************************************************', 'green')
        ut.cprint(f'{instance}', 'cyan')
        for version, module in options.items():
            ut.cprint(f'    {version}: {module}', 'cyan')

    ut.cprint('*************************************************\n', 'green')

    ut.cprint(
        'By default, splash will use ',
        'green',
        end=''
    )
    ut.cprint(f'{DEFAULT_ORCA_VERSION}', 'cyan')

    ut.cprint(
        'Change this with',
        'green'
    )
    ut.cprint('splash submit input_file.inp -o VERSION_NUMBER', 'cyan')

    ut.cprint(
        '\nContact Research Computing to add missing modules to nimbus',
        'green'
    )
    ut.cprint(
        'Then Dr Jon Kragskow to add missing modules to splash',
        'green'
    )

    return


def submit_func(uargs):
    '''
    Wrapper for CLI submit call

    Parameters
    ----------
    uargs : argparser object
        User arguments

    Returns
    -------
    None
    '''

    if len(ut.get_envvar('SPLASH_ORCA_MODULE')):
        ut.red_exit(
            (
                'SPLASH_ORCA_MODULE environment variableis deprecated\n'
                'Please see nimbus_splash documentation\n'
                'And set SPLASH_ORCA_VERSION instead'
            )
        )

    # Check instance is supported
    if uargs.instance in cfg.ORCA_SUPPORTED_INSTANCES:
        instance = uargs.instance
    else:
        ut.red_exit(f'Error: instance {uargs.instance} unsupported')

    # Check ORCA version exists on specified instance
    if uargs.orca_version not in cfg.ORCA_MODULES[uargs.instance.split('-')[1]]: # noqa
        ut.red_exit(
            f'ORCA version {uargs.orca_version} not available on instance {uargs.instance}' # noqa
        )

    # Read email environment variable
    try:
        email = os.environ['SPLASH_EMAIL']
    except KeyError:
        email = ''

    # Write job file
    for file in uargs.input_files:

        # Check input exists
        if not file.exists:
            ut.red_exit('Cannot locate {}'.format(file.name))

        # Check contents/format of input file and any file dependencies
        # with warnings.catch_warnings(record=True) as w:
        try:
            dependencies = job.parse_input_contents(
                file,
                instance_name=instance,
                skip_xyz=uargs.skip_xyz
            )
        except (ValueError, FileNotFoundError) as err:
            ut.red_exit(str(err))

        if uargs.verbose:
            print(dependencies)

        # Check for research allocation id environment variable
        raid = ut.get_envvar('SPLASH_RAID')
        if not len(raid):
            ut.red_exit('Please set SPLASH_RAID environment variable')

        job_file = job.write_file(
            file, instance, uargs.time, verbose=True,
            dependencies=list(dependencies.values()),
            orca_version=uargs.orca_version,
            research_allocation_id=raid,
            email=email
        )

        # Submit to queue
        if not uargs.no_start:
            subprocess.call('sbatch {}'.format(job_file), shell=True)

    return


class CustomErrorArgumentParser(argparse.ArgumentParser):
    '''
    Custom ArgumentParser to handle errors and print usage\n
    This is required to avoid the default behavior of argparse which
    modifies the usage message when it prints, conflicting with the preset
    values used in the subparsers.
    '''
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"error: {message}.\n")
        sys.stderr.write("       Use -h to see all options.\n")
        sys.exit(2)


def read_args(arg_list=None):
    '''
    Reader for command line arguments.
    Uses sub parsers for individual programs

    Parameters
    ----------
        args : argparser object
            command line arguments

    Returns
    -------
        None
    '''

    description = 'nimbus_splash (splash) - A package for using Orca on Nimbus'

    epilog = 'Type\n'
    epilog += ut.cstring('splash <subprogram> -h\n', 'cyan')
    epilog += 'for help with a specific subprogram.\n'

    parser = CustomErrorArgumentParser(
        usage=ut.cstring('splash <subprogram> [options]', 'cyan'),
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser._positionals.title = 'Subprograms'

    subparsers = parser.add_subparsers(dest='prog')

    submit = subparsers.add_parser(
        'submit',
        description='Generate Nimbus SLURM submission script',
        usage=ut.cstring('splash submit <input_file(s)> [options]', 'cyan'),
    )
    submit._positionals.title = 'Mandatory Arguments'

    submit.set_defaults(func=submit_func)

    submit.add_argument(
        'input_files',
        metavar='<input_file(s)>',
        nargs='+',
        type=pathlib.Path,
        help='Orca input file name(s)'
    )

    submit.add_argument(
        '-i',
        '--instance',
        default=DEFAULT_INSTANCE,
        type=str,
        help=f'Instance to run on, default is {DEFAULT_INSTANCE}'
    )

    submit.add_argument(
        '-t',
        '--time',
        type=str,
        default='24:00:00',
        help='Time for job, formatted as HH:MM:SS, default 24:00:00'
    )

    submit.add_argument(
        '-o',
        '--orca_version',
        type=str,
        default=DEFAULT_ORCA_VERSION,
        help=f'Version of orca to use e.g. {DEFAULT_ORCA_VERSION}'
    )

    submit.add_argument(
        '-sx',
        '--skip_xyz',
        action='store_true',
        help='Skip formatting check for .xyz file'
    )

    submit.add_argument(
        '-ns',
        '--no_start',
        action='store_true',
        help='If specified, jobs are not submitted to nimbus queue'
    )

    submit.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='If specified, debug information is printed to screen'
    )

    versions = subparsers.add_parser(
        'orca_modules',
        description='Print orca modules known to splash'
    )
    versions.set_defaults(func=orca_modules_func)

    # If argument list is none, then call function func
    # which is assigned to help function
    parser.set_defaults(func=lambda _: parser.print_help())

    args = parser.parse_args(arg_list)
    args.func(args)
    return args


def interface():
    read_args()
    return
