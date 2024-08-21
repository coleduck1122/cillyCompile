def make_tk(type, val=None):
    return [type, val] if val is not None else [type]


def tk_tag(t):
    return t[0]


def tk_val(t):
    return t[1] if len(t) > 1 else None


def error(src, msg):
    raise Exception(f'<{src}>: {msg}')


def lexer(prog):
    def err(msg):
        error('lexer', msg)

    pos = -1
    cur = None
    keywords = ['return', 'fun', 'print', 'if', 'else', 'var', 'true', 'false', 'import', 'while']

    def next():
        nonlocal pos, cur

        t = cur

        pos = pos + 1
        if pos >= len(prog):
            cur = 'eof'
        else:
            cur = prog[pos]

        return t

    def peek():
        return cur

    def match(m):
        if cur != m:
            err(f'期望是{m},实际是{cur}')

        return next()

    def ws_skip():
        while peek() in [' ', '\t', '\r', '\n']:
            next()

    def string():
        r = ''
        match('"')
        while peek() != '"':
            r = r + next()
        match('"')
        return make_tk('str', r)

    def isdigit(c):
        return c >= '0' and c <= '9'

    def num():
        r = next()

        while isdigit(peek()):
            r = r + next()

        if peek() == '.':
            r = r + next()
            while isdigit(peek()):
                r = r + next()

        return make_tk('num', float(r) if '.' in r else int(r))

    def isletter_(c):
        return c == '_' or (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z')

    def isletter_or_digit(c):
        return isdigit(c) or isletter_(c)

    def id():
        r = next()

        while isletter_or_digit(peek()):
            r = r + next()

        if r in keywords:
            return make_tk(r)

        return make_tk('id', r)

    def token():
        ws_skip()

        t = peek()

        if t == 'eof':
            return make_tk('eof')

        if t in [':', ',', '+', '-', '*', '/', '^', ';', '(', ')', '{', '}', '[', ']', 'T']:
            next()
            return make_tk(t)

        if t == '=':
            next()
            if peek() == '=':
                next()
                return make_tk('==')
            else:
                return make_tk('=')

        if t == '>':
            next()
            if peek() == '=':
                next()
                return make_tk('>=')
            else:
                return make_tk('>')

        if t == '"':
            return string()

        if t == '!':
            next()
            if peek() == '=':
                next()
                return make_tk('!=')
            else:
                return make_tk('!')

        if t == '<':
            next()
            if peek() == '=':
                next()
                return make_tk('<=')
            else:
                return make_tk('<')

        if isdigit(t):
            return num()

        if isletter_(t):
            return id()

        err(f'非法字符{t}')

    # lexer start
    next()

    tokens = []

    while True:
        t = token()
        tokens.append(t)
        if tk_tag(t) == 'eof':
            break

    return tokens
