from cilly_parser import *
from consts import *


def cilly_vm_compiler(ast, code, consts, glob_syms):
    def err(msg):
        error('cilly vm compiler', msg)

    def add_const(c):
        for i in range(len(consts)):
            if consts[i] == c:
                return i

        consts.append(c)
        return len(consts) - 1

    scopes = [glob_syms]

    def enter_scope():
        nonlocal scopes
        scope = []
        scopes.append(scope)

    def leave_scope():
        return scopes.pop()

    def current_scope():
        return scopes[-1]

    def define_var(name):
        scope = current_scope()
        for i in range(len(scope)):
            if scope[i] == name:
                err(f'已定义变量{name}')

        scope.append(name)

        return len(scope) - 1

    def resolve_var(name):
        for scope_i in range(len(scopes)):
            scope = scopes[-(scope_i + 1)]
            for i in range(len(scope)):
                if scope[i] == name:
                    return scope_i, i

        err(f'未定义变量{name}')

    def define_global(name):
        for i in range(len(glob_syms)):
            if glob_syms[i] == name:
                err(f'变量已定义{name}')

        glob_syms.append(name)
        return len(glob_syms) - 1

    def lookup_global(name):
        for i in range(len(glob_syms)):
            if glob_syms[i] == name:
                return i

        err(f'未定义变量{name}')

    while_stack = []

    def push_while_stack(d):
        while_stack.append(d)

    def pop_while_stack():
        return while_stack.pop()

    def current_while_stack():
        return while_stack[-1]

    def next_emit_addr():
        return len(code)

    def back_patch(addr, value):
        code[addr + 1] = value

    def emit(opcode, operand=None, operand2=None):
        addr = next_emit_addr()
        code.append(opcode)
        if operand is not None:
            code.append(operand)
        if operand2 is not None:
            code.append(operand2)
        return addr

    def compile_null(node):
        emit(LOAD_NULL)

    def compile_bool(node):
        _, value = node
        if value == T:
            emit(LOAD_TRUE)
        else:
            emit(LOAD_FALSE)

    def compile_literal(node):
        index = add_const(node)
        emit(LOAD_CONST, index)

    def compile_id(node):
        _, name = node
        scope_i, index = resolve_var(name)
        emit(LOAD_VAR, scope_i, index)

    def compile_uniop(node):
        _, op, e = node
        visit(e)
        if op == '-':
            emit(UNIOP_NEG)
        elif op == '!':
            emit(UNIOP_NOT)
        else:
            err(f'非法一元运算符号{op}')

    def compile_binop(node):
        _, op, e1, e2 = node
        visit(e1)
        visit(e2)
        if op == '+':
            emit(BINOP_ADD)
        elif op == '-':
            emit(BINOP_SUB)
        elif op == '*':
            emit(BINOP_MUL)
        elif op == '/':
            emit(BINOP_DIV)
        elif op == '<':
            emit(BINOP_LT)
        elif op == '<=':
            emit(BINOP_LE)
        elif op == '>':
            emit(BINOP_GT)
        elif op == '>=':
            emit(BINOP_GE)
        elif op == '==':
            emit(BINOP_EQ)
        elif op == '!=':
            emit(BINOP_NE)
        else:
            err(f'非法二元运算符{op}')

    def compile_assign(node):
        _, name, e = node
        visit(e)
        scope_i, i = resolve_var(tk_val(name))
        emit(STORE_VAR, scope_i, i)

    def compile_var(node):
        _, id, e = node
        if e is not None:
            visit(e)
        else:
            emit(LOAD_NULL)

        # i = defineGlobal(id)
        i = define_var(tk_val(id))

        emit(STORE_VAR, 0, i)

    def compile_continue(node):
        loop_addr, _, scope_depth = current_while_stack()
        for i in range(len(scopes) - scope_depth):
            emit(LEAVE_SCOPE)
        emit(JMP, loop_addr)

    def compile_break(node):
        _, q, scope_depth = current_while_stack()
        addr = emit(JMP, -1)
        q.append(addr)

        for i in range(len(scopes) - scope_depth):
            emit(LEAVE_SCOPE)

    def compile_return(node):
        _, e = node
        if e is not None:
            visit(e)
        else:
            emit(LOAD_NULL)
        emit(RET)

    def compile_print(node):
        _, exprs = node
        for e in exprs:
            visit(e)
            emit(PRINT_ITEM)
        emit(PRINT_NEWLINE)
        emit(LOAD_NULL)

    # def compile_input(node):
    #     v = input()
    #     index = add_const(v)
    #     emit(LOAD_CONST, index)

    def compile_while(node):
        _, cond, body = node

        loop_addr = next_emit_addr()

        push_while_stack((loop_addr, [], len(scopes)))

        visit(cond)
        addr = emit(JMP_FALSE, -1)

        visit(body)
        emit(JMP, loop_addr)

        back_patch(addr, next_emit_addr())

        _, break_list, _ = pop_while_stack()
        for a in break_list:
            back_patch(a, next_emit_addr())

    def compile_if(node):
        _, cond, true_s, false_s = node

        visit(cond)
        addr1 = emit(JMP_FALSE, -1)

        visit(true_s)
        addr2 = emit(JMP, -1)

        back_patch(addr1, next_emit_addr())

        if false_s is not None:
            visit(false_s)
        else:
            emit(LOAD_NULL)

        back_patch(addr2, next_emit_addr())

    def compile_block(node):
        _, statements = node

        enter_scope()
        addr = emit(ENTER_SCOPE, -1)

        for s in statements:
            visit(s)

        back_patch(addr, len(current_scope()))

        leave_scope()
        emit(LEAVE_SCOPE)

    def compile_call(node):
        _, f, args = node

        visit(f)
        for a in args:
            visit(a)

        emit(CALL, len(args))

    def compile_fun(node):
        _, name, params, body = node

        i = define_var(name)
        addr = emit(LOAD_CONST, -1)  # 函数常量，（函数入口地址，参数个数）
        emit(MAKE_CLOSURE)
        emit(STORE_VAR, 0, i)  # 保存到以函数名命名的变量
        addr2 = emit(JMP, -1)

        # 开始编译函数体
        i = add_const(['compiled fun', next_emit_addr(), len(params)])
        back_patch(addr, i)

        # 创建一个新的作用域用于存放参数
        enter_scope()
        for p in params:
            define_var(p)

        visit(body)

        emit(LOAD_NULL)
        emit(RET)

        leave_scope()
        back_patch(addr2, next_emit_addr())

    def compile_program(node):
        _, statements = node
        for s in statements[0:-1]:
            visit(s)
            emit(POP)
        visit(statements[-1])

    visitors = {
        'program': compile_program,
        'fun': compile_fun,
        'call': compile_call,
        'block': compile_block,
        'if': compile_if,
        'while': compile_while,
        'print': compile_print,
        'return': compile_return,
        'break': compile_break,
        'continue': compile_continue,
        'var': compile_var,
        'assign': compile_assign,
        'binop': compile_binop,
        'uniop': compile_uniop,
        'id': compile_id,
        'num': compile_literal,
        'str': compile_literal,
        'true': compile_bool,
        'false': compile_bool,
        'null': compile_null,
    }

    def visit(node):
        t = node_tag(node)
        if t not in visitors:
            err(f'非法节点{node}')

        v = visitors[t]
        # print(v)

        return v(node)

    visit(ast)

    return code, consts, glob_syms


if __name__ == '__main__':

    filename = './dist/test.cilly'
    with open(filename) as f:
        ast = parser(lexer(f.read()))
    print(ast)
    #
    # ast = ['program', [['fun', 'add', ['x', 'y'], ['block', [['return', ['binop', '+', ['id', 'x'], ['id', 'y']]]]]], ['var', ['id', 'a'], ['num', 1]], ['var', ['id', 'b'], ['num', 2]], ['print', [['call', ['id', 'add'], [['num', 1], ['num', 2]]]]]]]
    # ast = ['program', [
    #     ['fun', 'add', ['a', 'b'], ['block', [
    #         ['return', ['binop', '+', ['id', 'a'], ['id', 'b']]]
    #     ]]],
    #     ['print', [['call', ['id', 'add'], [['num', 4], ['num', 4]]]]]
    # ]]

    code, consts, glob_syms = cilly_vm_compiler(ast, [], [], [])

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
