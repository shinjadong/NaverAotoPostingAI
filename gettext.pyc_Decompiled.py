# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: gettext.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

"""Internationalization and localization support.\n\nThis module provides internationalization (I18N) and localization (L10N)\nsupport for your Python programs by providing an interface to the GNU gettext\nmessage catalog library.\n\nI18N refers to the operation by which a program is made aware of multiple\nlanguages.  L10N refers to the adaptation of your program, once\ninternationalized, to the local language and cultural habits.\n\n"""
global _localedirs  # inserted
global _current_domain  # inserted
import operator
import os
import re
import sys
__all__ = ['NullTranslations', 'GNUTranslations', 'Catalog', 'bindtextdomain', 'find', 'translation', 'install', 'textdomain', 'dgettext', 'dngettext', 'gettext', 'ngettext', 'pgettext', 'dpgettext', 'npgettext', 'dnpgettext']
_default_localedir = os.path.join(sys.base_prefix, 'share', 'locale')
_token_pattern = re.compile('\n        (?P<WHITESPACES>[ \\t]+)                    | # spaces and horizontal tabs\n        (?P<NUMBER>[0-9]+\\b)                       | # decimal integer\n        (?P<NAME>n\\b)                              | # only n is allowed\n        (?P<PARENTHESIS>[()])                      |\n        (?P<OPERATOR>[-*/%+?:]|[><!]=?|==|&&|\\|\\|) | # !, *, /, %, +, -, <, >,\n                                                     # <=, >=, ==, !=, &&, ||,\n                                                     # ? :\n                                                     # unary and bitwise ops\n                                                     # not allowed\n        (?P<INVALID>\\w+|.)                           # invalid token\n    ', re.VERBOSE | re.DOTALL)

def _tokenize(plural):
    for mo in re.finditer(_token_pattern, plural):
        kind = mo.lastgroup
        if kind == 'WHITESPACES':
            continue
        value = mo.group(kind)
        if kind == 'INVALID':
            raise ValueError('invalid token in plural form: %s' % value)
        yield value
    else:  # inserted
        yield ''

def _error(value):
    if value:
        return ValueError('unexpected token in plural form: %s' % value)
    return ValueError('unexpected end of plural form')
_binary_ops = (('||',), ('&&',), ('==', '!='), ('<', '>', '<=', '>='), ('+', '-'), ('*', '/', '%'))
_binary_ops = {op: i for i, ops in enumerate(_binary_ops, 1) for op in ops}
_c2py_ops = {'||': 'or', '&&': 'and', '/': '//'}

def _parse(tokens, priority=(-1)):
    result = ''
    nexttok = next(tokens)
    while nexttok == '!':
        result += 'not '
        nexttok = next(tokens)
        continue
    if nexttok == '(':
        sub, nexttok = _parse(tokens)
        result = f'{result}({sub})'
        if nexttok!= ')':
            raise ValueError('unbalanced parenthesis in plural form')
    else:  # inserted
        if nexttok == 'n':
            result = f'{result}{nexttok}'
        else:  # inserted
            try:
                value = int(nexttok, 10)
            except ValueError:
                pass  # postinserted
            else:  # inserted
                result = '%s%d' % (result, value)
    nexttok = next(tokens)
    j = 100
    while nexttok in _binary_ops:
        i = _binary_ops[nexttok]
        if i < priority:
            break
        else:  # inserted
            if i in [3, 4] and j in [3, 4]:
                result = '(%s)' % result
            op = _c2py_ops.get(nexttok, nexttok)
            right, nexttok = _parse(tokens, i + 1)
            result = f'{result} {op} {right}'
            j = i
    if j == priority == 4:
        result = '(%s)' % result
    if nexttok == '?' and priority <= 0:
        if_true, nexttok = _parse(tokens, 0)
        if nexttok!= ':':
            raise _error(nexttok)
        if_false, nexttok = _parse(tokens)
        result = f'{if_true} if {result} else {if_false}'
        if priority == 0:
            result = '(%s)' % result
    return (result, nexttok)
                raise _error(nexttok) from None
            else:  # inserted
                pass

def _as_int(n):
    try:
        round(n)
    except TypeError:
        pass  # postinserted
    else:  # inserted
        import warnings
        frame = sys._getframe(1)
        stacklevel = 2
        while frame.f_back is not None and frame.f_globals.get('__name__') == __name__:
            stacklevel += 1
            frame = frame.f_back
    warnings.warn(f'Plural value must be an integer, got {n.__class__.__name__}1', DeprecationWarning, stacklevel)
    return n
        raise TypeError(f'Plural value must be an integer, got {n.__class__.__name__}1') from None

def c2py(plural):
    """Gets a C expression as used in PO files for plural forms and returns a\n    Python function that implements an equivalent expression.\n    """  # inserted
    if len(plural) > 1000:
        raise ValueError('plural form expression is too long')
    try:
        result, nexttok = _parse(_tokenize(plural))
        if nexttok:
            raise _error(nexttok)
        depth = 0
        for c in result:
            if c == '(':
                depth += 1
                if depth > 20:
                    raise ValueError('plural form expression is too complex')
            else:  # inserted
                if c == ')':
                    pass  # postinserted
    except RecursionError:
            else:  # inserted
                depth -= 1
        else:  # inserted
            ns = {'_as_int': _as_int, '__name__': __name__}
            exec('if True:\n            def func(n):\n                if not isinstance(n, int):\n                    n = _as_int(n)\n                return int(%s)\n            ' % result, ns)
            return ns['func']
            raise ValueError('plural form expression is too complex')
        else:  # inserted
            pass

def _expand_lang(loc):
    import locale
    loc = locale.normalize(loc)
    COMPONENT_CODESET = 1
    COMPONENT_TERRITORY = 2
    COMPONENT_MODIFIER = 4
    mask = 0
    pos = loc.find('@')
    if pos >= 0:
        modifier = loc[pos:]
        loc = loc[:pos]
        mask |= COMPONENT_MODIFIER
    else:  # inserted
        modifier = ''
    pos = loc.find('.')
    if pos >= 0:
        codeset = loc[pos:]
        loc = loc[:pos]
        mask |= COMPONENT_CODESET
    else:  # inserted
        codeset = ''
    pos = loc.find('_')
    if pos >= 0:
        territory = loc[pos:]
        loc = loc[:pos]
        mask |= COMPONENT_TERRITORY
    else:  # inserted
        territory = ''
    language = loc
    ret = []
    for i in range(mask + 1):
        if i & ~mask:
            continue
        val = language
        if i & COMPONENT_TERRITORY:
            val += territory
        if i & COMPONENT_CODESET:
            val += codeset
        if i & COMPONENT_MODIFIER:
            val += modifier
        ret.append(val)
    ret.reverse()
    return ret

class NullTranslations:
    def __init__(self, fp=None):
        self._info = {}
        self._charset = None
        self._fallback = None
        if fp is not None:
            self._parse(fp)

    def _parse(self, fp):
        return

    def add_fallback(self, fallback):
        if self._fallback:
            self._fallback.add_fallback(fallback)
        else:  # inserted
            self._fallback = fallback

    def gettext(self, message):
        return self._fallback.gettext(message) if self._fallback else message

    def ngettext(self, msgid1, msgid2, n):
        if self._fallback:
            return self._fallback.ngettext(msgid1, msgid2, n)
        if n == 1:
            return msgid1
        return msgid2

    def pgettext(self, context, message):
        if self._fallback:
            return self._fallback.pgettext(context, message)

    def npgettext(self, context, msgid1, msgid2, n):
        if self._fallback:
            return self._fallback.npgettext(context, msgid1, msgid2, n)
        if n == 1:
            return msgid1
        return msgid2

    def info(self):
        return self._info

    def charset(self):
        return self._charset

    def install(self, names=None):
        import builtins
        builtins.__dict__['_'] = self.gettext
        if names is not None:
            allowed = {'gettext', 'pgettext', 'ngettext', 'npgettext'}
            for name in allowed & set(names):
                builtins.__dict__[name] = getattr(self, name)

class GNUTranslations(NullTranslations):
    LE_MAGIC = 2500072158
    BE_MAGIC = 3725722773
    CONTEXT = '%s%s'
    VERSIONS = (0, 1)

    def _get_versions(self, version):
        """Returns a tuple of major version, minor version"""  # inserted
        return (version >> 16, version & 65535)

    def _parse(self, fp):
        """Override this method to support alternative .mo formats."""  # inserted
        from struct import unpack
        filename = getattr(fp, 'name', '')
        self._catalog = catalog = {}
        self.plural = lambda n: int(n!= 1)
        buf = fp.read()
        buflen = len(buf)
        magic = unpack('<I', buf[:4])[0]
        if magic == self.LE_MAGIC:
            version, msgcount, masteridx, transidx = unpack('<4I', buf[4:20])
            ii = '<II'
        else:  # inserted
            if magic == self.BE_MAGIC:
                version, msgcount, masteridx, transidx = unpack('>4I', buf[4:20])
                ii = '>II'
            else:  # inserted
                raise OSError(0, 'Bad magic number', filename)
        major_version, minor_version = self._get_versions(version)
        if major_version not in self.VERSIONS:
            raise OSError(0, 'Bad version number ' + str(major_version), filename)
        for i in range(0, msgcount):
            mlen, moff = unpack(ii, buf[masteridx:masteridx + 8])
            mend = moff + mlen
            tlen, toff = unpack(ii, buf[transidx:transidx + 8])
            tend = toff + tlen
            if mend < buflen and tend < buflen:
                msg = buf[moff:mend]
                tmsg = buf[toff:tend]
            else:  # inserted
                raise OSError(0, 'File is corrupt', filename)
            if mlen == 0:
                lastk = None
                for b_item in tmsg.split(b'\n'):
                    item = b_item.decode().strip()
                    if not item:
                        continue
                    if item.startswith('#-#-#-#-#') and item.endswith('#-#-#-#-#'):
                        continue
                    k = v = None
                    if ':' in item:
                        k, v = item.split(':', 1)
                        k = k.strip().lower()
                        v = v.strip()
                        self._info[k] = v
                        lastk = k
                    else:  # inserted
                        if lastk:
                            self._info[lastk] += '\n' + item
                    if k == 'content-type':
                        self._charset = v.split('charset=')[1]
                    else:  # inserted
                        if k == 'plural-forms':
                            v = v.split(';')
                            plural = v[1].split('plural=')[1]
                            self.plural = c2py(plural)
            charset = self._charset or 'ascii'
            if b'\x00' in msg:
                msgid1, msgid2 = msg.split(b'\x00')
                tmsg = tmsg.split(b'\x00')
                msgid1 = str(msgid1, charset)
                for i, x in enumerate(tmsg):
                    catalog[msgid1, i] = str(x, charset)
            else:  # inserted
                catalog[str(msg, charset)] = str(tmsg, charset)
            masteridx += 8
            transidx += 8

    def gettext(self, message):
        missing = object()
        tmsg = self._catalog.get(message, missing)
        if tmsg is missing:
            tmsg = self._catalog.get((message, self.plural(1)), missing)
        if tmsg is not missing:
            return tmsg
        if self._fallback:
            return self._fallback.gettext(message)
        return message

    def ngettext(self, msgid1, msgid2, n):
        try:
            tmsg = self._catalog[msgid1, self.plural(n)]
        except KeyError:
            pass  # postinserted
        else:  # inserted
            return tmsg
            if self._fallback:
                return self._fallback.ngettext(msgid1, msgid2, n)
            if n == 1:
                tmsg = msgid1
            tmsg = msgid2
        else:  # inserted
            pass

    def pgettext(self, context, message):
        ctxt_msg_id = self.CONTEXT % (context, message)
        missing = object()
        tmsg = self._catalog.get(ctxt_msg_id, missing)
        if tmsg is missing:
            tmsg = self._catalog.get((ctxt_msg_id, self.plural(1)), missing)
        if tmsg is not missing:
            return tmsg
        if self._fallback:
            return self._fallback.pgettext(context, message)
        return message

    def npgettext(self, context, msgid1, msgid2, n):
        ctxt_msg_id = self.CONTEXT % (context, msgid1)
        try:
            tmsg = self._catalog[ctxt_msg_id, self.plural(n)]
        except KeyError:
            pass  # postinserted
        else:  # inserted
            return tmsg
            if self._fallback:
                return self._fallback.npgettext(context, msgid1, msgid2, n)
            if n == 1:
                tmsg = msgid1
            tmsg = msgid2
        else:  # inserted
            pass

def find(domain, localedir=None, languages=None, all=False):
    if localedir is None:
        localedir = _default_localedir
    if languages is None:
        languages = []
        for envar in ['LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG']:
            val = os.environ.get(envar)
            if val:
                languages = val.split(':')
                break
        if 'C' not in languages:
            languages.append('C')
    nelangs = []
    for lang in languages:
        for nelang in _expand_lang(lang):
            if nelang not in nelangs:
                nelangs.append(nelang)
    if all:
        result = []
    else:  # inserted
        result = None
    for lang in nelangs:
        if lang == 'C':
            pass  # postinserted
        except:
            return result
        mofile = os.path.join(localedir, lang, 'LC_MESSAGES', '%s.mo' % domain)
        if os.path.exists(mofile):
            if all:
                result.append(mofile)
            else:  # inserted
                return mofile
    else:  # inserted
        return result
_translations = {}
pass
pass
def translation(domain, localedir=None, languages=None, class_=None, fallback=False):
    if class_ is None:
        class_ = GNUTranslations
    mofiles = find(domain, localedir, languages, all=True)
    if not mofiles:
        if fallback:
            return NullTranslations()
        from errno import ENOENT
        raise FileNotFoundError(ENOENT, 'No translation file found for domain', domain)
    result = None
    for mofile in mofiles:
        key = (class_, os.path.abspath(mofile))
        t = _translations.get(key)
        if t is None:
            with open(mofile, 'rb') as fp:
                t = _translations.setdefault(key, class_(fp))
        import copy
        t = copy.copy(t)
        if result is None:
            result = t
        else:  # inserted
            result.add_fallback(t)
    return result

def install(domain, localedir=None, *, names=None):
    t = translation(domain, localedir, fallback=True)
    t.install(names)
_localedirs = {}
_current_domain = 'messages'

def textdomain(domain=None):
    global _current_domain  # inserted
    if domain is not None:
        _current_domain = domain
    return _current_domain

def bindtextdomain(domain, localedir=None):
    if localedir is not None:
        _localedirs[domain] = localedir
    return _localedirs.get(domain, _default_localedir)

def dgettext(domain, message):
    try:
        t = translation(domain, _localedirs.get(domain, None))
    except OSError:
        pass  # postinserted
    else:  # inserted
        return t.gettext(message)
        return message
    else:  # inserted
        pass

def dngettext(domain, msgid1, msgid2, n):
    try:
        t = translation(domain, _localedirs.get(domain, None))
    except OSError:
        pass  # postinserted
    else:  # inserted
        return t.ngettext(msgid1, msgid2, n)
        if n == 1:
            return msgid1
        return msgid2
    else:  # inserted
        pass

def dpgettext(domain, context, message):
    try:
        t = translation(domain, _localedirs.get(domain, None))
    except OSError:
        pass  # postinserted
    else:  # inserted
        return t.pgettext(context, message)
        return message
    else:  # inserted
        pass

def dnpgettext(domain, context, msgid1, msgid2, n):
    try:
        t = translation(domain, _localedirs.get(domain, None))
    except OSError:
        pass  # postinserted
    else:  # inserted
        return t.npgettext(context, msgid1, msgid2, n)
        if n == 1:
            return msgid1
        return msgid2
    else:  # inserted
        pass

def gettext(message):
    return dgettext(_current_domain, message)

def ngettext(msgid1, msgid2, n):
    return dngettext(_current_domain, msgid1, msgid2, n)

def pgettext(context, message):
    return dpgettext(_current_domain, context, message)

def npgettext(context, msgid1, msgid2, n):
    return dnpgettext(_current_domain, context, msgid1, msgid2, n)
Catalog = translation