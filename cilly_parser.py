from cilly_lexer import *


def node_tag(ast):
    return ast[0]


def make_tokenizer(tokens, err):
    pos = -1
    cur = None

    def next():
        nonlocal cur, pos
        t = cur
        pos = pos + 1
        if pos >= len(tokens):
            cur = ['eof']
        else:
            cur = tokens[pos]
        return t

    def peek(k=0):
        if k + pos >= len(tokens):
            return 'eof'
        else:
            return tk_tag(tokens[k + pos])

    def match(*m):
        if peek() not in m:
            err(f'期望{m},实际为{peek()}')

        return next()

    next()
    return (next, peek, match)


def parser(tokens):
    def expr():
        return logic_or()

    def logic_or():
        ret = logic_and()
        while peek() in ['or']:
            op = tk_tag(next())
            ret = [op, ret, logic_and()]
        return ret

    def logic_and():
        ret = equality()
        while peek() in ['and']:
            op = tk_tag(next())
            ret = [op, ret, equality()]
        return ret

    def equality():
        ret = comparison()
        while peek() in ['==', '!=']:
            op = tk_tag(next())
            ret = ['binop', op, ret, comparison()]
        return ret

    def comparison():
        ret = term()
        while peek() in ['>', '>=', '<', '<=']:
            op = tk_tag(next())
            ret = ['binop', op, ret, term()]
        return ret

    def term():
        ret = factor()
        while peek() in ['+', '-']:
            op = tk_tag(next())
            ret = ['binop', op, ret, factor()]
        return ret

    def factor():
        ret = unary()
        while peek() in ['*', '/']:
            op = tk_tag(next())
            ret = ['binop', op, ret, unary()]
        return ret

    def unary():
        if peek() == '-':
            match('-')
            return ['uinop', '-', unary()]
        elif peek() == '!':
            match('!')
            return ['uinop', '!', unary()]
        else:
            return pow()

    def pow():
        ret = atom()
        if peek() == '!':
            match('!')
            ret = ['uinop', 'frac', ret]
        if peek() == '^':
            match('^')
            ret = ['binop', '^', ret, pow()]
        return ret

    def atom():
        if peek() == 'num':
            return match('num')
        if peek() == 'true':
            return match('true')
        if peek() == 'false':
            return match('false')
        if peek() == 'str':
            return match('str')
        if peek() == 'T':
            return match('T')
        if peek() == '[':
            match('[')
            ret = vec()
            match(']')
            return ['vec', ret]
        if peek() == 'id':
            if peek(1) == '(':
                return call()
            else:
                return variable()
        if peek() == '(':
            match('(')
            ret = expr()
            match(')')
            return ret
        return None

    def vec():
        if peek() == ']':
            return []
        ret = [expr()]
        while peek() == ',':
            match(',')
            ret.append(expr())
        return ret

    def variable():
        if peek() == 'id':
            t = match('id')
            if peek() != '[':
                return t
            pos = []
            while peek() == '[':
                match('[')
                ret = expr()
                match(']')
                pos.append(ret)
            return (t, ['vec', pos])

    def call():
        t = match('id')
        match('(')

        tv = tk_val(t)

        # 系统函数 - 无参
        if tv in ['input']:
            ret = [tv]
        # 系统函数 - 一参
        elif tv in ['arr', 'int', 'len', 'type', 'abs', 'show', 'inv', 'det', 'tr', 'eig']:
            ret = [tv, expr()]
        # 调用
        else:
            ret = ['call', t, args()]

        match(')')
        return ret

    def params():
        if peek() == ')':
            return []
        t = tk_val(match('id'))
        ret = [t]
        while peek() == ',':
            match(',')
            ret.append(tk_val(match('id')))
        return ret

    def args():
        if peek() == ')':
            return []
        ret = [expr()]
        while peek() == ',':
            match(',')
            ret.append(expr())
        return ret

    def err(m):
        error('cilly parser', m)

    next, peek, match = make_tokenizer(tokens, err)

    def program():
        r = []
        while peek() != 'eof':
            r.append(statement())
        return ['program', r]

    def statement():
        t = peek()

        if t == 'import':
            return import_stat()

        if t == 'fun':
            return fun_stat()

        if t == '{':
            return block_stat()

        if t == 'while':
            return while_stat()

        if t == 'if':
            return if_stat()

        if t == 'return':
            return ret_stat()

        if t == 'continue':
            return continue_stat()

        if t == 'break':
            return break_stat()

        if t == 'print':
            return print_stat()

        if t == 'var':
            return var_stat()

        if t == 'id':
            pos = 1
            while peek(pos) != 'eof' and peek(pos) != ';':
                if peek(pos) == '=':
                    return assign_stat()
                pos += 1

        # 默认处理为匹配表达式
        return expr_stat()

    def import_stat():
        match('import')
        ret = tk_val(match('str'))
        match(';')
        return ['import', ret]

    def expr_stat():
        ret = expr()
        match(';')
        return ret

    def fun_stat():
        match('fun')
        id = match('id')
        match('(')
        ret = params()
        match(')')
        return ['fun', tk_val(id), ret, block_stat()]

    def block_stat():
        match('{')
        r = []
        while peek() != '}':
            r.append(statement())
        match('}')
        return ['block', r]

    def while_stat():
        match('while')
        match('(')
        ret = expr()
        match(')')
        return ['while', ret, statement()]

    def if_stat():
        match('if')
        match('(')
        ret = expr()
        match(')')
        sta = statement()
        if peek() == 'else':
            match('else')
            return ['if', ret, sta, statement()]
        else:
            return ['if', ret, sta, None]

    def ret_stat():
        match('return')
        if peek() != ';':
            e = expr()
        else:
            e = None
        match(';')
        return ['return', e]

    def print_stat():
        match('print')
        match('(')
        ret = args()
        match(')')
        match(';')
        return ['print', ret]

    def var_stat():
        match('var')
        id = match('id')
        if peek() == '=':
            match('=')
            e = expr()
        else:
            e = None
        match(';')
        return ['var', id, e]

    def assign_stat():
        vr = variable()
        match('=')
        ret = expr()
        match(';')
        return ['assign', vr, ret]

    def continue_stat():
        match('continue')
        match(';')
        return ['continue']

    def break_stat():
        match('break')
        match(';')
        return ['break']

    return program()
