class VirtualMachine:
    def __init__(self):
        self.instructions = []
        self.constants = []
        self.variables = {}
        self.scope_stack = []

    def define_var(self, name):
        if name in self.variables:
            return self.variables[name]
        else:
            index = len(self.variables)
            self.variables[name] = index
            return index

    def emit(self, opcode, *operands):
        addr = len(self.instructions)
        self.instructions.append((opcode, operands))
        return addr

    def next_emit_addr(self):
        return len(self.instructions)

    def back_patch(self, addr, target):
        opcode, operands = self.instructions[addr]
        self.instructions[addr] = (opcode, (target, *operands[1:]))

    def enter_scope(self):
        self.scope_stack.append(self.variables.copy())
        self.variables.clear()

    def leave_scope(self):
        self.variables = self.scope_stack.pop()

    def add_const(self, const):
        index = len(self.constants)
        self.constants.append(const)
        return index

    def visit(self, node):
        if isinstance(node, list) and isinstance(node[0], list):
            for subnode in node:
                self.visit(subnode)
        elif isinstance(node, list):
            if node[0] == 'program':
                for stmt in node[1]:
                    self.visit(stmt)
            elif node[0] == 'assign':
                _, var_name, expr = node
                self.visit(expr)
                var_index = self.define_var(var_name)
                self.emit('STORE_VAR', var_index)
            elif node[0] == 'var':
                _, var_name, expr = node
                self.visit(expr)
                var_index = self.define_var(var_name)
                self.emit('STORE_VAR', var_index)
            elif node[0] == 'binop':
                _, op, left, right = node
                self.visit(left)
                self.visit(right)
                if op == '+':
                    self.emit('ADD')
                elif op == '-':
                    self.emit('SUB')
                elif op == '*':
                    self.emit('MUL')
                elif op == '/':
                    self.emit('DIV')
                elif op == '<':
                    self.emit('LT')
            elif node[0] == 'id':
                var_name = node[1]
                var_index = self.variables[var_name]
                self.emit('LOAD_VAR', var_index)
            elif node[0] == 'num':
                num_value = node[1]
                const_index = self.add_const(num_value)
                self.emit('LOAD_CONST', const_index)
            elif node[0] == 'print':
                for expr in node[1]:
                    self.visit(expr)
                    self.emit('PRINT')
            elif node[0] == 'fun':
                self.compile_fun(node)
            elif node[0] == 'call':
                _, func, args = node
                for arg in args:
                    self.visit(arg)
                func_index = self.variables[func[1]]
                self.emit('CALL_FUNCTION', func_index, len(args))
            elif node[0] == 'while':
                self.compile_while(node)
            elif node[0] == 'if':
                self.compile_if(node)
            elif node[0] == 'block':
                for stmt in node[1]:
                    print(stmt)
                    self.visit(stmt)
            elif node[0] == 'return':
                self.visit(node[1])  # 首先计算返回值表达式
                self.emit('RET')  # 然后执行返回指令

    def compile_fun(self, node):
        print(node)
        _, name, params, body = node

        # Define the function as a variable
        var_index = self.define_var(name)
        func_index = self.add_const(['compiled fun', -1, len(params)])  # Placeholder for function address
        self.emit('LOAD_CONST', func_index)
        self.emit('STORE_VAR', var_index)

        # Record the jump address to the function body
        jump_addr = self.emit('JMP', -1)
        #print(jump_addr)
        # Compile the function body
        self.enter_scope()
        for param in params:
            self.define_var(param)
        #print(body)
        self.visit(body)
        #self.emit('RET')
        self.leave_scope()

        # Backpatch the jump address
        self.back_patch(jump_addr, self.next_emit_addr())

        # Update function address after compiling the body
        self.constants[func_index][1] = jump_addr+1 #self.next_emit_addr()
        #print(self.next_emit_addr)


    def compile_while(self, node):
        _, condition, body = node

        # Start of the loop
        loop_start = self.next_emit_addr()
        print("Loop start:", loop_start)

        # Compile the condition
        self.visit(condition)

        # Jump out of the loop if the condition is false
        jmp_false = self.emit('JMP_IF_FALSE', -1)

        # Remember the address of the condition check
        condition_check_addr = self.next_emit_addr() - 1

        # Compile the loop body
        print("Loop body start:", self.next_emit_addr())
        self.visit(body)
        print("Loop body end:", self.next_emit_addr())

        # Jump back to the start of the loop
        self.emit('JMP', loop_start)

        # Patch the false jump to the instruction after the loop body
        self.back_patch(jmp_false, self.next_emit_addr())

        # Patch the condition check to jump to the end of the loop if condition is false
        self.back_patch(condition_check_addr, self.next_emit_addr())



    def compile_if(self, node):
        _, condition, if_body, else_body = node

        # Compile condition
        self.visit(condition)
        jmp_if_false = self.emit('JMP_IF_FALSE', -1)

        # Compile if-body
        self.visit(if_body)
        jmp_end = self.emit('JMP', -1)

        # Patch false jump address
        self.back_patch(jmp_if_false, self.next_emit_addr())

        # Compile else-body
        if else_body:
            self.visit(else_body)

        # Patch end jump address
        self.back_patch(jmp_end, self.next_emit_addr())


class VirtualMachineExecutor:
    def __init__(self, instructions, constants):
        self.instructions = instructions
        self.constants = constants
        self.stack = []
        self.variables = {}
        self.scope_stack = []
        self.pc = 0  # Program counter

    def run(self):
        while self.pc < len(self.instructions):
            opcode, operands = self.instructions[self.pc]
            self.pc += 1
            #print(self.pc)
            self.execute(opcode, operands)

    def execute(self, opcode, operands):
        if opcode == 'LOAD_CONST':
            index = operands[0]
            #print(self.constants[index])
            self.stack.append(self.constants[index])
        elif opcode == 'STORE_VAR':
            var_index = operands[0]
            value = self.stack.pop()
            self.variables[var_index] = value
        elif opcode == 'LOAD_VAR':
            var_index = operands[0]
            self.stack.append(self.variables[var_index])
        elif opcode == 'ADD':
            #print(0)
            right = self.stack.pop()
            left = self.stack.pop()
            #print(left+right)
            self.stack.append(left + right)
        elif opcode == 'SUB':
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left - right)
        elif opcode == 'MUL':
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left * right)
        elif opcode == 'DIV':
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left / right)
        elif opcode == 'LT':
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left < right)
        elif opcode == 'PRINT':
            value = self.stack.pop()
            print("Output:", value)
        elif opcode == 'JMP':
            target = operands[0]
            self.pc = target
            #print(target)
        elif opcode == 'CALL_FUNCTION':
            func_index, arg_count = operands
            func = self.constants[func_index]
            #print(func)
            if isinstance(func, list) and func[0] == 'compiled fun':
                entry_point, param_count = func[1], func[2]
                if arg_count != param_count:
                    raise ValueError(f"Expected {param_count} arguments, got {arg_count}")
                #print(self.pc)

                # Collect arguments in the correct order
                args = [self.stack.pop() for _ in range(arg_count)][::-1]

                # Push return address onto stack
                self.stack.append(self.pc)
                #print(self.pc)
                self.enter_scope()
                for i, arg in enumerate(args):
                    #print(arg)
                    self.variables[i] = arg
                # Set the program counter to the entry point of the function
                #print(entry_point)
                self.pc = entry_point
            else:
                raise ValueError("Unsupported function call")
        elif opcode == 'RET':
            # Pop return value from stack
            return_value = self.stack.pop()
            #print(return_value)
            # Leave current scope
            self.leave_scope()
            if self.stack:  # Check if stack is not empty
                # Pop return address from stack
                self.pc = self.stack.pop()  # Set program counter to return address
                # Push return value to stack
                self.stack.append(return_value)
            else:
                # Set program counter to 0 to terminate execution
                self.pc = 0
                # Print return value
                print("Return value:", return_value)
        elif opcode == 'JMP_IF_FALSE':
            print("1")
            target = operands[0]
            condition = self.stack.pop()
            if not condition:
                self.pc = target


    def enter_scope(self):
        self.scope_stack.append(self.variables.copy())
        self.variables.clear()

    def leave_scope(self):
        if not self.scope_stack:
            raise ValueError("Attempted to leave scope when scope stack is empty")
        self.variables = self.scope_stack.pop()



# 示例代码
vm = VirtualMachine()


# 节点表示

c4= '''
var x = 1;
var y = x + 5;
print(x+y);
'''

node = ['program', [
    ['var', 'x', ['num', 1]],
    ['var', 'y', ['binop', '+', ['id', 'x'], ['num', 5]]],
    ['print', [['binop', '+', ['id', 'x'], ['id', 'y']]]]
]]

c2 = '''
print(1,42, 2*3-5*4);
'''

node1 = ['program', [
    ['print', [
        ['num', 1],
        ['num', 42],
        ['binop', '-', ['binop', '*', ['num', 2], ['num', 3]], ['binop', '*', ['num', 5], ['num', 4]]]
    ]]
]]

node2 = ['program', [
    ['fun', 'add', ['a', 'b'], ['block', [
        ['return', ['binop', '+', ['id', 'a'], ['id', 'b']]]
    ]]],
    ['print', [['call', ['id', 'add'], [['num', 4], ['num', 4]]]]]
]]

node3 = ['program', [
    ['var', 'x', ['num', 0]],
    ['while', ['binop', '<', ['id', 'x'], ['num', 5]], [
        ['print', [['id', 'x']]],
        ['var', 'x', ['binop', '+', ['id', 'x'], ['num', 2]]]
    ]]
]]

node4 = ['program', [
    ['var', 'x', ['num', 10]],
    ['if', 
        ['binop', '<', ['id', 'x'], ['num', 5]], 
        [['print', [['num', 1]]]], 
        [['print', [['num', 2]]]]
    ]
]]

node5 = [
    'program', [
        ['assign', 'sum', ['num', 0]],
        ['assign', 'i', ['num', 1]],
        ['while', ['binop', '<=', ['id', 'i'], ['num', 100]], [
            ['block', [
                ['assign', 'sum', ['binop', '+', ['id', 'sum'], ['id', 'i']]],
                ['assign', 'i', ['binop', '+', ['id', 'i'], ['num', 1]]]
            ]]
        ]],
        ['print', [['id', 'sum']]]
    ]
]

vm.visit(node5)
# 输出生成的指令
for i, instr in enumerate(vm.instructions):
    print(f'{i}: {instr}')
#print(vm.constants)

# 执行指令
executor = VirtualMachineExecutor(vm.instructions, vm.constants)
executor.run()
