from cilly_vm_compiler import *


def num(n):
    return ['num', n]


def string(s):
    return ['str', s]


def boolean(b):
    return T if b else F


def val(v):
    return v[1]


def cilly_vm(code, consts, globs):
    stack = []
    callStack = []
    scopes = [globs]

    def err(msg):
        error('cilly vm', msg)

    def push_call_stack(c):
        callStack.append(c)

    def pop_call_stack():
        return callStack.pop()

    def enter_scope(var_count):
        nonlocal scopes
        scope = [None for _ in range(var_count)]
        scopes = scopes + [scope]

    def leave_scope():
        nonlocal scopes
        scopes = scopes[0:-1]

    def current_scope():
        return scopes[-1]

    def load_var(scope_i, i):
        scope = scopes[-(scope_i + 1)]
        push(scope[i])

    def store_var(scope_i, i):
        scope = scopes[-(scope_i + 1)]
        scope[i] = top()

    def push(x):
        stack.append(x)

    def pop():
        t = stack.pop()
        return t

    def top():
        return stack[-1]

    def empty():
        return len(stack) == 0

    def init_stack():
        nonlocal stack
        stack = []

    def binop(op):
        v2 = val(pop())
        v1 = val(pop())

        if op == '+':
            v = num(v1 + v2)
        elif op == '-':
            v = num(v1 - v2)
        elif op == '*':
            v = num(v1 * v2)
        elif op == '/':
            v = num(v1 / v2)
        elif op == '>':
            v = boolean(v1 > v2)
        elif op == '>=':
            v = boolean(v1 >= v2)
        elif op == '<':
            v = boolean(v1 < v2)
        elif op == '<=':
            v = boolean(v1 <= v2)
        elif op == '==':
            v = boolean(v1 == v2)
        elif op == '!=':
            v = boolean(v1 != v2)
        else:
            err(f'非法二元运算符{op}')

        push(v)

    def run():
        nonlocal scopes
        init_stack()

        pc = 0

        while pc < len(code):
            inst = code[pc]

            pc = pc + 1

            if inst == LOAD_CONST:
                index = code[pc]
                pc = pc + 1
                v = consts[index]
                push(v)
            elif inst == LOAD_TRUE:
                push(T)

            elif inst == MAKE_CLOSURE:
                tag, proc_entry, params = pop()
                if tag != 'compiled fun':
                    err(f'非法函数定义{tag}')

                push(['compiled closure', proc_entry, params, scopes])
            elif inst == CALL:
                args = code[pc]

                enter_scope(args)
                scope = current_scope()

                for i in range(args):
                    scope[-(i + 1)] = pop()

                proc = pop()
                tag, proc_entry, params, saved_scopes = proc

                new_scopes = saved_scopes + [scope]

                push_call_stack((pc + 1, scopes))

                scopes = new_scopes
                pc = proc_entry
            elif inst == RET:
                leave_scope()
                pc, scopes = pop_call_stack()

            elif inst == ENTER_SCOPE:
                var_count = code[pc]
                enter_scope(var_count)
                pc = pc + 1
            elif inst == LEAVE_SCOPE:
                leave_scope()
            elif inst == LOAD_VAR:
                scope_i = code[pc]
                i = code[pc + 1]
                load_var(scope_i, i)
                pc = pc + 2
            elif inst == STORE_VAR:
                scope_i = code[pc]
                i = code[pc + 1]
                store_var(scope_i, i)
                pc = pc + 2
            elif inst == LOAD_GLOBAL:
                index = code[pc]
                pc = pc + 1
                v = globs[index]
                push(v)
            elif inst == STORE_GLOBAL:
                index = code[pc]
                pc = pc + 1
                v = pop()
                globs[index] = v

            elif inst == LOAD_FALSE:
                push(F)

            elif inst == JMP:
                target = code[pc]
                pc = target

            elif inst == JMP_TRUE:
                target = code[pc]
                v = pop()
                if v == T:
                    pc = target
                else:
                    pc = pc + 1
            elif inst == JMP_FALSE:
                target = code[pc]
                v = pop()
                if v == F:
                    pc = target
                else:
                    pc = pc + 1

            elif inst == LOAD_NULL:
                push(Null)
            elif inst == BINOP_ADD:
                binop('+')
            elif inst == BINOP_SUB:
                binop('-')
            elif inst == BINOP_MUL:
                binop('*')
            elif inst == BINOP_DIV:
                binop('/')
            elif inst == BINOP_GT:
                binop('>')
            elif inst == BINOP_GE:
                binop('>=')
            elif inst == BINOP_LT:
                binop('<')
            elif inst == BINOP_LE:
                binop('<=')
            elif inst == BINOP_GT:
                binop('>')
            elif inst == BINOP_GE:
                binop('>=')
            elif inst == BINOP_EQ:
                binop('==')
            elif inst == BINOP_NE:
                binop('!=')

            elif inst == PRINT_ITEM:
                v = pop()
                print(val(v), end=' ')
            elif inst == PRINT_NEWLINE:
                print('')

            elif inst == POP:
                pop()
            elif inst == UNIOP_NOT:
                v = pop()
                if v == T:
                    push(F)
                else:
                    push(T)
            elif inst == UNIOP_NEG:
                v = pop()
                push(num(-val(v)))
            else:
                err(f'非法指令{inst}')

        return top()

    return run()


if __name__ == '__main__':
    filename = './dist/test.cilly'
    with open(filename) as f:
        ast = parser(lexer(f.read()))
    print(ast)

    code, consts, glob_syms = cilly_vm_compiler(ast, [],
                                                [], [])

    c = []
    i = 0
    while i < len(code):
        for key, value in zl.items():
            if code[i] == value:
                st = ""
                for x in c:
                    st += x + '\t'
                print(st)
                c = []
                c.append(f"{i}: {key}")
                f = key
                break
        if f in ["LOAD_CONST", "ENTER_SCOPE", "JMP", "JMP_TRUE", "JMP_FALSE", "CALL"]:
            c.append(f"{code[i + 1]}")
            f = None
            i += 1
        elif f in ["LOAD_VAR", "STORE_VAR"]:
            c.append(f"{code[i + 1]}")
            c.append(f"{code[i + 2]}")
            f = None
            i += 2
        i += 1

    print(code)
    print(consts)
    print(glob_syms)
    # cilly_vm(code, consts, [Null for _ in glob_syms])
    cilly_vm(code, consts, glob_syms)