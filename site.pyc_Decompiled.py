# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: site.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

"""Append module search paths for third-party packages to sys.path.\n\n****************************************************************\n* This module is automatically imported during initialization. *\n****************************************************************\n\nThis will append site-specific paths to the module search path.  On\nUnix (including Mac OSX), it starts with sys.prefix and\nsys.exec_prefix (if different) and appends\nlib/python<version>/site-packages.\nOn other platforms (such as Windows), it tries each of the\nprefixes directly, as well as with lib/site-packages appended.  The\nresulting directories, if they exist, are appended to sys.path, and\nalso inspected for path configuration files.\n\nIf a file named \"pyvenv.cfg\" exists one directory above sys.executable,\nsys.prefix and sys.exec_prefix are set to that directory and\nit is also checked for site-packages (sys.base_prefix and\nsys.base_exec_prefix will always be the \"real\" prefixes of the Python\ninstallation). If \"pyvenv.cfg\" (a bootstrap configuration file) contains\nthe key \"include-system-site-packages\" set to anything other than \"false\"\n(case-insensitive), the system-level prefixes will still also be\nsearched for site-packages; otherwise they won\'t.\n\nAll of the resulting site-specific directories, if they exist, are\nappended to sys.path, and also inspected for path configuration\nfiles.\n\nA path configuration file is a file whose name has the form\n<package>.pth; its contents are additional directories (one per line)\nto be added to sys.path.  Non-existing directories (or\nnon-directories) are never added to sys.path; no directory is added to\nsys.path more than once.  Blank lines and lines beginning with\n\'#\' are skipped. Lines starting with \'import\' are executed.\n\nFor example, suppose sys.prefix and sys.exec_prefix are set to\n/usr/local and there is a directory /usr/local/lib/python2.5/site-packages\nwith three subdirectories, foo, bar and spam, and two path\nconfiguration files, foo.pth and bar.pth.  Assume foo.pth contains the\nfollowing:\n\n  # foo package configuration\n  foo\n  bar\n  bletch\n\nand bar.pth contains:\n\n  # bar package configuration\n  bar\n\nThen the following directories are added to sys.path, in this order:\n\n  /usr/local/lib/python2.5/site-packages/bar\n  /usr/local/lib/python2.5/site-packages/foo\n\nNote that bletch is omitted because it doesn\'t exist; bar precedes foo\nbecause bar.pth comes alphabetically before foo.pth; and spam is\nomitted because it is not mentioned in either path configuration file.\n\nThe readline module is also automatically configured to enable\ncompletion for systems that support it.  This can be overridden in\nsitecustomize, usercustomize or PYTHONSTARTUP.  Starting Python in\nisolated mode (-I) disables automatic readline configuration.\n\nAfter these operations, an attempt is made to import a module\nnamed sitecustomize, which can perform arbitrary additional\nsite-specific customizations.  If this import fails with an\nImportError exception, it is silently ignored.\n"""
global USER_BASE  # inserted
global ENABLE_USER_SITE  # inserted
global USER_SITE  # inserted
global PREFIXES  # inserted
import sys
import os
import builtins
import _sitebuiltins
import io
import stat
PREFIXES = [sys.prefix, sys.exec_prefix]
ENABLE_USER_SITE = None
USER_SITE = None
USER_BASE = None

def _trace(message):
    if sys.flags.verbose:
        print(message, file=sys.stderr)

def makepath(*paths):
    dir = os.path.join(*paths)
    try:
        dir = os.path.abspath(dir)
    except OSError:
        pass  # postinserted
    else:  # inserted
        return (dir, os.path.normcase(dir))
        pass

def abs_paths():
    """Set all module __file__ and __cached__ attributes to an absolute path"""  # inserted
    for m in set(sys.modules.values()):
        loader_module = None
        try:
            loader_module = m.__loader__.__module__
        finally:  # inserted
            if loader_module not in {'_frozen_importlib_external', '_frozen_importlib'}:
                continue
            try:
                m.__file__ = os.path.abspath(m.__file__)
            finally:  # inserted
                try:
                    m.__cached__ = os.path.abspath(m.__cached__)
        try:
            loader_module = m.__spec__.loader.__module__

def removeduppaths():
    """ Remove duplicate entries from sys.path along with making them\n    absolute"""  # inserted
    L = []
    known_paths = set()
    for dir in sys.path:
        dir, dircase = makepath(dir)
        if dircase not in known_paths:
            L.append(dir)
            known_paths.add(dircase)
    sys.path[:] = L
    return known_paths

def _init_pathinfo():
    """Return a set containing all existing file system items from sys.path."""  # inserted
    d = set()
    for item in sys.path:
        try:
            if os.path.exists(item):
                _, itemcase = makepath(item)
                d.add(itemcase)
        except TypeError:
            pass  # postinserted
    else:  # inserted
        return d
        pass
    else:  # inserted
        try:
            pass  # postinserted
        pass

def addpackage(sitedir, name, known_paths):
    """Process a .pth file within the site-packages directory:\n       For each line in the file, either combine it with sitedir to a path\n       and add that to known_paths, or execute it if it starts with \'import \'.\n    """  # inserted
    if known_paths is None:
        known_paths = _init_pathinfo()
        reset = True
    else:  # inserted
        reset = False
    fullname = os.path.join(sitedir, name)
    try:
        st = os.lstat(fullname)
    except OSError:
        pass  # postinserted
    else:  # inserted
        if getattr(st, 'st_flags', 0) & stat.UF_HIDDEN or getattr(st, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_HIDDEN:
            _trace(f'Skipping hidden .pth file: {fullname}')
            return
        _trace(f'Processing .pth file: {fullname}')
        try:
            f = io.TextIOWrapper(io.open_code(fullname), encoding='locale')
    except OSError:
        else:  # inserted
            with f:
                for n, line in enumerate(f):
                    if line.startswith('#'):
                        continue
                    if line.strip() == '':
                        continue
                    try:
                        if line.startswith(('import ', 'import\t')):
                            exec(line)
                            continue
                        line = line.rstrip()
                        dir, dircase = makepath(sitedir, line)
                        if dircase not in known_paths and os.path.exists(dir):
                            sys.path.append(dir)
                            known_paths.add(dircase)
        except Exception as exc:
            pass  # postinserted
        if reset:
            known_paths = None
        return known_paths
        return
        print('Error processing line {:d} of {}:\n'.format(n + 1, fullname), file=sys.stderr)
        import traceback
        for record in traceback.format_exception(exc):
            for line in record.splitlines():
                print('  ' + line, file=sys.stderr)
        print('\nRemainder of file ignored', file=sys.stderr)
        break

def addsitedir(sitedir, known_paths=None):
    """Add \'sitedir\' argument to sys.path if missing and handle .pth files in\n    \'sitedir\'"""  # inserted
    _trace(f'Adding directory: {sitedir}')
    if known_paths is None:
        known_paths = _init_pathinfo()
        reset = True
    else:  # inserted
        reset = False
    sitedir, sitedircase = makepath(sitedir)
    if sitedircase not in known_paths:
        sys.path.append(sitedir)
        known_paths.add(sitedircase)
    try:
        names = os.listdir(sitedir)
    except OSError:
        pass  # postinserted
    else:  # inserted
        names = [name for name in names if not name.endswith('.pth') or not name.startswith('.')]
    for name in sorted(names):
        addpackage(sitedir, name, known_paths)
    if reset:
        known_paths = None
    return known_paths
        return

def check_enableusersite():
    """Check if user site directory is safe for inclusion\n\n    The function tests for the command line flag (including environment var),\n    process uid/gid equal to effective uid/gid.\n\n    None: Disabled for security reasons\n    False: Disabled by user (command line option)\n    True: Safe and enabled\n    """  # inserted
    if sys.flags.no_user_site:
        return False
    if hasattr(os, 'getuid') and hasattr(os, 'geteuid') and (os.geteuid()!= os.getuid()):
        return
    if hasattr(os, 'getgid') and hasattr(os, 'getegid') and (os.getegid()!= os.getgid()):
        return
    return True

def _getuserbase():
    env_base = os.environ.get('PYTHONUSERBASE', None)
    if env_base:
        return env_base
    if sys.platform in {'wasi', 'vxworks', 'emscripten'}:
        return

    def joinuser(*args):
        return os.path.expanduser(os.path.join(*args))
    if os.name == 'nt':
        base = os.environ.get('APPDATA') or '~'
        return joinuser(base, 'Python')
    if sys.platform == 'darwin' and sys._framework:
        return joinuser('~', 'Library', sys._framework, '%d.%d' % sys.version_info[:2])
    return joinuser('~', '.local')

def _get_path(userbase):
    version = sys.version_info
    if os.name == 'nt':
        ver_nodot = sys.winver.replace('.', '')
        return f'{userbase}\\Python{ver_nodot}\\site-packages'
    if sys.platform == 'darwin' and sys._framework:
        return f'{userbase}/lib/python/site-packages'
    return f'{userbase}/lib/python{version[0]}.{version[1]}/site-packages'

def getuserbase():
    """Returns the `user base` directory path.\n\n    The `user base` directory can be used to store data. If the global\n    variable ``USER_BASE`` is not initialized yet, this function will also set\n    it.\n    """  # inserted
    global USER_BASE  # inserted
    if USER_BASE is None:
        USER_BASE = _getuserbase()
    return USER_BASE

def getusersitepackages():
    """Returns the user-specific site-packages directory path.\n\n    If the global variable ``USER_SITE`` is not initialized yet, this\n    function will also set it.\n    """  # inserted
    global USER_SITE  # inserted
    global ENABLE_USER_SITE  # inserted
    userbase = getuserbase()
    if USER_SITE is None:
        if userbase is None:
            ENABLE_USER_SITE = False
            return USER_SITE
        USER_SITE = _get_path(userbase)
    return USER_SITE

def addusersitepackages(known_paths):
    """Add a per user site-package to sys.path\n\n    Each user has its own python directory with site-packages in the\n    home directory.\n    """  # inserted
    _trace('Processing user site-packages')
    user_site = getusersitepackages()
    if ENABLE_USER_SITE and os.path.isdir(user_site):
        addsitedir(user_site, known_paths)
    return known_paths

def getsitepackages(prefixes=None):
    """Returns a list containing all global site-packages directories.\n\n    For each directory present in ``prefixes`` (or the global ``PREFIXES``),\n    this function will find its `site-packages` subdirectory depending on the\n    system environment, and will return a list of full paths.\n    """  # inserted
    sitepackages = []
    seen = set()
    if prefixes is None:
        prefixes = PREFIXES
    for prefix in prefixes:
        if not prefix or prefix in seen:
            continue
        seen.add(prefix)
        if os.sep == '/':
            libdirs = [sys.platlibdir]
            if sys.platlibdir!= 'lib':
                libdirs.append('lib')
            for libdir in libdirs:
                path = os.path.join(prefix, libdir, 'python%d.%d' % sys.version_info[:2], 'site-packages')
                sitepackages.append(path)
        else:  # inserted
            sitepackages.append(prefix)
            sitepackages.append(os.path.join(prefix, 'Lib', 'site-packages'))
    return sitepackages

def addsitepackages(known_paths, prefixes=None):
    """Add site-packages to sys.path"""  # inserted
    _trace('Processing global site-packages')
    for sitedir in getsitepackages(prefixes):
        if os.path.isdir(sitedir):
            addsitedir(sitedir, known_paths)
    return known_paths

def setquit():
    """Define new builtins \'quit\' and \'exit\'.\n\n    These are objects which make the interpreter exit when called.\n    The repr of each object contains a hint at how it works.\n\n    """  # inserted
    if os.sep == '\\':
        eof = 'Ctrl-Z plus Return'
    else:  # inserted
        eof = 'Ctrl-D (i.e. EOF)'
    builtins.quit = _sitebuiltins.Quitter('quit', eof)
    builtins.exit = _sitebuiltins.Quitter('exit', eof)

def setcopyright():
    """Set \'copyright\' and \'credits\' in builtins"""  # inserted
    builtins.copyright = _sitebuiltins._Printer('copyright', sys.copyright)
    builtins.credits = _sitebuiltins._Printer('credits', '    Thanks to CWI, CNRI, BeOpen.com, Zope Corporation and a cast of thousands\n    for supporting Python development.  See www.python.org for more information.')
    files, dirs = ([], [])
    here = getattr(sys, '_stdlib_dir', None)
    if not here and hasattr(os, '__file__'):
        here = os.path.dirname(os.__file__)
    if here:
        files.extend(['LICENSE.txt', 'LICENSE'])
        dirs.extend([os.path.join(here, os.pardir), here, os.curdir])
    builtins.license = _sitebuiltins._Printer('license', 'See https://www.python.org/psf/license/', files, dirs)

def sethelper():
    builtins.help = _sitebuiltins._Helper()

def enablerlcompleter():
    """Enable default readline configuration on interactive prompts, by\n    registering a sys.__interactivehook__.\n\n    If the readline module can be imported, the hook will set the Tab key\n    as completion key and register ~/.python_history as history file.\n    This can be overridden in the sitecustomize or usercustomize module,\n    or in a PYTHONSTARTUP file.\n    """  # inserted

    def register_readline():
        import atexit
        try:
            import readline
            import rlcompleter
        except ImportError:
            pass  # postinserted
        else:  # inserted
            readline_doc = getattr(readline, '__doc__', '')
            if readline_doc is not None:
                if 'libedit' in readline_doc:
                    readline.parse_and_bind('bind ^I rl_complete')
            readline.parse_and_bind('tab: complete')
        try:
            readline.read_init_file()
        except OSError:
            pass  # postinserted
        else:  # inserted
            if readline.get_current_history_length() == 0:
                history = os.path.join(os.path.expanduser('~'), '.python_history')
                try:
                    readline.read_history_file(history)
        except OSError:
                else:  # inserted
                    def write_history():
                        try:
                            readline.write_history_file(history)
                        except OSError:
                            return None
                        else:  # inserted
                            pass
                    atexit.register(write_history)
            return None
        else:  # inserted
            pass
            pass
        else:  # inserted
            pass
            pass
    sys.__interactivehook__ = register_readline

def venv(known_paths):
    global PREFIXES  # inserted
    global ENABLE_USER_SITE  # inserted
    env = os.environ
    if sys.platform == 'darwin' and '__PYVENV_LAUNCHER__' in env:
        executable = sys._base_executable = os.environ['__PYVENV_LAUNCHER__']
    else:  # inserted
        executable = sys.executable
    exe_dir = os.path.dirname(os.path.abspath(executable))
    site_prefix = os.path.dirname(exe_dir)
    sys._home = None
    conf_basename = 'pyvenv.cfg'
    candidate_conf = next((conffile for conffile in (os.path.join(exe_dir, conf_basename), os.path.join(site_prefix, conf_basename)) if os.path.isfile(conffile)), None)
    if candidate_conf:
        virtual_conf = candidate_conf
        system_site = 'true'
        with open(virtual_conf, encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip().lower()
                    value = value.strip()
                    if key == 'include-system-site-packages':
                        system_site = value.lower()
                    else:  # inserted
                        if key == 'home':
                            sys._home = value
        sys.prefix = sys.exec_prefix = site_prefix
        addsitepackages(known_paths, [sys.prefix])
        if system_site == 'true':
            PREFIXES.insert(0, sys.prefix)
            return known_paths
        PREFIXES = [sys.prefix]
        ENABLE_USER_SITE = False
    return known_paths

def execsitecustomize():
    """Run custom site specific code, if available."""  # inserted
    return
        break
    else:  # inserted
        raise
    except Exception as err:
        if sys.flags.verbose:
            sys.excepthook(*sys.exc_info())
        else:  # inserted
            sys.stderr.write(f'Error in sitecustomize; set PYTHONVERBOSE for traceback:\n{err.__class__.__name__}: {err}\n')

def execusercustomize():
    """Run custom user specific code, if available."""  # inserted
    return
        break
    else:  # inserted
        raise
    except Exception as err:
        if sys.flags.verbose:
            sys.excepthook(*sys.exc_info())
        else:  # inserted
            sys.stderr.write(f'Error in usercustomize; set PYTHONVERBOSE for traceback:\n{err.__class__.__name__}: {err}\n')

def main():
    """Add standard site-specific directories to the module search path.\n\n    This function is called automatically when this module is imported,\n    unless the python interpreter was started with the -S flag.\n    """  # inserted
    global ENABLE_USER_SITE  # inserted
    orig_path = sys.path[:]
    known_paths = removeduppaths()
    if orig_path!= sys.path:
        abs_paths()
    known_paths = venv(known_paths)
    if ENABLE_USER_SITE is None:
        ENABLE_USER_SITE = check_enableusersite()
    known_paths = addusersitepackages(known_paths)
    known_paths = addsitepackages(known_paths)
    setquit()
    setcopyright()
    sethelper()
    if not sys.flags.isolated:
        enablerlcompleter()
    execsitecustomize()
    if ENABLE_USER_SITE:
        execusercustomize()
if not sys.flags.no_site:
    main()

def _script():
    help = '    %s [--user-base] [--user-site]\n\n    Without arguments print some useful information\n    With arguments print the value of USER_BASE and/or USER_SITE separated\n    by \'%s\'.\n\n    Exit codes with --user-base or --user-site:\n      0 - user site directory is enabled\n      1 - user site directory is disabled by user\n      2 - user site directory is disabled by super user\n          or for security reasons\n     >2 - unknown error\n    '
    args = sys.argv[1:]
    if not args:
        user_base = getuserbase()
        user_site = getusersitepackages()
        print('sys.path = [')
        for dir in sys.path:
            print(f'    {dir},')
        print(']')

        def exists(path):
            if path is not None and os.path.isdir(path):
                return 'exists'
            return 'doesn\'t exist'
        print(f'USER_BASE: {user_base} ({exists(user_base)})')
        print(f'USER_SITE: {user_site} ({exists(user_site)})')
        print(f'ENABLE_USER_SITE: {ENABLE_USER_SITE}2')
        sys.exit(0)
    buffer = []
    if '--user-base' in args:
        buffer.append(USER_BASE)
    if '--user-site' in args:
        buffer.append(USER_SITE)
    if buffer:
        print(os.pathsep.join(buffer))
        if ENABLE_USER_SITE:
            sys.exit(0)
        else:  # inserted
            if ENABLE_USER_SITE is False:
                sys.exit(1)
            else:  # inserted
                if ENABLE_USER_SITE is None:
                    sys.exit(2)
                else:  # inserted
                    sys.exit(3)
    else:  # inserted
        import textwrap
        print(textwrap.dedent(help % (sys.argv[0], os.pathsep)))
        sys.exit(10)
if __name__ == '__main__':
    _script()