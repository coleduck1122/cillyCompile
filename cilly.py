import argparse
from cilly_interpreter import *
# from cilly_vm import *

def parse_command_line():
    command = argparse.ArgumentParser(description='Simple compiler')
    command.add_argument('-help', action='store_true', help='to print help message')
    command.add_argument('-lex', nargs='?', help='to perform lexical analysis')
    command.add_argument('-par', nargs='?', help='to perform parsing')
    command.add_argument('-exc', nargs='?', help='(Maintenance) to execute a cilly file')
    command.add_argument('-cat', nargs='?', help='to look up cilly files')
    command.add_argument('-env', action='store_true', help='(Maintenance) to watch current environment variables')
    command.add_argument('-itr', action='store_true', help='to entry interactive mode')
    command.add_argument('-vmc', nargs='?', help='to compiler from ast to opcode')
    command.add_argument('-vme', nargs='?', help='to execute a cilly program in virtual machine')

    return command.parse_args()


def cilly_help():
    print('Usage: cilly [options]')
    print('Options:')
    print('  -help          to print help message')
    print('  -lex [file]    to perform lexical analysis')
    print('  -par [file]    to perform parsing')
    print('  -exc [file]    (Maintenance) to execute a cilly file')
    print('  -cat [file]    to look up cilly files')
    print('  -env           (Maintenance) to watch current environment variables')
    print('  -itr           to entry interactive mode')
    print('  -vmc [file]    to compiler from ast to opcode')
    print('  -vme [file]    to execute a cilly program in virtual machine')


def cilly_lexer(filename):
    if filename is not None:
        with open(filename) as f:
            print(lexer(f.read()))


def cilly_parser(filename):
    if filename is not None:
        with open(filename) as f:
            print(parser(lexer(f.read())))


def cilly_execute(filename):
    envir = {}
    if filename is not None:
        with open(filename) as f:
            print(eval(parser(lexer(f.read())), envir))


def cilly_cat(filename):
    if filename is not None:
        with open(filename) as f:
            print(f.read())


def cilly_env():
    pass


def cilly_interact():
    def exexute(code, env):
        lex = lexer(code)
        eval(parser(lex), env)
    envir = {}
    code = ''
    layer = 0
    while True:
        print('>>>' + ' ' * 2 * layer, end=' ')
        line = input()

        if line == 'exit':
            break

        if line.rstrip()[-1] == '{':
            layer += 1
            code += line + '\n'
        elif line.rstrip()[-1] == '}':
            layer -= 1
            code += line + '\n'
            if layer == 0:
                exexute(code, envir)
                code = ''
            elif layer < 0:
                print('Invalid synix, please input again, key `exit` to break')
        elif line.rstrip()[-1] == ';':
            if layer > 0:
                code += line + '\n'
            elif layer == 0:
                exexute(line, envir)
        else:
            print('Invalid synix, please input again, key `exit` to break')


# def opcode_2_instruction(opcode):
#     c = []
#     i = 0
#     while i < len(opcode):
#         for key, value in zl.items():
#             if opcode[i] == value:
#                 st = ""
#                 for x in c:
#                     st += x + '\t'
#                 print(st)
#                 c = []
#                 c.append(f"{i}: {key}")
#                 f = key
#                 break
#         if f in ["LOAD_CONST", "ENTER_SCOPE", "JMP", "JMP_TRUE", "JMP_FALSE", "CALL"]:
#             c.append(f"{opcode[i + 1]}")
#             f = None
#             i += 1
#         elif f in ["LOAD_VAR", "STORE_VAR"]:
#             c.append(f"{opcode[i + 1]}")
#             c.append(f"{opcode[i + 2]}")
#             f = None
#             i += 2
#         i += 1


# def cilly_vmc(filename):
#     if filename is not None:
#         with open(filename) as f:
#             ast = parser(lexer(f.read()))
#
#     code, consts, glob_syms = cilly_vm_compiler(ast, [], [], [])
#
#     opcode_2_instruction(code)
#     print(consts)
#     print(glob_syms)


# def cilly_vme(filename):
#     if filename is not None:
#         with open(filename) as f:
#             ast = parser(lexer(f.read()))
#
#     code, consts, glob_syms = cilly_vm_compiler(ast, [], [], [])
#     cilly_vm(code, consts, glob_syms)


def main():
    args = parse_command_line()

    if args.help:
        cilly_help()
        return

    if args.lex:
        if args.lex.endswith('.cilly'):
            cilly_lexer(filename=args.lex)

    if args.par:
        if args.par.endswith('.cilly'):
            cilly_parser(filename=args.par)

    if args.exc:
        if args.exc.endswith('.cilly'):
            cilly_execute(filename=args.exc)

    if args.env:
        cilly_env()
        return

    if args.cat:
        cilly_cat(filename=args.cat)

    if args.itr:
        cilly_interact()
        return

    # if args.vmc:
    #     cilly_vmc(filename=args.vmc)
    #     return
    #
    # if args.vme:
    #     cilly_vme(filename=args.vme)
    #     return


if __name__ == '__main__':
    main()
