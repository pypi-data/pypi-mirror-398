import collections
import re

import types
from typing import Optional, Dict, AbstractSet

__all__ = ('EdgeQLLexer', 'UnknownTokenError')

keyword_types = range(1, 4)
UNRESERVED_KEYWORD, RESERVED_KEYWORD, TYPE_FUNC_NAME_KEYWORD = keyword_types
reserved_keywords = (
    "__edgedbsys__",
    "__edgedbtpl__",
    "__source__",
    "__std__",
    "__subject__",
    "__type__",
    "alter",
    "analyze",
    "and",
    "anyarray",
    "anytuple",
    "anytype",
    "begin",
    "by",
    "case",
    "check",
    "commit",
    "configure",
    "create",
    "deallocate",
    "delete",
    "describe",
    "detached",
    "discard",
    "distinct",
    "do",
    "drop",
    "else",
    "end",
    "execute",
    "exists",
    "explain",
    "extending",
    "fetch",
    "filter",
    "for",
    "get",
    "global",
    "grant",
    "group",
    "if",
    "ilike",
    "import",
    "in",
    "insert",
    "introspect",
    "is",
    "like",
    "limit",
    "listen",
    "load",
    "lock",
    "match",
    "module",
    "move",
    "never",
    "not",
    "notify",
    "offset",
    "on",
    "optional",
    "or",
    "over",
    "partition",
    "prepare",
    "raise",
    "refresh",
    "reindex",
    "revoke",
    "rollback",
    "select",
    "set",
    "single",
    "start",
    "typeof",
    "union",
    "update",
    "variadic",
    "when",
    "window",
    "with",
)
unreserved_keywords = (
    "abort",
    "abstract",
    "access",
    "after",
    "alias",
    "all",
    "allow",
    "annotation",
    "applied",
    "as",
    "asc",
    "assignment",
    "before",
    "cardinality",
    "cast",
    "config",
    "conflict",
    "constraint",
    "cube",
    "current",
    "database",
    "ddl",
    "declare",
    "default",
    "deferrable",
    "deferred",
    "delegated",
    "deny",
    "desc",
    "empty",
    "except",
    "expression",
    "extension",
    "final",
    "first",
    "from",
    "function",
    "implicit",
    "index",
    "infix",
    "inheritable",
    "instance",
    "into",
    "isolation",
    "json",
    "last",
    "link",
    "migration",
    "multi",
    "named",
    "object",
    "of",
    "only",
    "onto",
    "operator",
    "optionality",
    "order",
    "orphan",
    "overloaded",
    "owned",
    "package",
    "policy",
    "populate",
    "postfix",
    "prefix",
    "property",
    "proposed",
    "pseudo",
    "read",
    "reject",
    "release",
    "rename",
    "required",
    "reset",
    "restrict",
    "role",
    "roles",
    "rollup",
    "savepoint",
    "scalar",
    "schema",
    "sdl",
    "serializable",
    "session",
    "source",
    "superuser",
    "system",
    "target",
    "ternary",
    "text",
    "then",
    "to",
    "transaction",
    "type",
    "unless",
    "using",
    "verbose",
    "version",
    "view",
    "write",
)
_dunder_re = re.compile(r'(?i)^__[a-z]+__$')


def tok_name(keyword):
    '''Convert a literal keyword into a token name.'''
    if _dunder_re.match(keyword):
        return f'DUNDER{keyword[2:-2].upper()}'
    else:
        return keyword.upper()


edgeql_keywords = {k: (tok_name(k), UNRESERVED_KEYWORD)
                   for k in unreserved_keywords}
edgeql_keywords.update({k: (tok_name(k), RESERVED_KEYWORD)
                        for k in reserved_keywords})


STATE_KEEP = 0
STATE_BASE = 1


re_dquote = r'\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$'


class LexError(Exception):
    def __init__(
            self, msg, *, line=None, col=None, filename=None, format=True):
        if format and '{' in msg:
            position = self._format_position(line, col, filename)
            msg = msg.format(
                line=line, col=col, filename=filename, position=position)

        super().__init__(msg)
        self.line = line
        self.col = col
        self.filename = filename

    @classmethod
    def _format_position(cls, line, col, filename):
        position = 'at {}:{}'.format(line, col)
        if filename:
            position += ' of ' + str(filename)
        return position


Token = collections.namedtuple(
    'Token',
    ['value', 'type', 'text', 'start', 'end', 'filename']
)


class UnknownTokenError(LexError):
    pass


class Rule:
    _idx = 0
    _map: Dict[str, "Rule"] = {}

    def __init__(self, *, token, next_state, regexp):
        cls = self.__class__
        cls._idx += 1
        self.id = 'rule{}'.format(cls._idx)
        cls._map[self.id] = self

        self.token = token
        self.next_state = next_state
        self.regexp = regexp

    def __repr__(self):
        return '<{} {} {!r}>'.format(self.id, self.token, self.regexp)


def group(*literals, _re_alpha=re.compile(r'^\w+$'), asbytes=False):
    rx = []
    for lit in literals:
        if r'\b' not in lit:
            lit = re.escape(lit)
        if _re_alpha.match(lit):
            lit = r'\b' + lit + r'\b'
        rx.append(lit)
    result = ' | '.join(rx)
    if asbytes:
        result = result.encode()

    return result


class Lexer:

    NL: Optional[str] = None
    MULTILINE_TOKENS: AbstractSet[str] = frozenset()
    RE_FLAGS = re.X | re.M
    asbytes = False
    _NL = '\n'

    def __init_subclass__(cls):
        if not hasattr(cls, 'states'):
            return

        re_states = {}
        for state, rules in cls.states.items():
            res = []
            for rule in rules:
                if cls.asbytes:
                    res.append(b'(?P<%b>%b)' % (rule.id.encode(), rule.regexp))
                else:
                    res.append('(?P<{}>{})'.format(rule.id, rule.regexp))

            if cls.asbytes:
                res.append(b'(?P<err>.)')
            else:
                res.append('(?P<err>.)')

            if cls.asbytes:
                full_re = b' | '.join(res)
            else:
                full_re = ' | '.join(res)
            re_states[state] = re.compile(full_re, cls.RE_FLAGS)

        cls.re_states = types.MappingProxyType(re_states)

    def __init__(self):
        self.reset()
        if self.asbytes:
            self._NL = b'\n'

    def reset(self):
        self.lineno = 1
        self.column = 1
        self._state = self.start_state
        self._states = []

    def setinputstr(self, inputstr, filename=None):
        self.inputstr = inputstr
        self.filename = filename
        self.start = 0
        self.end = len(inputstr)
        self.reset()
        self._token_stream = None

    def get_start_token(self):
        """Return a start token or None if no start token is wanted."""
        return None

    def get_eof_token(self):
        """Return an EOF token or None if no EOF token is wanted."""
        return None

    def token_from_text(self, rule_token, txt):
        """Given the rule_token with txt create a token.

        Update the lexer lineno, column, and start.
        """
        start_pos = self.start
        len_txt = len(txt)

        if rule_token is self.NL:
            # Newline -- increase line number & set col to 1
            self.lineno += 1
            self.column = 1

        elif rule_token in self.MULTILINE_TOKENS and self._NL in txt:
            # Advance line & col according to how many new lines
            # are in comments/strings/etc.
            self.lineno += txt.count(self._NL)
            self.column = len(txt.rsplit(self._NL, 1)[1]) + 1
        else:
            self.column += len_txt

        self.start += len_txt
        end_pos = self.start

        return Token(txt, type=rule_token, text=txt,
                     start=start_pos, end=end_pos,
                     filename=self.filename)

    def lex(self):
        """Tokenize the src.

        Generator. Yields tokens (as defined by the rules).

        May yield special start and EOF tokens.
        May raise UnknownTokenError exception.
        """
        src = self.inputstr

        start_tok = self.get_start_token()
        if start_tok is not None:
            yield start_tok

        while self.start < self.end:
            for match in self.re_states[self._state].finditer(src, self.start):
                rule_id = match.lastgroup

                txt = match.group(rule_id)

                if rule_id == 'err':
                    # Error group -- no rule has been matched
                    self.handle_error(txt)

                rule = Rule._map[rule_id]
                rule_token = rule.token

                token = self.token_from_text(rule_token, txt)

                yield token

                if rule.next_state and rule.next_state != self._state:
                    # Rule dictates that the lexer state should be
                    # switched
                    self._state = rule.next_state
                    break

        # End of file
        eof_tok = self.get_eof_token()
        if eof_tok is not None:
            yield eof_tok

    def handle_error(self, txt, *,
                     exact_message=False, exc_type=UnknownTokenError):
        if exact_message:
            msg = txt
        else:
            msg = f"Unexpected '{txt}'"

        raise exc_type(
            msg, line=self.lineno, col=self.column, filename=self.filename
        )

    def token(self):
        """Return the next token produced by the 

        The token is an xvalue with the following attributes: type,
        text, start, end, and filename.
        """
        if self._token_stream is None:
            self._token_stream = self.lex()

        try:
            return next(self._token_stream)
        except StopIteration:
            return None


class UnterminatedStringError(UnknownTokenError):
    pass


class PseudoRule(Rule):
    def __init__(self, *, token, regexp, rule_id, next_state=STATE_KEEP):
        self.id = rule_id
        Rule._map[rule_id] = self
        self.token = token
        self.next_state = next_state
        self.regexp = regexp


class EdgeQLLexer(Lexer):

    start_state = STATE_BASE

    MERGE_TOKENS = {
        ('NAMED', 'ONLY'),
        ('SET', 'ANNOTATION'),
        ('SET', 'TYPE'),
        ('EXTENSION', 'PACKAGE'),
    }

    NL = 'NL'
    MULTILINE_TOKENS = frozenset(('SCONST', 'BCONST', 'RSCONST'))
    RE_FLAGS = re.X | re.M | re.I

    # Basic keywords
    keyword_rules = [Rule(token=tok[0],
                          next_state=STATE_KEEP,
                          regexp=group(val))
                     for val, tok in edgeql_keywords.items()]

    common_rules = keyword_rules + [
        Rule(token='WS',
             next_state=STATE_KEEP,
             regexp=r'[^\S\n]+'),

        Rule(token='NL',
             next_state=STATE_KEEP,
             regexp=r'\n'),

        Rule(token='COMMENT',
             next_state=STATE_KEEP,
             regexp=r'''\#.*?$'''),

        Rule(token='ASSIGN',
             next_state=STATE_KEEP,
             regexp=r':='),

        Rule(token='REMASSIGN',
             next_state=STATE_KEEP,
             regexp=r'-='),

        Rule(token='ADDASSIGN',
             next_state=STATE_KEEP,
             regexp=r'\+='),

        Rule(token='ARROW',
             next_state=STATE_KEEP,
             regexp=r'->'),

        Rule(token='??',
             next_state=STATE_KEEP,
             regexp=r'\?\?'),

        Rule(token='::',
             next_state=STATE_KEEP,
             regexp=r'::'),

        # special path operators
        Rule(token='.<',
             next_state=STATE_KEEP,
             regexp=r'\.<'),

        Rule(token='//',
             next_state=STATE_KEEP,
             regexp=r'//'),

        Rule(token='++',
             next_state=STATE_KEEP,
             regexp=r'\+\+'),

        Rule(token='OP',
             next_state=STATE_KEEP,
             regexp=r'''
                (?: >= | <= | != | \?= | \?!=)
             '''),

        Rule(token='self',
             next_state=STATE_KEEP,
             regexp=r'[,()\[\].@;:+\-*/%^<>=&|]'),

        Rule(token='NFCONST',
             next_state=STATE_KEEP,
             regexp=r"""
                (?:
                    (?: \d+ (?:\.\d+)?
                        (?:[eE](?:[+\-])?[0-9]+)
                    )
                    |
                    (?: \d+\.\d+)
                )n
                """),

        Rule(token='NICONST',
             next_state=STATE_KEEP,
             regexp=r'((?:[1-9]\d* | 0)n)'),

        Rule(token='FCONST',
             next_state=STATE_KEEP,
             regexp=r"""
                    (?: \d+ (?:\.\d+)?
                        (?:[eE](?:[+\-])?[0-9]+)
                    )
                    |
                    (?: \d+\.\d+)
                """),

        Rule(token='ICONST',
             next_state=STATE_KEEP,
             regexp=r'([1-9]\d* | 0)(?![0-9])'),

        Rule(token='BCONST',
             next_state=STATE_KEEP,
             regexp=rf'''
                (?:
                    b
                )
                (?P<BQ>
                    ' | "
                )
                (?:
                    (
                        \\\\ | \\['"] | \n | .
                        # we'll validate escape codes in the parser
                    )*?
                )
                (?P=BQ)
             '''),

        Rule(token='RSCONST',
             next_state=STATE_KEEP,
             regexp=rf'''
                (?:
                    r
                )?
                (?P<RQ>
                    (?:
                        (?<=r) (?: ' | ")
                    ) | (?:
                        (?<!r) (?: {re_dquote})
                    )
                )
                (?:
                    (
                        \n | .
                        # we'll validate escape codes in the parser
                    )*?
                )
                (?P=RQ)
             '''),

        Rule(token='LSCONST',
             next_state=STATE_KEEP,
             regexp=rf'''
                (?:
                    L
                )?
                (?P<LQ>
                    (?:
                        (?<=L) (?: ' | ")
                    ) | (?:
                        (?<!L) (?: {re_dquote})
                    )
                )
                (?:
                    (
                        \n | .
                        # we'll validate escape codes in the parser
                    )*?
                )
                (?P=LQ)
             '''),

        Rule(token='SCONST',
             next_state=STATE_KEEP,
             regexp=rf'''
                (?P<Q>
                    ' | "
                )
                (?:
                    (
                        \\\\ | \\['"] | \n | .
                        # we'll validate escape codes in the parser
                    )*?
                )
                (?P=Q)
             '''),

        # this rule will capture malformed strings and allow us to
        # provide better error messages
        Rule(token='BADSCONST',
             next_state=STATE_KEEP,
             regexp=rf'''
                [rb]?
                (['"] | (?: {re_dquote}))
                [^\n]*
             '''),

        Rule(token='BADIDENT',
             next_state=STATE_KEEP,
             regexp=r'''
                    __[^\W\d]\w*__
                    |
                    `__([^`]|``)*__`(?!`)
                '''),

        Rule(token='IDENT',
             next_state=STATE_KEEP,
             regexp=r'[^\W\d]\w*'),

        Rule(token='QIDENT',
             next_state=STATE_KEEP,
             regexp=r'`([^`]|``)*`'),

        Rule(token='self',
             next_state=STATE_KEEP,
             regexp=r'[\{\}]'),

        Rule(token='ARGUMENT',
             next_state=STATE_KEEP,
             regexp=r'\$(?:[0-9]+|[^\W\d]\w*|`(?:[^`]|``)*`)'),

        Rule(token='BADARGUMENT',
             next_state=STATE_KEEP,
             regexp=r'\$[0-9]+[^\W\d]\w*'),
    ]

    states = {
        STATE_BASE:
            common_rules,
    }

    # add capacity to handle a few tokens composed of 2 elements
    _possible_long_token = {x[0] for x in MERGE_TOKENS}
    _long_token_match = {x[1]: x[0] for x in MERGE_TOKENS}

    special_rules = [
        PseudoRule(token='UNKNOWN',
                   next_state=STATE_KEEP,
                   regexp=r'.',
                   rule_id='err')
    ]

    def __init__(self, *, strip_whitespace=True, raise_lexerror=True):
        super().__init__()
        self.strip_whitespace = strip_whitespace
        self.raise_lexerror = raise_lexerror

    def get_eof_token(self):
        """Return an EOF token or None if no EOF token is wanted."""
        return self.token_from_text('EOF', '')

    def token_from_text(self, rule_token, txt):
        if rule_token == 'BADSCONST':
            self.handle_error(f"Unterminated string {txt}",
                              exact_message=True,
                              exc_type=UnterminatedStringError)
        elif rule_token == 'BADIDENT':
            self.handle_error(txt)

        elif rule_token == 'QIDENT':
            if txt == '``':
                self.handle_error(f'Identifiers cannot be empty',
                                  exact_message=True)
            elif txt[1] == '@':
                self.handle_error(f'Identifiers cannot start with "@"',
                                  exact_message=True)
            elif '::' in txt:
                self.handle_error(f'Identifiers cannot contain "::"',
                                  exact_message=True)
        elif rule_token == 'ARGUMENT':
            if txt == '$``':
                self.handle_error(f'Backtick-quoted variable names '
                                  f'cannot be empty',
                                  exact_message=True)
        elif rule_token == 'BADARGUMENT':
            self.handle_error(f"Invalid argument name {txt!r} "
                              f"should be either all digits or "
                              f"start with letter",
                              exact_message=True,
                              exc_type=UnterminatedStringError)

        tok = super().token_from_text(rule_token, txt)

        if rule_token == 'self':
            tok = tok._replace(type=txt)

        elif rule_token == 'QIDENT':
            # Drop the quotes and replace the "``" inside with a "`"
            val = txt[1:-1].replace('``', '`')
            tok = tok._replace(type='IDENT', value=val)

        return tok

    def lex(self):
        buffer = []

        for tok in super().lex():
            tok_type = tok.type

            if self.strip_whitespace and tok_type in {'WS', 'NL', 'COMMENT'}:
                # Strip out whitespace and comments
                continue

            elif tok_type in self._possible_long_token:
                # Buffer in case this is a merged token
                if not buffer:
                    buffer.append(tok)
                else:
                    yield from iter(buffer)
                    buffer[:] = [tok]

            elif tok_type in self._long_token_match:
                prev_token = buffer[-1] if buffer else None
                if (prev_token and
                        prev_token.type == self._long_token_match[tok_type]):
                    tok = prev_token._replace(
                        value=prev_token.value + ' ' + tok.value,
                        type=prev_token.type + tok_type)
                    buffer.pop()
                yield tok

            else:
                if buffer:
                    yield from iter(buffer)
                    buffer[:] = []
                yield tok

    def lex_highlight(self):
        return super().lex()

    def handle_error(self, txt, *,
                     exact_message=False, exc_type=UnknownTokenError):
        if self.raise_lexerror:
            super().handle_error(
                txt, exact_message=exact_message, exc_type=exc_type)
