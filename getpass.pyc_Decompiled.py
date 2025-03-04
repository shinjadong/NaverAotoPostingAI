# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: getpass.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

"""Utilities to get a password and/or the current user name.\n\ngetpass(prompt[, stream]) - Prompt for a password, with echo turned off.\ngetuser() - Get the user name from the environment or password database.\n\nGetPassWarning - This UserWarning is issued when getpass() cannot prevent\n                 echoing of the password contents while reading.\n\nOn Windows, the msvcrt module will be used.\n\n"""
import contextlib
import io
import os
import sys
import warnings
__all__ = ['getpass', 'getuser', 'GetPassWarning']

class GetPassWarning(UserWarning):
    pass  # postinserted
def unix_getpass(prompt='Password: ', stream=None):
    """Prompt for a password, with echo turned off.\n\n    Args:\n      prompt: Written on stream to ask for the input.  Default: \'Password: \'\n      stream: A writable file object to display the prompt.  Defaults to\n              the tty.  If no tty is available defaults to sys.stderr.\n    Returns:\n      The seKr3t input.\n    Raises:\n      EOFError: If our input tty or stdin was closed.\n      GetPassWarning: When we were unable to turn echo off on the input.\n\n    Always restores terminal settings before returning.\n    """  # inserted
    passwd = None
    with contextlib.ExitStack() as stack:
        try:
            fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY)
            tty = io.FileIO(fd, 'w+')
            stack.enter_context(tty)
            input = io.TextIOWrapper(tty)
            stack.enter_context(input)
            if not stream:
                stream = input
        except OSError:
            pass  # postinserted
        else:  # inserted
            if fd is not None:
                try:
                    old = termios.tcgetattr(fd)
                    new = old[:]
                    new[3] &= ~termios.ECHO
                    tcsetattr_flags = termios.TCSAFLUSH
                    if hasattr(termios, 'TCSASOFT'):
                        tcsetattr_flags |= termios.TCSASOFT
        except termios.error:
                else:  # inserted
                    try:
                        termios.tcsetattr(fd, tcsetattr_flags, new)
                        passwd = _raw_input(prompt, stream, input=input)
                    finally:  # inserted
                        termios.tcsetattr(fd, tcsetattr_flags, old)
                        stream.flush()
            stream.write('\n')
            return passwd
            stack.close()
            try:
                fd = sys.stdin.fileno()
            except (AttributeError, ValueError):
                fd = None
                passwd = fallback_getpass(prompt, stream)
            input = sys.stdin
            if not stream:
                stream = sys.stderr
            if passwd is not None:
                raise
            if stream is not input:
                stack.close()
            passwd = fallback_getpass(prompt, stream)

def win_getpass(prompt='Password: ', stream=None):
    """Prompt for password with echo off, using Windows getwch()."""  # inserted
    if sys.stdin is not sys.__stdin__:
        return fallback_getpass(prompt, stream)
    for c in prompt:
        msvcrt.putwch(c)
    pw = ''
    while True:
        c = msvcrt.getwch()
        if c == '\r' or c == '\n':
            break
        if c == '':
            raise KeyboardInterrupt
        if c == '\b':
            pw = pw[:(-1)]
        else:  # inserted
            pw = pw + c
    msvcrt.putwch('\r')
    msvcrt.putwch('\n')
    return pw

def fallback_getpass(prompt='Password: ', stream=None):
    warnings.warn('Can not control echo on the terminal.', GetPassWarning, stacklevel=2)
    if not stream:
        stream = sys.stderr
    print('Warning: Password input may be echoed.', file=stream)
    return _raw_input(prompt, stream)

def _raw_input(prompt='', stream=None, input=None):
    if not stream:
        stream = sys.stderr
    if not input:
        input = sys.stdin
    prompt = str(prompt)
    if prompt:
        try:
            stream.write(prompt)
        except UnicodeEncodeError:
            pass  # postinserted
        else:  # inserted
            stream.flush()
    line = input.readline()
    if not line:
        raise EOFError
    if line[(-1)] == '\n':
        line = line[:(-1)]
    return line
            prompt = prompt.encode(stream.encoding, 'replace')
            prompt = prompt.decode(stream.encoding)
            stream.write(prompt)
        else:  # inserted
            pass

def getuser():
    """Get the username from the environment or password database.\n\n    First try various environment variables, then the password\n    database.  This works on Windows as long as USERNAME is set.\n\n    """  # inserted
    for name in ['LOGNAME', 'USER', 'LNAME', 'USERNAME']:
        user = os.environ.get(name)
        if user:
            return user
    else:  # inserted
        import pwd
        return pwd.getpwuid(os.getuid())[0]
try:
    import termios
    (termios.tcgetattr, termios.tcsetattr)
except (ImportError, AttributeError):
    pass  # postinserted
else:  # inserted
    getpass = unix_getpass
    try:
        import msvcrt
    except ImportError:
        pass  # postinserted
    else:  # inserted
        getpass = win_getpass
        getpass = fallback_getpass