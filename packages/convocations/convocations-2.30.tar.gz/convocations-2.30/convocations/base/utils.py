from decimal import Decimal
from functools import wraps
from io import StringIO
from itertools import chain
import os
import sys
import re
from typing import Any
import yaml
from termcolor import colored, cprint


g_brief = False
g_quiet = False


def expand_template(local_path, context):
    from jinja2 import Environment, FileSystemLoader
    jenv = Environment(loader=FileSystemLoader(os.getcwd()), lstrip_blocks=True, trim_blocks=True)
    content = jenv.get_template(local_path).render(**context or {})
    return content


def create_owner_string(owner=None, group=None):
    if owner:
        if group:
            return f'{owner}:{group}'
        return f'{owner}:'
    if group:
        return f':{group}'
    return None


def flush_print(st, **kwargs):
    """
    prints a string to stdout and flushes the stdout buffer.
    This is useful where stdout buffering delays the output of certain messages
    :param st: the message to print
    :param kwargs: additional kwargs to pass to the `print` function
    """
    flush = kwargs.pop('flush', True)
    print(st, **kwargs, flush=flush)
    sys.stdout.flush()


g_which_dot = -1


def dot_leader(st, length=40):
    """
    creates a dot leader to suffix a message with so that we get
    nicely aligned output and an easy way to get from message to value
    :param st: the message we are suffixing with the dot leader
    :param length: the field length (i.e., dot leader + len(st) == legnth)
    :return: the suffixed string, including the message + dot leader
    """
    global g_which_dot
    dot_chars = [ '.' ]
    g_which_dot += 1
    g_which_dot %= len(dot_chars)
    dot_char = dot_chars[g_which_dot]
    while length <= len(st):
        length += 10
    dots = dot_char * (length - len(st))
    return f'{st}{dots}'


def notice(st, length=40, **kwargs):
    """
    provides a notification message to the user.  this function is used
    in conjunction with `notice_end` to notify the user that something is
    happening and to await the response.
    :param st: the message that will be noticed to theuser
    :param length: the expected maximum field length for dot leads
    :param kwargs: additional kwargs to provide to `termcolor.cprint`
    :return:
    """
    if g_brief or g_quiet:
        return
    ending = kwargs.pop('end', None) or ''
    color = kwargs.pop('color', 'blue')
    attrs = kwargs.pop('attrs', None)
    if isinstance(attrs, str):
        attrs = [ attrs ]
    cprint(dot_leader(st, length), end=ending, color=color, attrs=attrs, **kwargs)


def notice_end(st=None, color=None, **kwargs):
    """
    ends the notice cycle.  this function is used
    in conjunction with `notice` to notify the user that something is
    happening and to await the response.
    :param st: the message that will be provided to the user
    :param color: the color of the notification
    :param kwargs: additional kwargs to provide to `termcolor.cprint`
    :return:
    """
    if g_brief or g_quiet:
        return
    if st is not None and not isinstance(st, (bool,)):
        st = f'{st}'
    if isinstance(st, str):
        cprint(st, color, **kwargs)
    elif st is False:
        flush_print('\N{wilted flower}')
    else:
        flush_print('\N{cherry blossom}')


def to_string(value: Any, format_floats=True) -> str:
    """
    used by the `print_table` function, this function converts
    a value to a string making sure to format decimal.Decimal and float values
    to 2 decimal places
    :param Any value: the message that will be provided to the user
    :param bool format_floats: if specified as True, values will be formatted
                               nicely with commas and 2 decimal places
    :return: the string representation of value
    :rtype: str
    """
    if isinstance(value, (float, Decimal)) and format_floats:
        st = f'{value:,.2f}'
    else:
        st = f'{value}'
    if '\n' in st:
        st = st.split('\n')
    return st


def print_table(
        header,
        rows,
        color='cyan',
        wrap_newline=False,
        format_floats=True,
        **kwargs):
    """
    prints a header and rows in a tabular format in the specified color.
    this function is useful for presenting summary information from aws
    commands in a tabular format
    :param list[str] header: a list of strings for the table header
    :param list[Iterable[Any]] rows: a list of list of values to present
    :param str color: the color in which we will print our table
    :param bool wrap_newline: if true, values with new lines in them
                              will be wrapped at '\n'
    :param bool format_floats: if true, floats and Decimals will be
                               formatted numerically
    """
    if g_brief or g_quiet:
        return
    max_lens = [ 0 ] * len(header)
    rows = [ [ to_string(x, format_floats) for x in row ] for row in rows ]
    for row in chain([ header ], rows):
        for i, x in enumerate(row):
            if isinstance(x, list):
                local_max = max(map(len, x))
                max_lens[i] = max(max_lens[i], local_max)
            else:
                max_lens[i] = max(max_lens[i], len(x))
    f_header = []
    for width, x in zip(max_lens, header):
        diff = len(x)
        x = colored(x, color)
        diff = len(x) - diff
        f = f'%-{width + diff}s'
        f = f % (x,)
        f_header.append(f)
    print(' | '.join(f_header))
    print(' | '.join([ colored('-' * width, color) for width in max_lens ]))
    if wrap_newline:
        for row in rows:
            max_height = max(len(x) if isinstance(x, list) else 1 for x in row)
            for h in range(max_height):
                f_row = []
                for n, (name, width, x) in enumerate(zip(header, max_lens, row)):
                    diff = 0
                    value = ' '
                    if isinstance(x, list) and h < len(x):
                        value = x[h]
                    elif h == 0 and not isinstance(x, list):
                        value = x
                    if n == 0:
                        diff = len(value)
                        value = colored(value, color)
                        diff = len(value) - diff
                    if name in ('size', 'price'):
                        f = f'%{width + diff}s'
                    else:
                        f = f'%-{width + diff}s'
                    f = f % (value,)
                    f_row.append(f)
                print(' | '.join(f_row))
    else:
        for row in rows:
            f_row = []
            for n, (name, width, x) in enumerate(zip(header, max_lens, row)):
                diff = 0
                if n == 0:
                    diff = len(x)
                    x = colored(x, color)
                    diff = len(x) - diff
                if name in ('size', 'price'):
                    f = f'%{width + diff}s'
                else:
                    f = f'%-{width + diff}s'
                f = f % (x,)
                f_row.append(f)
            print(' | '.join(f_row))


def confirm(message: str) -> bool:
    """
    presents the user with a confirmation message to which the user should
    respond with a YES / NO response
    :param message: the confirmation prompt
    :rtype: bool
    :return: whether the user entered yes or not
    """
    cprint(message, color='red', attrs=['underline'])
    confirmation = input("Please enter 'YES' to confirm and continue: ")
    return confirmation.lower() == 'yes'


def noticed(initial, completion=None):
    def wrap(fn):
        @wraps
        def decorated(*args, **kwargs):
            notice(initial)
            fn(*args, **kwargs)
            notice_end(completion)
        return decorated
    return wrap


def load_yaml(filename: str) -> Any:
    """
    Loads the yaml from filename and returns the relevant object
    :param filename: the name of the file to load
    :return: the constructed yaml object
    """
    with open(filename, 'r') as f:
        return yaml.load(f, yaml.SafeLoader)


def yaml_serializer(**kwargs):
    from ruamel.yaml import YAML
    y = YAML(**kwargs)
    y.indent(sequence=4, mapping=2, offset=2)
    return y


def get_context_value(ctx, key, default=None):
    pieces = key.split('.')
    value = ctx
    for piece in pieces:
        try:
            value = getattr(value, piece, None)
        except AttributeError:
            return default
    return value


def get_encrypted_context_value(ctx, session, key, default=None):
    from waddle import ParamBunch
    pieces = key.split('.')
    value = ctx
    for piece in pieces:
        try:
            value = getattr(value, piece, None)
        except AttributeError:
            return default
    value = ParamBunch.try_decrypt(value, session=session)
    return value


def dump_yaml(p, buff=None, quiet=True):
    """
    dumps an object as yaml to stdout
    """
    y = yaml_serializer()
    buff = buff or StringIO()
    y.dump(p, buff)
    buff.seek(0)
    if not quiet:
        print(buff.getvalue())
    return buff.getvalue()


def notice_level(brief=False, quiet=False):
    global g_brief, g_quiet
    g_brief = bool(brief)
    g_quiet = bool(quiet)


def sortable_cidr(cidr):
    if ':' in cidr:
        base = cidr.split('/', 1)[0]
        pieces = base.split(':')
        pieces = [ int(x, 16) for x in pieces if x ]
        return [256, 256, 256, 256, ] + pieces
    if re.match(r'^\d{1-3}\.\d{1-3}\.\d{1-3}\.\d{1-3}/\d+', cidr):
        return [int(y) for y in cidr.split('/', 1)[0].split('.')]
    return []
