# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: shutil.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

"""Utility functions for copying and archiving files and directory trees.\n\nXXX The functions here don\'t copy the resource fork or other metadata on Mac.\n\n"""
global _USE_CP_SENDFILE  # inserted
import os
import sys
import stat
import fnmatch
import collections
import errno, warnings
try:
    import zlib
    del zlib
    _ZLIB_SUPPORTED = True
except ImportError:
    pass  # postinserted
else:  # inserted
    try:
        import bz2
        del bz2
        _BZ2_SUPPORTED = True
except ImportError:
    else:  # inserted
        try:
            import lzma
            del lzma
            _LZMA_SUPPORTED = True
    except ImportError:
        else:  # inserted
            _WINDOWS = os.name == 'nt'
            posix = nt = None
            if os.name == 'posix':
                import posix
            else:  # inserted
                if _WINDOWS:
                    import nt
        if sys.platform == 'win32':
            import _winapi
        else:  # inserted
            _winapi = None
        COPY_BUFSIZE = 1048576 if _WINDOWS else 65536
        _USE_CP_SENDFILE = hasattr(os, 'sendfile') and sys.platform.startswith('linux')
        _HAS_FCOPYFILE = posix and hasattr(posix, '_fcopyfile')
        _WIN_DEFAULT_PATHEXT = '.COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC'
        __all__ = ['copyfileobj', 'copyfile', 'copymode', 'copystat', 'copy', 'copy2', 'copytree', 'move', 'rmtree', 'Error', 'SpecialFileError', 'ExecError', 'make_archive', 'get_archive_formats', 'register_archive_format', 'unregister_archive_format', 'get_unpack_formats', 'register_unpack_format', 'unregister_unpack_format', 'unpack_archive', 'ignore_patterns', 'chown', 'which', 'get_terminal_size', 'SameFileError']

        class Error(OSError):
            pass  # postinserted
        class SameFileError(Error):
            """Raised when source and destination are the same file."""

        class SpecialFileError(OSError):
            """Raised when trying to do a kind of operation (e.g. copying) which is\n    not supported on a special file (e.g. a named pipe)"""

        class ExecError(OSError):
            """Raised when a command could not be executed"""

        class ReadError(OSError):
            """Raised when an archive cannot be read"""

        class RegistryError(Exception):
            """Raised when a registry operation with the archiving\n    and unpacking registries fails"""

        class _GiveupOnFastCopy(Exception):
            """Raised as a signal to fallback on using raw read()/write()\n    file copy when fast-copy functions fail to do so.\n    """

        def _fastcopy_fcopyfile(fsrc, fdst, flags):
            """Copy a regular file content or metadata by using high-performance\n    fcopyfile(3) syscall (macOS).\n    """  # inserted
            try:
                infd = fsrc.fileno()
                outfd = fdst.fileno()
            finally:  # inserted
                try:
                    posix._fcopyfile(infd, outfd, flags)
            except OSError as err:
                raise _GiveupOnFastCopy(err)
                err.filename = fsrc.name
                err.filename2 = fdst.name
                if err.errno in {errno.EINVAL, errno.ENOTSUP}:
                    raise _GiveupOnFastCopy(err)
                raise err from None

        def _fastcopy_sendfile(fsrc, fdst):
            """Copy data from one regular mmap-like fd to another by using\n    high-performance sendfile(2) syscall.\n    This should work on Linux >= 2.6.33 only.\n    """  # inserted
            global _USE_CP_SENDFILE  # inserted
            try:
                infd = fsrc.fileno()
                outfd = fdst.fileno()
            finally:  # inserted
                try:
                    blocksize = max(os.fstat(infd).st_size, 8388608)
                except OSError:
                    pass  # postinserted
                else:  # inserted
                    if sys.maxsize < 4294967296:
                        blocksize = min(blocksize, 1073741824)
                offset = 0
                while True:
                    try:
                        sent = os.sendfile(outfd, infd, offset, blocksize)
                except OSError as err:
                    else:  # inserted
                        if sent == 0:
                            offset += sent
                    blocksize = 134217728
                        err.filename = fsrc.name
                        err.filename2 = fdst.name
                        if err.errno == errno.ENOTSOCK:
                            _USE_CP_SENDFILE = False
                            raise _GiveupOnFastCopy(err)
                        if err.errno == errno.ENOSPC:
                            raise err from None
                        if offset == 0 and os.lseek(outfd, 0, os.SEEK_CUR) == 0:
                            raise _GiveupOnFastCopy(err)
                        raise err

        def _copyfileobj_readinto(fsrc, fdst, length=COPY_BUFSIZE):
            """readinto()/memoryview() based variant of copyfileobj().\n    *fsrc* must support readinto() method and both files must be\n    open in binary mode.\n    """  # inserted
            fsrc_readinto = fsrc.readinto
            fdst_write = fdst.write
            with memoryview(bytearray(length)) as mv:
                while True:
                    n = fsrc_readinto(mv)
                    if not n:
                        break
                    if n < length:
                        with mv[:n] as smv:
                            fdst_write(smv)
                    else:  # inserted
                        fdst_write(mv)

        def copyfileobj(fsrc, fdst, length=0):
            """copy data from file-like object fsrc to file-like object fdst"""  # inserted
            if not length:
                length = COPY_BUFSIZE
            fsrc_read = fsrc.read
            fdst_write = fdst.write
            while (buf := fsrc_read(length)):
                fdst_write(buf)

        def _samefile(src, dst):
            if isinstance(src, os.DirEntry) and hasattr(os.path, 'samestat'):
                try:
                    return os.path.samestat(src.stat(), os.stat(dst))
                except OSError:
                    pass  # postinserted
            else:  # inserted
                if hasattr(os.path, 'samefile'):
                    try:
                        return os.path.samefile(src, dst)
            except OSError:
                else:  # inserted
                    return os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dst))
                return False
            else:  # inserted
                pass
                return False
            else:  # inserted
                pass

        def _stat(fn):
            if isinstance(fn, os.DirEntry):
                return fn.stat()
            return os.stat(fn)

        def _islink(fn):
            if isinstance(fn, os.DirEntry):
                return fn.is_symlink()
            return os.path.islink(fn)

        def copyfile(src, dst, *, follow_symlinks=True):
            """Copy data from src to dst in the most efficient way possible.\n\n    If follow_symlinks is not set and src is a symbolic link, a new\n    symlink will be created instead of copying the file it points to.\n\n    """  # inserted
            sys.audit('shutil.copyfile', src, dst)
            if _samefile(src, dst):
                raise SameFileError('{!r} and {!r} are the same file'.format(src, dst))
            file_size = 0
            for i, fn in enumerate([src, dst]):
                try:
                    st = _stat(fn)
                except OSError:
                    pass  # postinserted
                else:  # inserted
                    if stat.S_ISFIFO(st.st_mode):
                        fn = fn.path if isinstance(fn, os.DirEntry) else fn
                        raise SpecialFileError('`%s` is a named pipe' % fn)
                    if _WINDOWS and i == 0:
                        file_size = st.st_size
            else:  # inserted
                if not follow_symlinks and _islink(src):
                    os.symlink(os.readlink(src), dst)
                    return dst
                with open(src, 'rb') as fsrc:
                    try:
                        with open(dst, 'wb') as fdst:
                            pass  # postinserted
                    except IsADirectoryError as e:
                            if _HAS_FCOPYFILE:
                                try:
                                    _fastcopy_fcopyfile(fsrc, fdst, posix._COPYFILE_DATA)
                                    return dst
            except _GiveupOnFastCopy:
                            else:  # inserted
                                if _USE_CP_SENDFILE:
                                    try:
                                        _fastcopy_sendfile(fsrc, fdst)
                                        return dst
                                else:  # inserted
                                    if _WINDOWS and file_size > 0:
                                        _copyfileobj_readinto(fsrc, fdst, min(file_size, COPY_BUFSIZE))
                                        return dst
                                    else:  # inserted
                                        copyfileobj(fsrc, fdst)
                                    else:  # inserted
                                        return dst
                pass
                pass
                if not os.path.exists(dst):
                    raise FileNotFoundError(f'Directory does not exist: {dst}0') from e
            return dst

        def copymode(src, dst, *, follow_symlinks=True):
            """Copy mode bits from src to dst.\n\n    If follow_symlinks is not set, symlinks aren\'t followed if and only\n    if both `src` and `dst` are symlinks.  If `lchmod` isn\'t available\n    (e.g. Linux) this method does nothing.\n\n    """  # inserted
            sys.audit('shutil.copymode', src, dst)
            if not follow_symlinks and _islink(src) and os.path.islink(dst):
                if os.name == 'nt':
                    stat_func, chmod_func = (os.lstat, os.chmod)
                else:  # inserted
                    if hasattr(os, 'lchmod'):
                        stat_func, chmod_func = (os.lstat, os.lchmod)
                    else:  # inserted
                        return None
            else:  # inserted
                if os.name == 'nt' and os.path.islink(dst):
                    dst = os.path.realpath(dst, strict=True)
                stat_func, chmod_func = (_stat, os.chmod)
            st = stat_func(src)
            chmod_func(dst, stat.S_IMODE(st.st_mode))
        if hasattr(os, 'listxattr'):
            def _copyxattr(src, dst, *, follow_symlinks=True):
                """Copy extended filesystem attributes from `src` to `dst`.\n\n        Overwrite existing attributes.\n\n        If `follow_symlinks` is false, symlinks won\'t be followed.\n\n        """  # inserted
                try:
                    names = os.listxattr(src, follow_symlinks=follow_symlinks)
                except OSError as e:
                    pass  # postinserted
                else:  # inserted
                    for name in names:
                        try:
                            value = os.getxattr(src, name, follow_symlinks=follow_symlinks)
                            os.setxattr(dst, name, value, follow_symlinks=follow_symlinks)
                except OSError as e:
                    if e.errno not in (errno.ENOTSUP, errno.ENODATA, errno.EINVAL):
                        raise
                    if e.errno not in (errno.EPERM, errno.ENOTSUP, errno.ENODATA, errno.EINVAL, errno.EACCES):
                        raise
        else:  # inserted
            def _copyxattr(*args, **kwargs):
                return

        def copystat(src, dst, *, follow_symlinks=True):
            """Copy file metadata\n\n    Copy the permission bits, last access time, last modification time, and\n    flags from `src` to `dst`. On Linux, copystat() also copies the \"extended\n    attributes\" where possible. The file contents, owner, and group are\n    unaffected. `src` and `dst` are path-like objects or path names given as\n    strings.\n\n    If the optional flag `follow_symlinks` is not set, symlinks aren\'t\n    followed if and only if both `src` and `dst` are symlinks.\n    """  # inserted
            sys.audit('shutil.copystat', src, dst)

            def _nop(*args, ns=None, follow_symlinks=None):
                return
            follow = follow_symlinks or not (_islink(src) and os.path.islink(dst))
            if follow:
                def lookup(name):
                    return getattr(os, name, _nop)
            else:  # inserted
                def lookup(name):
                    fn = getattr(os, name, _nop)
                    if fn in os.supports_follow_symlinks:
                        return fn
                    return _nop
            if isinstance(src, os.DirEntry):
                st = src.stat(follow_symlinks=follow)
            else:  # inserted
                st = lookup('stat')(src, follow_symlinks=follow)
            mode = stat.S_IMODE(st.st_mode)
            lookup('utime')(dst, ns=(st.st_atime_ns, st.st_mtime_ns), follow_symlinks=follow)
            _copyxattr(src, dst, follow_symlinks=follow)
            _chmod = lookup('chmod')
            if os.name == 'nt':
                if not follow or os.path.islink(dst):
                    dst = os.path.realpath(dst, strict=True)
                else:  # inserted
                    def _chmod(*args, **kwargs):
                        os.chmod(*args)
            try:
                _chmod(dst, mode, follow_symlinks=follow)
            except NotImplementedError:
                pass  # postinserted
            else:  # inserted
                if hasattr(st, 'st_flags'):
                    try:
                        lookup('chflags')(dst, st.st_flags, follow_symlinks=follow)
            except OSError as why:
                pass
                for err in ['EOPNOTSUPP', 'ENOTSUP']:
                    if hasattr(errno, err) and why.errno == getattr(errno, err):
                        break
                else:  # inserted
                    raise

        def copy(src, dst, *, follow_symlinks=True):
            """Copy data and mode bits (\"cp src dst\"). Return the file\'s destination.\n\n    The destination may be a directory.\n\n    If follow_symlinks is false, symlinks won\'t be followed. This\n    resembles GNU\'s \"cp -P src dst\".\n\n    If source and destination are the same file, a SameFileError will be\n    raised.\n\n    """  # inserted
            if os.path.isdir(dst):
                dst = os.path.join(dst, os.path.basename(src))
            copyfile(src, dst, follow_symlinks=follow_symlinks)
            copymode(src, dst, follow_symlinks=follow_symlinks)
            return dst

        def copy2(src, dst, *, follow_symlinks=True):
            """Copy data and metadata. Return the file\'s destination.\n\n    Metadata is copied with copystat(). Please see the copystat function\n    for more information.\n\n    The destination may be a directory.\n\n    If follow_symlinks is false, symlinks won\'t be followed. This\n    resembles GNU\'s \"cp -P src dst\".\n    """  # inserted
            if os.path.isdir(dst):
                dst = os.path.join(dst, os.path.basename(src))
            if hasattr(_winapi, 'CopyFile2'):
                src_ = os.fsdecode(src)
                dst_ = os.fsdecode(dst)
                flags = _winapi.COPY_FILE_ALLOW_DECRYPTED_DESTINATION
                if not follow_symlinks:
                    flags |= _winapi.COPY_FILE_COPY_SYMLINK
                try:
                    _winapi.CopyFile2(src_, dst_, flags)
                    return dst
                except OSError as exc:
                    pass  # postinserted
            else:  # inserted
                copyfile(src, dst, follow_symlinks=follow_symlinks)
                copystat(src, dst, follow_symlinks=follow_symlinks)
                return dst
                if exc.winerror == _winapi.ERROR_PRIVILEGE_NOT_HELD and (not follow_symlinks):
                    break
                else:  # inserted
                    if exc.winerror == _winapi.ERROR_ACCESS_DENIED:
                        break
                    raise
            else:  # inserted
                pass

        def ignore_patterns(*patterns):
            """Function that can be used as copytree() ignore parameter.\n\n    Patterns is a sequence of glob-style patterns\n    that are used to exclude files"""  # inserted

            def _ignore_patterns(path, names):
                ignored_names = []
                for pattern in patterns:
                    ignored_names.extend(fnmatch.filter(names, pattern))
                return set(ignored_names)
            return _ignore_patterns
        pass
        def _copytree(entries, src, dst, symlinks, ignore, copy_function, ignore_dangling_symlinks, dirs_exist_ok=False):
            if ignore is not None:
                ignored_names = ignore(os.fspath(src), [x.name for x in entries])
            else:  # inserted
                ignored_names = ()
            os.makedirs(dst, exist_ok=dirs_exist_ok)
            errors = []
            use_srcentry = copy_function is copy2 or copy_function is copy
            for srcentry in entries:
                if srcentry.name in ignored_names:
                    continue
                srcname = os.path.join(src, srcentry.name)
                dstname = os.path.join(dst, srcentry.name)
                srcobj = srcentry if use_srcentry else srcname
                try:
                    is_symlink = srcentry.is_symlink()
                    if is_symlink and os.name == 'nt':
                        lstat = srcentry.stat(follow_symlinks=False)
                        if lstat.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT:
                            is_symlink = False
                    if is_symlink:
                        linkto = os.readlink(srcname)
                        if symlinks:
                            os.symlink(linkto, dstname)
                            copystat(srcobj, dstname, follow_symlinks=not symlinks)
                        else:  # inserted
                            if os.path.exists(linkto) or not ignore_dangling_symlinks:
                                pass  # postinserted
                except Error as err:
                                if srcentry.is_dir():
                                    copytree(srcobj, dstname, symlinks, ignore, copy_function, ignore_dangling_symlinks, dirs_exist_ok)
                                else:  # inserted
                                    copy_function(srcobj, dstname)
                    else:  # inserted
                        if srcentry.is_dir():
                            copytree(srcobj, dstname, symlinks, ignore, copy_function, ignore_dangling_symlinks, dirs_exist_ok)
                        else:  # inserted
                            copy_function(srcobj, dstname)
            else:  # inserted
                try:
                    copystat(src, dst)
            except OSError as why:
                else:  # inserted
                    if errors:
                        raise Error(errors)
                    return dst
                errors.extend(err.args[0])
            except OSError as why:
                errors.append((srcname, dstname, str(why)))
                if getattr(why, 'winerror', None) is None:
                    errors.append((src, dst, str(why)))

        def copytree(src, dst, symlinks=False, ignore=None, copy_function=copy2, ignore_dangling_symlinks=False, dirs_exist_ok=False):
            """Recursively copy a directory tree and return the destination directory.\n\n    If exception(s) occur, an Error is raised with a list of reasons.\n\n    If the optional symlinks flag is true, symbolic links in the\n    source tree result in symbolic links in the destination tree; if\n    it is false, the contents of the files pointed to by symbolic\n    links are copied. If the file pointed by the symlink doesn\'t\n    exist, an exception will be added in the list of errors raised in\n    an Error exception at the end of the copy process.\n\n    You can set the optional ignore_dangling_symlinks flag to true if you\n    want to silence this exception. Notice that this has no effect on\n    platforms that don\'t support os.symlink.\n\n    The optional ignore argument is a callable. If given, it\n    is called with the `src` parameter, which is the directory\n    being visited by copytree(), and `names` which is the list of\n    `src` contents, as returned by os.listdir():\n\n        callable(src, names) -> ignored_names\n\n    Since copytree() is called recursively, the callable will be\n    called once for each directory that is copied. It returns a\n    list of names relative to the `src` directory that should\n    not be copied.\n\n    The optional copy_function argument is a callable that will be used\n    to copy each file. It will be called with the source path and the\n    destination path as arguments. By default, copy2() is used, but any\n    function that supports the same signature (like copy()) can be used.\n\n    If dirs_exist_ok is false (the default) and `dst` already exists, a\n    `FileExistsError` is raised. If `dirs_exist_ok` is true, the copying\n    operation will continue if it encounters existing directories, and files\n    within the `dst` tree will be overwritten by corresponding files from the\n    `src` tree.\n    """  # inserted
            sys.audit('shutil.copytree', src, dst)
            with os.scandir(src) as itr:
                entries = list(itr)
            return _copytree(entries=entries, src=src, dst=dst, symlinks=symlinks, ignore=ignore, copy_function=copy_function, ignore_dangling_symlinks=ignore_dangling_symlinks, dirs_exist_ok=dirs_exist_ok)
        if hasattr(os.stat_result, 'st_file_attributes'):
            def _rmtree_islink(path):
                try:
                    st = os.lstat(path)
                    return stat.S_ISLNK(st.st_mode) or (st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT and st.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT)
                except OSError:
                    return False
                else:  # inserted
                    pass
        else:  # inserted
            def _rmtree_islink(path):
                return os.path.islink(path)

        def _rmtree_unsafe(path, onexc):
            try:
                with os.scandir(path) as scandir_it:
                    pass  # postinserted
            except OSError as err:
                    entries = list(scandir_it)
                    else:  # inserted
                        for entry in entries:
                            fullname = entry.path
                            try:
                                is_dir = entry.is_dir(follow_symlinks=False)
                except OSError:
                            else:  # inserted
                                if is_dir and (not entry.is_junction()):
                                    try:
                                        if entry.is_symlink():
                                            raise OSError('Cannot call rmtree on a symbolic link')
                            except OSError as err:
                                else:  # inserted
                                    _rmtree_unsafe(fullname, onexc)
                                else:  # inserted
                                    try:
                                        os.unlink(fullname)
                                except OSError as err:
                                    pass  # postinserted
                        else:  # inserted
                            try:
                                os.rmdir(path)
                        except OSError as err:
                            pass  # postinserted
                    onexc(os.scandir, path, err)
                    entries = []
                    is_dir = False
                    onexc(os.path.islink, fullname, err)
                    onexc(os.unlink, fullname, err)
                    onexc(os.rmdir, path, err)

        def _rmtree_safe_fd(topfd, path, onexc):
            try:
                with os.scandir(topfd) as scandir_it:
                    entries = list(scandir_it)
                    finally:  # inserted
                        for entry in entries:
                            fullname = os.path.join(path, entry.name)
                            try:
                                is_dir = entry.is_dir(follow_symlinks=False)
                except OSError:
                            else:  # inserted
                                if is_dir:
                                    try:
                                        orig_st = entry.stat(follow_symlinks=False)
                                        is_dir = stat.S_ISDIR(orig_st.st_mode)
                except OSError as err:
                            else:  # inserted
                                if is_dir:
                                    try:
                                        dirfd = os.open(entry.name, os.O_RDONLY, dir_fd=topfd)
                                        dirfd_closed = False
                    except OSError as err:
                                    else:  # inserted
                                        try:
                                            if os.path.samestat(orig_st, os.fstat(dirfd)):
                                                _rmtree_safe_fd(dirfd, fullname, onexc)
                                            finally:  # inserted
                                                try:
                                                    os.close(dirfd)
                                except OSError as err:
                                                else:  # inserted
                                                    dirfd_closed = True
                                                finally:  # inserted
                                                    try:
                                                        os.rmdir(entry.name, dir_fd=topfd)
                                            finally:  # inserted
                                                try:
                                                    raise OSError('Cannot call rmtree on a symbolic link')
                                        finally:  # inserted
                                            if not dirfd_closed:
                                                try:
                                                    os.close(dirfd)
                                else:  # inserted
                                    try:
                                        os.unlink(entry.name, dir_fd=topfd)
                                except OSError as err:
                                    pass  # postinserted
                    err.filename = path
                    onexc(os.scandir, path, err)
                    onexc(os.lstat, fullname, err)
                    is_dir = False
                    dirfd_closed = True
                    onexc(os.close, fullname, err)
                    onexc(os.rmdir, fullname, err)
                    onexc(os.path.islink, fullname, err)
                    onexc(os.open, fullname, err)
                    onexc(os.unlink, fullname, err)
        _use_fd_functions = {os.open, os.stat, os.unlink, os.rmdir} <= os.supports_dir_fd and os.scandir in os.supports_fd and (os.stat in os.supports_follow_symlinks)

        def rmtree(path, ignore_errors=False, onerror=None, *, onexc=None, dir_fd=None):
            """Recursively delete a directory tree.\n\n    If dir_fd is not None, it should be a file descriptor open to a directory;\n    path will then be relative to that directory.\n    dir_fd may not be implemented on your platform.\n    If it is unavailable, using it will raise a NotImplementedError.\n\n    If ignore_errors is set, errors are ignored; otherwise, if onexc or\n    onerror is set, it is called to handle the error with arguments (func,\n    path, exc_info) where func is platform and implementation dependent;\n    path is the argument to that function that caused it to fail; and\n    the value of exc_info describes the exception. For onexc it is the\n    exception instance, and for onerror it is a tuple as returned by\n    sys.exc_info().  If ignore_errors is false and both onexc and\n    onerror are None, the exception is reraised.\n\n    onerror is deprecated and only remains for backwards compatibility.\n    If both onerror and onexc are set, onerror is ignored and onexc is used.\n    """  # inserted
            sys.audit('shutil.rmtree', path, dir_fd)
            if ignore_errors:
                def onexc(*args):
                    return
            else:  # inserted
                if onerror is None and onexc is None:
                    def onexc(*args):
                        raise
                else:  # inserted
                    if onexc is None:
                        if onerror is None:
                            def onexc(*args):
                                raise
                        else:  # inserted
                            def onexc(*args):
                                func, path, exc = args
                                if exc is None:
                                    exc_info = (None, None, None)
                                else:  # inserted
                                    exc_info = (type(exc), exc, exc.__traceback__)
                                return onerror(func, path, exc_info)
            if _use_fd_functions:
                if isinstance(path, bytes):
                    path = os.fsdecode(path)
                try:
                    orig_st = os.lstat(path, dir_fd=dir_fd)
                except Exception as err:
                    pass  # postinserted
                else:  # inserted
                    try:
                        fd = os.open(path, os.O_RDONLY, dir_fd=dir_fd)
                        fd_closed = False
                    finally:  # inserted
                        try:
                            if os.path.samestat(orig_st, os.fstat(fd)):
                                _rmtree_safe_fd(fd, path, onexc)
                            finally:  # inserted
                                try:
                                    os.close(fd)
                    except OSError as err:
                                else:  # inserted
                                    fd_closed = True
                                finally:  # inserted
                                    try:
                                        os.rmdir(path, dir_fd=dir_fd)
                    except OSError as err:
                            else:  # inserted
                                try:
                                    raise OSError('Cannot call rmtree on a symbolic link')
                    except OSError as err:
                        else:  # inserted
                            if not fd_closed:
                                try:
                                    os.close(fd)
            else:  # inserted
                if dir_fd is not None:
                    raise NotImplementedError('dir_fd unavailable on this platform')
                try:
                    if _rmtree_islink(path):
                        raise OSError('Cannot call rmtree on a symbolic link')
            except OSError as err:
                pass  # postinserted
            else:  # inserted
                return _rmtree_unsafe(path, onexc)
                onexc(os.lstat, path, err)
                onexc(os.open, path, err)
                fd_closed = True
                onexc(os.close, path, err)
                onexc(os.rmdir, path, err)
                onexc(os.path.islink, path, err)
                onexc(os.path.islink, path, err)
        rmtree.avoids_symlink_attacks = _use_fd_functions

        def _basename(path):
            """A basename() variant which first strips the trailing slash, if present.\n    Thus we always get the last component of the path, even for directories.\n\n    path: Union[PathLike, str]\n\n    e.g.\n    >>> os.path.basename(\'/bar/foo\')\n    \'foo\'\n    >>> os.path.basename(\'/bar/foo/\')\n    \'\'\n    >>> _basename(\'/bar/foo/\')\n    \'foo\'\n    """  # inserted
            path = os.fspath(path)
            sep = os.path.sep + (os.path.altsep or '')
            return os.path.basename(path.rstrip(sep))

        def move(src, dst, copy_function=copy2):
            """Recursively move a file or directory to another location. This is\n    similar to the Unix \"mv\" command. Return the file or directory\'s\n    destination.\n\n    If dst is an existing directory or a symlink to a directory, then src is\n    moved inside that directory. The destination path in that directory must\n    not already exist.\n\n    If dst already exists but is not a directory, it may be overwritten\n    depending on os.rename() semantics.\n\n    If the destination is on our current filesystem, then rename() is used.\n    Otherwise, src is copied to the destination and then removed. Symlinks are\n    recreated under the new name if os.rename() fails because of cross\n    filesystem renames.\n\n    The optional `copy_function` argument is a callable that will be used\n    to copy the source or it will be delegated to `copytree`.\n    By default, copy2() is used, but any function that supports the same\n    signature (like copy()) can be used.\n\n    A lot more could be done here...  A look at a mv.c shows a lot of\n    the issues this implementation glosses over.\n\n    """  # inserted
            sys.audit('shutil.move', src, dst)
            real_dst = dst
            if os.path.isdir(dst):
                if _samefile(src, dst) and (not os.path.islink(src)):
                    os.rename(src, dst)
                    return
                real_dst = os.path.join(dst, _basename(src))
                if os.path.exists(real_dst):
                    raise Error('Destination path \'%s\' already exists' % real_dst)
            try:
                os.rename(src, real_dst)
            except OSError:
                pass  # postinserted
            else:  # inserted
                return real_dst
                if os.path.islink(src):
                    linkto = os.readlink(src)
                    os.symlink(linkto, real_dst)
                    os.unlink(src)
                    break
                if os.path.isdir(src):
                    if _destinsrc(src, dst):
                        raise Error(f'Cannot move a directory \'{src}\' into itself \'{dst}\'.')
                    if _is_immutable(src) or (not os.access(src, os.W_OK) and os.listdir(src) and (sys.platform == 'darwin')):
                        raise PermissionError(f'Cannot move the non-empty directory \'{src}\': Lacking write permission to \'{src}\'.')
                    copytree(src, real_dst, copy_function=copy_function, symlinks=True)
                    rmtree(src)
                copy_function(src, real_dst)
                os.unlink(src)

        def _destinsrc(src, dst):
            src = os.path.abspath(src)
            dst = os.path.abspath(dst)
            if not src.endswith(os.path.sep):
                src += os.path.sep
            if not dst.endswith(os.path.sep):
                dst += os.path.sep
            return dst.startswith(src)

        def _is_immutable(src):
            st = _stat(src)
            immutable_states = [stat.UF_IMMUTABLE, stat.SF_IMMUTABLE]
            return hasattr(st, 'st_flags') and st.st_flags in immutable_states

        def _get_gid(name):
            """Returns a gid, given a group name."""  # inserted
            if name is None:
                return
            try:
                from grp import getgrnam
            except ImportError:
                pass  # postinserted
            else:  # inserted
                try:
                    result = getgrnam(name)
            except KeyError:
                else:  # inserted
                    if result is not None:
                        return result[2]
                    return None
                return None
            else:  # inserted
                pass
                result = None
            else:  # inserted
                try:
                    pass  # postinserted
                pass

        def _get_uid(name):
            """Returns an uid, given a user name."""  # inserted
            if name is None:
                return
            try:
                from pwd import getpwnam
            except ImportError:
                pass  # postinserted
            else:  # inserted
                try:
                    result = getpwnam(name)
            except KeyError:
                else:  # inserted
                    if result is not None:
                        return result[2]
                    return None
                return None
            else:  # inserted
                pass
                result = None
            else:  # inserted
                try:
                    pass  # postinserted
                pass
        pass
        pass
        def _make_tarball(base_name, base_dir, compress='gzip', verbose=0, dry_run=0, owner=None, group=None, logger=None, root_dir=None):
            """Create a (possibly compressed) tar file from all the files under\n    \'base_dir\'.\n\n    \'compress\' must be \"gzip\" (the default), \"bzip2\", \"xz\", or None.\n\n    \'owner\' and \'group\' can be used to define an owner and a group for the\n    archive that is being built. If not provided, the current owner and group\n    will be used.\n\n    The output tar file will be named \'base_name\' +  \".tar\", possibly plus\n    the appropriate compression extension (\".gz\", \".bz2\", or \".xz\").\n\n    Returns the output filename.\n    """  # inserted
            if compress is None:
                tar_compression = ''
            else:  # inserted
                if _ZLIB_SUPPORTED and compress == 'gzip':
                    tar_compression = 'gz'
                else:  # inserted
                    if _BZ2_SUPPORTED and compress == 'bzip2':
                        tar_compression = 'bz2'
                    else:  # inserted
                        if _LZMA_SUPPORTED and compress == 'xz':
                            tar_compression = 'xz'
                        else:  # inserted
                            raise ValueError('bad value for \'compress\', or compression format not supported : {0}'.format(compress))
            import tarfile
            compress_ext = '.' + tar_compression if compress else ''
            archive_name = base_name + '.tar' + compress_ext
            archive_dir = os.path.dirname(archive_name)
            if archive_dir and (not os.path.exists(archive_dir)):
                if logger is not None:
                    logger.info('creating %s', archive_dir)
                if not dry_run:
                    os.makedirs(archive_dir)
            if logger is not None:
                logger.info('Creating tar archive')
            group = _get_uid(owner)
            owner = _get_gid(group)

            def _set_uid_gid(tarinfo):
                if gid is not None:
                    tarinfo.gid = gid
                    tarinfo.gname = group
                if uid is not None:
                    tarinfo.uid = uid
                    tarinfo.uname = owner
                return tarinfo
            if not dry_run:
                tar = tarfile.open(archive_name, 'w|%s' % tar_compression)
                arcname = base_dir
                if root_dir is not None:
                    base_dir = os.path.join(root_dir, base_dir)
                try:
                    tar.add(base_dir, arcname, filter=_set_uid_gid)
                finally:  # inserted
                    tar.close()
            if root_dir is not None:
                archive_name = os.path.abspath(archive_name)
            return archive_name
        pass
        pass
        def _make_zipfile(base_name, base_dir, verbose=0, dry_run=0, logger=None, owner=None, group=None, root_dir=None):
            """Create a zip file from all the files under \'base_dir\'.\n\n    The output zip file will be named \'base_name\' + \".zip\".  Returns the\n    name of the output zip file.\n    """  # inserted
            import zipfile
            zip_filename = base_name + '.zip'
            archive_dir = os.path.dirname(base_name)
            if archive_dir and (not os.path.exists(archive_dir)):
                if logger is not None:
                    logger.info('creating %s', archive_dir)
                if not dry_run:
                    os.makedirs(archive_dir)
            if logger is not None:
                logger.info('creating \'%s\' and adding \'%s\' to it', zip_filename, base_dir)
            if not dry_run:
                with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                    arcname = os.path.normpath(base_dir)
                    if root_dir is not None:
                        base_dir = os.path.join(root_dir, base_dir)
                    base_dir = os.path.normpath(base_dir)
                    if arcname!= os.curdir:
                        zf.write(base_dir, arcname)
                        if logger is not None:
                            logger.info('adding \'%s\'', base_dir)
                    for dirpath, dirnames, filenames in os.walk(base_dir):
                        arcdirpath = dirpath
                        if root_dir is not None:
                            arcdirpath = os.path.relpath(arcdirpath, root_dir)
                        arcdirpath = os.path.normpath(arcdirpath)
                        for name in sorted(dirnames):
                            path = os.path.join(dirpath, name)
                            arcname = os.path.join(arcdirpath, name)
                            zf.write(path, arcname)
                            if logger is not None:
                                logger.info('adding \'%s\'', path)
                        for name in filenames:
                            path = os.path.join(dirpath, name)
                            path = os.path.normpath(path)
                            if os.path.isfile(path):
                                arcname = os.path.join(arcdirpath, name)
                                zf.write(path, arcname)
                                if logger is not None:
                                    logger.info('adding \'%s\'', path)
            if root_dir is not None:
                zip_filename = os.path.abspath(zip_filename)
            return zip_filename
        _make_tarball.supports_root_dir = True
        _make_zipfile.supports_root_dir = True
        _ARCHIVE_FORMATS = {'tar': (_make_tarball, [('compress', None)], 'uncompressed tar file')}
        if _ZLIB_SUPPORTED:
            _ARCHIVE_FORMATS['gztar'] = (_make_tarball, [('compress', 'gzip')], 'gzip\'ed tar-file')
            _ARCHIVE_FORMATS['zip'] = (_make_zipfile, [], 'ZIP file')
        if _BZ2_SUPPORTED:
            _ARCHIVE_FORMATS['bztar'] = (_make_tarball, [('compress', 'bzip2')], 'bzip2\'ed tar-file')
        if _LZMA_SUPPORTED:
            _ARCHIVE_FORMATS['xztar'] = (_make_tarball, [('compress', 'xz')], 'xz\'ed tar-file')

        def get_archive_formats():
            """Returns a list of supported formats for archiving and unarchiving.\n\n    Each element of the returned sequence is a tuple (name, description)\n    """  # inserted
            formats = [(name, registry[2]) for name, registry in _ARCHIVE_FORMATS.items()]
            formats.sort()
            return formats

        def register_archive_format(name, function, extra_args=None, description=''):
            """Registers an archive format.\n\n    name is the name of the format. function is the callable that will be\n    used to create archives. If provided, extra_args is a sequence of\n    (name, value) tuples that will be passed as arguments to the callable.\n    description can be provided to describe the format, and will be returned\n    by the get_archive_formats() function.\n    """  # inserted
            if extra_args is None:
                extra_args = []
            if not callable(function):
                raise TypeError('The %s object is not callable' % function)
            if not isinstance(extra_args, (tuple, list)):
                raise TypeError('extra_args needs to be a sequence')
            for element in extra_args:
                if not isinstance(element, (tuple, list)) or len(element)!= 2:
                    raise TypeError('extra_args elements are : (arg_name, value)')
            else:  # inserted
                _ARCHIVE_FORMATS[name] = (function, extra_args, description)

        def unregister_archive_format(name):
            del _ARCHIVE_FORMATS[name]
        pass
        pass
        def make_archive(base_name, format, root_dir=None, base_dir=None, verbose=0, dry_run=0, owner=None, group=None, logger=None):
            """Create an archive file (eg. zip or tar).\n\n    \'base_name\' is the name of the file to create, minus any format-specific\n    extension; \'format\' is the archive format: one of \"zip\", \"tar\", \"gztar\",\n    \"bztar\", or \"xztar\".  Or any other registered format.\n\n    \'root_dir\' is a directory that will be the root directory of the\n    archive; ie. we typically chdir into \'root_dir\' before creating the\n    archive.  \'base_dir\' is the directory where we start archiving from;\n    ie. \'base_dir\' will be the common prefix of all files and\n    directories in the archive.  \'root_dir\' and \'base_dir\' both default\n    to the current directory.  Returns the name of the archive file.\n\n    \'owner\' and \'group\' are used when creating a tar archive. By default,\n    uses the current owner and group.\n    """  # inserted
            sys.audit('shutil.make_archive', base_name, format, root_dir, base_dir)
            try:
                format_info = _ARCHIVE_FORMATS[format]
            except KeyError:
                pass  # postinserted
            else:  # inserted
                kwargs = {'dry_run': dry_run, 'logger': logger, 'owner': owner, 'group': group}
                func = format_info[0]
                for arg, val in format_info[1]:
                    kwargs[arg] = val
            if base_dir is None:
                base_dir = os.curdir
            supports_root_dir = getattr(func, 'supports_root_dir', False)
            save_cwd = None
            if root_dir is not None:
                stmd = os.stat(root_dir).st_mode
                if not stat.S_ISDIR(stmd):
                    raise NotADirectoryError(errno.ENOTDIR, 'Not a directory', root_dir)
                if supports_root_dir:
                    base_name = os.fspath(base_name)
                    kwargs['root_dir'] = root_dir
                else:  # inserted
                    save_cwd = os.getcwd()
                    if logger is not None:
                        logger.debug('changing into \'%s\'', root_dir)
                    base_name = os.path.abspath(base_name)
                    if not dry_run:
                        os.chdir(root_dir)
            try:
                filename = func(base_name, base_dir, **kwargs)
            finally:  # inserted
                if save_cwd is not None:
                    if logger is not None:
                        logger.debug('changing back to \'%s\'', save_cwd)
                    os.chdir(save_cwd)
            return filename
                raise ValueError('unknown archive format \'%s\'' % format) from None

        def get_unpack_formats():
            """Returns a list of supported formats for unpacking.\n\n    Each element of the returned sequence is a tuple\n    (name, extensions, description)\n    """  # inserted
            formats = [(name, info[0], info[3]) for name, info in _UNPACK_FORMATS.items()]
            formats.sort()
            return formats

        def _check_unpack_options(extensions, function, extra_args):
            """Checks what gets registered as an unpacker."""  # inserted
            existing_extensions = {}
            for name, info in _UNPACK_FORMATS.items():
                for ext in info[0]:
                    existing_extensions[ext] = name
            for extension in extensions:
                if extension in existing_extensions:
                    msg = '%s is already registered for \"%s\"'
                    raise RegistryError(msg % (extension, existing_extensions[extension]))
            else:  # inserted
                if not callable(function):
                    raise TypeError('The registered function must be a callable')
        pass
        pass
        def register_unpack_format(name, extensions, function, extra_args=None, description=''):
            """Registers an unpack format.\n\n    `name` is the name of the format. `extensions` is a list of extensions\n    corresponding to the format.\n\n    `function` is the callable that will be\n    used to unpack archives. The callable will receive archives to unpack.\n    If it\'s unable to handle an archive, it needs to raise a ReadError\n    exception.\n\n    If provided, `extra_args` is a sequence of\n    (name, value) tuples that will be passed as arguments to the callable.\n    description can be provided to describe the format, and will be returned\n    by the get_unpack_formats() function.\n    """  # inserted
            if extra_args is None:
                extra_args = []
            _check_unpack_options(extensions, function, extra_args)
            _UNPACK_FORMATS[name] = (extensions, function, extra_args, description)

        def unregister_unpack_format(name):
            """Removes the pack format from the registry."""  # inserted
            del _UNPACK_FORMATS[name]

        def _ensure_directory(path):
            """Ensure that the parent directory of `path` exists"""  # inserted
            dirname = os.path.dirname(path)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)

        def _unpack_zipfile(filename, extract_dir):
            """Unpack zip `filename` to `extract_dir`\n    """  # inserted
            import zipfile
            if not zipfile.is_zipfile(filename):
                raise ReadError('%s is not a zip file' % filename)
            zip = zipfile.ZipFile(filename)
            try:
                for info in zip.infolist():
                    name = info.filename
                    if name.startswith('/') or '..' in name:
                        continue
                    targetpath = os.path.join(*extract_dir, *name.split('/'))
                    if not targetpath:
                        continue
                    _ensure_directory(targetpath)
                    if not name.endswith('/'):
                        with zip.open(name, 'r') as source:
                            with open(targetpath, 'wb') as target:
                                copyfileobj(source, target)
                finally:  # inserted
                    zip.close()

        def _unpack_tarfile(filename, extract_dir, *, filter=None):
            """Unpack tar/tar.gz/tar.bz2/tar.xz `filename` to `extract_dir`\n    """  # inserted
            import tarfile
            try:
                tarobj = tarfile.open(filename)
            except tarfile.TarError:
                pass  # postinserted
            else:  # inserted
                try:
                    tarobj.extractall(extract_dir, filter=filter)
                finally:  # inserted
                    tarobj.close()
                raise ReadError('%s is not a compressed or uncompressed tar file' % filename)
        _UNPACK_FORMATS = {'tar': (['.tar'], _unpack_tarfile, [], 'uncompressed tar file'), 'zip': (['.zip'], _unpack_zipfile, [], 'ZIP file')}
        if _ZLIB_SUPPORTED:
            _UNPACK_FORMATS['gztar'] = (['.tar.gz', '.tgz'], _unpack_tarfile, [], 'gzip\'ed tar-file')
        if _BZ2_SUPPORTED:
            _UNPACK_FORMATS['bztar'] = (['.tar.bz2', '.tbz2'], _unpack_tarfile, [], 'bzip2\'ed tar-file')
        if _LZMA_SUPPORTED:
            _UNPACK_FORMATS['xztar'] = (['.tar.xz', '.txz'], _unpack_tarfile, [], 'xz\'ed tar-file')

        def _find_unpack_format(filename):
            for name, info in _UNPACK_FORMATS.items():
                for extension in info[0]:
                    if filename.endswith(extension):
                        return name
            else:  # inserted
                return

        def unpack_archive(filename, extract_dir=None, format=None, *, filter=None):
            """Unpack an archive.\n\n    `filename` is the name of the archive.\n\n    `extract_dir` is the name of the target directory, where the archive\n    is unpacked. If not provided, the current working directory is used.\n\n    `format` is the archive format: one of \"zip\", \"tar\", \"gztar\", \"bztar\",\n    or \"xztar\".  Or any other registered format.  If not provided,\n    unpack_archive will use the filename extension and see if an unpacker\n    was registered for that extension.\n\n    In case none is found, a ValueError is raised.\n\n    If `filter` is given, it is passed to the underlying\n    extraction function.\n    """  # inserted
            sys.audit('shutil.unpack_archive', filename, extract_dir, format)
            if extract_dir is None:
                extract_dir = os.getcwd()
            extract_dir = os.fspath(extract_dir)
            filename = os.fspath(filename)
            if filter is None:
                filter_kwargs = {}
            else:  # inserted
                filter_kwargs = {'filter': filter}
            if format is not None:
                try:
                    format_info = _UNPACK_FORMATS[format]
                except KeyError:
                    pass  # postinserted
                else:  # inserted
                    func = format_info[1]
                    func(filename, extract_dir, **dict(format_info[2]), **filter_kwargs)
            else:  # inserted
                format = _find_unpack_format(filename)
                if format is None:
                    raise ReadError('Unknown archive format \'{0}\''.format(filename))
                func = _UNPACK_FORMATS[format][1]
                kwargs = dict(_UNPACK_FORMATS[format][2]) | filter_kwargs
                func(filename, extract_dir, **kwargs)
                raise ValueError('Unknown unpack format \'{0}\''.format(format)) from None
        if hasattr(os, 'statvfs'):
            __all__.append('disk_usage')
            _ntuple_diskusage = collections.namedtuple('usage', 'total used free')
            _ntuple_diskusage.total.__doc__ = 'Total space in bytes'
            _ntuple_diskusage.used.__doc__ = 'Used space in bytes'
            _ntuple_diskusage.free.__doc__ = 'Free space in bytes'

            def disk_usage(path):
                """Return disk usage statistics about the given path.\n\n        Returned value is a named tuple with attributes \'total\', \'used\' and\n        \'free\', which are the amount of total, used and free space, in bytes.\n        """  # inserted
                st = os.statvfs(path)
                free = st.f_bavail * st.f_frsize
                total = st.f_blocks * st.f_frsize
                used = (st.f_blocks - st.f_bfree) * st.f_frsize
                return _ntuple_diskusage(total, used, free)
        else:  # inserted
            if _WINDOWS:
                __all__.append('disk_usage')
                _ntuple_diskusage = collections.namedtuple('usage', 'total used free')

                def disk_usage(path):
                    """Return disk usage statistics about the given path.\n\n        Returned values is a named tuple with attributes \'total\', \'used\' and\n        \'free\', which are the amount of total, used and free space, in bytes.\n        """  # inserted
                    total, free = nt._getdiskusage(path)
                    used = total - free
                    return _ntuple_diskusage(total, used, free)

        def chown(path, user=None, group=None):
            """Change owner user and group of the given path.\n\n    user and group can be the uid/gid or the user/group names, and in that case,\n    they are converted to their respective uid/gid.\n    """  # inserted
            sys.audit('shutil.chown', path, user, group)
            if user is None and group is None:
                raise ValueError('user and/or group must be set')
            _user = user
            _group = group
            if user is None:
                _user = (-1)
            else:  # inserted
                if isinstance(user, str):
                    _user = _get_uid(user)
                    if _user is None:
                        raise LookupError('no such user: {!r}'.format(user))
            if group is None:
                _group = (-1)
            else:  # inserted
                if not isinstance(group, int):
                    _group = _get_gid(group)
                    if _group is None:
                        raise LookupError('no such group: {!r}'.format(group))
            os.chown(path, _user, _group)

        def get_terminal_size(fallback=(80, 24)):
            """Get the size of the terminal window.\n\n    For each of the two dimensions, the environment variable, COLUMNS\n    and LINES respectively, is checked. If the variable is defined and\n    the value is a positive integer, it is used.\n\n    When COLUMNS or LINES is not defined, which is the common case,\n    the terminal connected to sys.__stdout__ is queried\n    by invoking os.get_terminal_size.\n\n    If the terminal size cannot be successfully queried, either because\n    the system doesn\'t support querying, or because we are not\n    connected to a terminal, the value given in fallback parameter\n    is used. Fallback defaults to (80, 24) which is the default\n    size used by many terminal emulators.\n\n    The value returned is a named tuple of type os.terminal_size.\n    """  # inserted
            try:
                columns = int(os.environ['COLUMNS'])
            except (KeyError, ValueError):
                pass  # postinserted
            else:  # inserted
                try:
                    lines = int(os.environ['LINES'])
            except (KeyError, ValueError):
                else:  # inserted
                    if columns <= 0 or lines <= 0:
                        try:
                            size = os.get_terminal_size(sys.__stdout__.fileno())
                except (AttributeError, ValueError, OSError):
                        else:  # inserted
                            if columns <= 0:
                                columns = size.columns or fallback[0]
                        if lines <= 0:
                            lines = size.lines or fallback[1]
                    return os.terminal_size((columns, lines))
                columns = 0
                lines = 0
                size = os.terminal_size(fallback)

        def _access_check(fn, mode):
            return os.path.exists(fn) and os.access(fn, mode) and (not os.path.isdir(fn))

        def _win_path_needs_curdir(cmd, mode):
            """\n    On Windows, we can use NeedCurrentDirectoryForExePath to figure out\n    if we should add the cwd to PATH when searching for executables if\n    the mode is executable.\n    """  # inserted
            return not mode & os.X_OK or _winapi.NeedCurrentDirectoryForExePath(os.fsdecode(cmd))

        def which(cmd, mode=os.F_OK | os.X_OK, path=None):
            """Given a command, mode, and a PATH string, return the path which\n    conforms to the given mode on the PATH, or None if there is no such\n    file.\n\n    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result\n    of os.environ.get(\"PATH\"), or can be overridden with a custom search\n    path.\n\n    """  # inserted
            use_bytes = isinstance(cmd, bytes)
            dirname, cmd = os.path.split(cmd)
            if dirname:
                path = [dirname]
            else:  # inserted
                if path is None:
                    path = os.environ.get('PATH', None)
                    if path is None:
                        try:
                            path = os.confstr('CS_PATH')
                        except (AttributeError, ValueError):
                            pass  # postinserted
            else:  # inserted
                if not path:
                    return
                if use_bytes:
                    path = os.fsencode(path)
                    path = path.split(os.fsencode(os.pathsep))
                else:  # inserted
                    path = os.fsdecode(path)
                    path = path.split(os.pathsep)
                if sys.platform == 'win32' and _win_path_needs_curdir(cmd, mode):
                    curdir = os.curdir
                    if use_bytes:
                        curdir = os.fsencode(curdir)
                    path.insert(0, curdir)
            if sys.platform == 'win32':
                pathext_source = os.getenv('PATHEXT') or _WIN_DEFAULT_PATHEXT
                pathext = [ext for ext in pathext_source.split(os.pathsep) if ext]
                if use_bytes:
                    pathext = [os.fsencode(ext) for ext in pathext]
                files = [cmd] + [cmd + ext for ext in pathext]
                suffix = os.path.splitext(files[0])[1].upper()
                if mode & os.X_OK:
                    if not any((suffix == ext.upper() for ext in pathext)):
                        files.append(files.pop(0))
            else:  # inserted
                files = [cmd]
            seen = set()
            for dir in path:
                normdir = os.path.normcase(dir)
                if normdir not in seen:
                    seen.add(normdir)
                    for thefile in files:
                        name = os.path.join(dir, thefile)
                        if _access_check(name, mode):
                            return name
                            path = os.defpath
    _ZLIB_SUPPORTED = False
    _BZ2_SUPPORTED = False
    _LZMA_SUPPORTED = False