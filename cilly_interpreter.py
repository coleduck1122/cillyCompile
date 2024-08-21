# import argparse
import numpy as np
from cilly_parser import *
from collections import ChainMap


# 定义求值函数
def eval(expression, envir):
    # 如果表达式为整数或布尔值，则直接返回
    if type(expression) is list and expression[0] in ["id", "num", "str", "vec", "true", "false", "T"]:
        if expression[0] == 'id':
            return envir[expression[1]]
        if expression[0] == 'num':
            return expression[1]
        if expression[0] == 'true':
            return True
        if expression[0] == 'false':
            return False
        if expression[0] == 'T':
            return 'T'
        # 如果表达式为字符串，则返回其内容（去除引号）
        if expression[0] == 'str':
            return expression[1]
        if expression[0] == 'vec':
            res = []
            for item in expression[1]:
                res.append(eval(item, envir))
            return res

        return expression

    # 如果表达式为元组，则检查变量并返回其值
    if type(expression) is tuple:
        return check_variable((expression[0], eval(expression[1], envir)), envir)

    # 处理变量赋值语句
    if type(expression) is list and len(expression) == 3 and expression[0] == 'var':
        set_var(expression[1], eval(expression[2], envir), envir)
        return None

    # 处理导入语句
    if type(expression) is list and len(expression) == 2 and expression[0] == 'import':
        inner_envir = {}
        eval(parser(lexer(open(expression[1]).read())), inner_envir)
        envir.update(inner_envir)
        return None

    # 处理赋值语句
    if type(expression) is list and len(expression) == 3 and expression[0] == 'assign':
        var = expression[1]
        if type(var) is list:
            check_variable(var, envir)
            set_var(var, eval(expression[2], envir), envir)
            return None
        if type(var) is tuple and len(var) == 2:
            check_variable((var[0], eval(var[1], envir)), envir)
            set_var(var, eval(expression[2], envir), envir)
            return None
        else:
            err(f'{var} is not a legal var')

    # 处理函数定义语句
    if type(expression) is list and len(expression) == 4 and expression[0] == 'fun':
        set_var(expression[1], ['proc', expression[2], expression[3], envir], envir)
        return None

    # 处理阶乘函数
    if type(expression) is list and len(expression) == 2 and expression[0] == 'frac':
        if type(expression[1]) is not int:
            err(f'{expression[1]} is not an integer')
        frac = 1
        for i in range(1, expression[1] + 1):
            frac *= i
        return frac

    # 处理函数调用
    if type(expression) is list and len(expression) == 3 and expression[0] == 'call':
        f = eval(expression[1], envir)
        if type(f) != list or f[0] != 'proc':
            err(f'{f} is not a function')

        old_envir = f[3]
        old_envir = ChainMap({expression[1]: f}, old_envir)
        new_envir = old_envir.copy()

        if expression[2] is not None:
            new_envir = ext_env(f[1], [eval(e, envir) for e in expression[2]], old_envir)

        this_ret = eval(f[2], new_envir)
        up_env(f[3], new_envir)
        if type(this_ret) is list and this_ret[0] == 'return':
            return this_ret[1]
        else:
            return None

    # 处理代码块
    if type(expression) is list and len(expression) == 2 and expression[0] == 'block':
        for e in expression[1]:
            this_ret = eval(e, envir)
            if type(this_ret) == list and this_ret[0] == "return":
                return this_ret
        return None

    # 处理return语句
    if type(expression) is list and len(expression) == 2 and expression[0] == 'return':
        return ['return', eval(expression[1], envir)]

    # 处理if语句
    if type(expression) is list and len(expression) == 4 and expression[0] == 'if':
        cond = eval(expression[1], envir)
        if cond == True:
            return eval(expression[2], envir)
        else:
            if expression[3] == None:
                return None
            else:
                return eval(expression[3], envir)

    # 处理while语句
    if type(expression) is list and len(expression) == 3 and expression[0] == 'while':
        while eval(expression[1], envir):
            this_ret = eval(expression[2], envir)
            if type(this_ret) == list and this_ret[0] == "return":
                return this_ret

        return None

    # 处理print语句
    if type(expression) is list and len(expression) == 2 and expression[0] == 'print':
        st = ""
        cnt = 0
        for e in expression[1]:
            if cnt > 0:
                st += ' '
            cnt += 1
            st += str(eval(e, envir))
        print(st)
        return None

    if type(expression) is list and len(expression) == 2 and expression[0] == 'show':
        st = ''
        res = eval(expression[1], envir)
        if type(res) is list:
            # 矩阵
            if type(res[0]) is list:
                res = [[str(x) for x in y] for y in res]
                if len(res) == 1:
                    st += '[[' + ','.join(res[0]) + ']]'
                else:
                    st += '[[' + ','.join(res[0]) + '],' + '\n'
                    for item in res[1:-1]:
                        st += ' [' + ','.join(item) + '],' + '\n'
                    st += ' [' + ','.join(res[-1]) + ']]'
            # 向量
            else:
                res = [str(x) for x in res]
                st += '[' + ','.join(res) + ']'
            print(st)
        else:
            print(res)

        return None

    # 系统函数
    if type(expression) is list and len(expression) == 1 and expression[0] == 'input':
        this_ret = input()
        return this_ret

    if type(expression) is list and len(expression) == 2 and expression[0] == 'abs':
        return abs(eval(expression[1], envir))

    if type(expression) is list and len(expression) == 2 and expression[0] == 'int':
        return int(eval(expression[1], envir))

    if type(expression) is list and len(expression) == 2 and expression[0] == 'len':
        return len(eval(expression[1], envir))

    if type(expression) is list and len(expression) == 2 and expression[0] == 'type':
        val = eval(expression[1], envir)
        if type(val) is int:
            return 'int'
        if type(val) is bool:
            return 'bool'
        if type(val) is str:
            return 'str'
        if type(val) is list:
            return 'arr'

    if type(expression) is list and len(expression) == 2 and expression[0] == 'tr':
        res = eval(expression[1], envir)
        if type(res) is list and type(res[0]) is list:
            return np.trace(np.array(res))
        else:
            err(f'type error:{res} is not matrix, cannot use tr()')

    if type(expression) is list and len(expression) == 2 and expression[0] == 'eig':
        res = eval(expression[1], envir)
        if type(res) is list and type(res[0]) is list and len(res) == len(res[0]):
            eigenvalues, eigenvectors = np.linalg.eig(res)
            return eigenvalues, eigenvectors
        else:
            err(f'type error:{res} is not square matrix, cannot use eig()')

    if type(expression) is list and len(expression) == 2 and expression[0] == 'det':
        res = eval(expression[1], envir)
        if type(res) is list and type(res[0]) is list and len(res) == len(res[0]):
            return np.linalg.det(np.array(res))
        else:
            err(f'type error:{res} is not square matrix, cannot use det()')

    if type(expression) is list and len(expression) == 2 and expression[0] == 'inv':
        res = eval(expression[1], envir)
        if type(res) is list and type(res[0]) is list and len(res) == len(res[0]):
            return np.linalg.inv(np.array(res)).tolist()
        else:
            err(f'type error:{res} is not square matrix, cannot use inv()')

    # if type(expression) is list and len(expression) == 2 and expression[0] == 'arr':
    #     length = eval(expression[1], envir)
    #     this_ret = [0 for i in range(length)]
    #     return this_ret

    if type(expression) is list and len(expression) == 2 and expression[0] == 'program':
        for e in expression[1]:
            this_ret = eval(e, envir)
            if type(this_ret) == list and this_ret[0] == "return":
                return this_ret[1]
        return ""

    # 处理二元操作符
    if type(expression) is list and len(expression) == 4 and expression[0] == 'binop':
        first = eval(expression[2], envir)
        second = eval(expression[3], envir)
        option = expression[1]
        arr1 = None
        arr2 = None
        if first == [] or first == [[]] or second == [] or second == [[]]:
            err('矩阵或向量不能为空')

        if option == '>':
            return first > second
        if option == '>=':
            return first >= second
        if option == '<':
            return first < second
        if option == '<=':
            return first <= second
        if option == '==':
            return first == second
        if option == '!=':
            return first != second

        if option == '^':
            # A^T -> A的转置矩阵
            if type(first) is list and type(first[0]) is list and second == 'T':
                matrix = np.array(first)
                return np.transpose(matrix).tolist()
            # A^B -> A的B次幂
            return first ^ second

        if option == '+':
            if type(first) is list:
                arr1 = np.array(first)
            if type(second) is list:
                arr2 = np.array(second)
            # 向量 + 向量
            if np.any(arr1) and (type(first[0]) is not list) and np.any(arr2) and (type(second[0]) is not list):
                if arr1.shape != arr2.shape:
                    err(f'向量大小不匹配')
                return (arr1 + arr2).tolist()
            # 矩阵 + 矩阵
            if np.any(arr1) and np.any(arr2):
                if arr1.shape != arr2.shape:
                    err(f'矩阵大小不匹配')
                return (arr1 + arr2).tolist()
            # 标量 + 标量
            return first + second

        if option == '-':
            if type(first) is list:
                arr1 = np.array(first)
            if type(second) is list:
                arr2 = np.array(second)
            # 向量 - 向量
            if np.any(arr1) and (type(first[0]) is not list) and np.any(arr2) and (type(second[0]) is not list):
                if arr1.shape != arr2.shape:
                    err(f'向量大小不匹配')
                return (arr1 - arr2).tolist()
            # 矩阵 - 矩阵
            if np.any(arr1) and np.any(arr2):
                if arr1.shape != arr2.shape:
                    err(f'矩阵大小不匹配')
                return (arr1 - arr2).tolist()
            # 标量 - 标量
            return first - second

        if option == '*':
            if type(first) is list:
                arr1 = np.array(first)
            if type(second) is list:
                arr2 = np.array(second)
            # 向量 * 向量
            if np.any(arr1) and (type(first[0]) is not list) and np.any(arr2) and (type(second[0]) is not list):
                if arr1.shape != arr2.shape:
                    err(f'向量大小不匹配')
                return (arr1 * arr2).tolist()
            # 向量 * 标量
            if np.any(arr1) and (type(first[0]) is not list) and not np.any(arr2):
                return (arr1 * second).tolist()
            # 标量 * 向量
            if np.any(arr2) and (type(second[0]) is not list) and not np.any(arr1):
                return (arr2 * first).tolist()
            # 矩阵 * 矩阵
            if np.any(arr1) and np.any(arr2):
                if arr1.shape[1] != arr2.shape[0]:
                    err(f'矩阵大小不匹配')
                return np.dot(arr1, arr2).tolist()
            # 矩阵 * 标量
            if np.any(arr1) and not np.any(arr2):
                return (arr1 * second).tolist()
            # 标量 * 矩阵
            if np.any(arr2) and not np.any(arr1):
                return (arr2 * first).tolist()
            # 标量 * 标量
            return first * second

        if option == '/':
            return first / second


    # 处理一元操作符
    if type(expression) is list and len(expression) == 3 and expression[0] == 'uinop':
        option = expression[1]
        if option == '!':
            return not eval(expression[2], envir)
        if option == '-':
            return -eval(expression[2], envir)
        if option == 'frac':
            num = eval(expression[2], envir)
            for i in range(1, num):
                num *= i
            return num

    # 若未匹配到任何情况，则抛出异常
    err(f'illegal expression{expression}')


# 异常处理函数
def err(e):
    raise Exception(e)


# 设置变量
def set_var(var, val, envir):
    if type(var) is tuple:
        var2 = tk_val(var[0])
        pos = eval(var[1], envir)
        # print(var2, pos)
        element = envir[var2]
        for x in pos[:-1]:
            element = element[x]
        element[pos[-1]] = val
    else:
        envir[tk_val(var)] = val


# 更新环境
def up_env(envir, new_envir):
    for var, val in envir.items():
        envir[var] = check_variable(var, new_envir)


# 检查变量
def check_variable(var, envir):
    if type(var) is list:
        var = var[1]
        if var not in envir:
            err(f'unbound variable{var}')
        return envir[var]

    if type(var) is tuple:
        var2 = tk_val(var[0])
        pos = var[1]
        # print(var2, var[1])
        if var2 not in envir:
            err(f'unbound variable{var[0]}')

        try:
            element = envir[var2]
            for x in pos[:-1]:
                element = element[x]
            return element[pos[-1]]
        except Exception as e:
            err(e)


# 扩展环境
def ext_env(vars, vals, envir):
    e = {var: val for (var, val) in zip(vars, vals)}

    return ChainMap(e, envir)



if __name__ == '__main__':
    # main()
    envir = {}
    with open('./dist/test.cilly') as f:
        code = f.read()
        # print(code)
        lex = lexer(code)
        print(lex)
        par = parser(lex)
        print(par)
        ans = eval(par, envir)
        print(ans)
