# jpvm/vm.py
from .instr import Instr

class VM:
    def __init__(self):
        self.stack = []
        self.vars = {}

    def run(self, code: list[Instr]):
        ip = 0
        while ip < len(code):
            ins = code[ip]

            if ins.op == "PUSH":
                self.stack.append(ins.arg)

            elif ins.op == "LOAD":
                if ins.arg not in self.vars:
                    raise NameError(f"未定義変数: {ins.arg}")
                self.stack.append(self.vars[ins.arg])

            elif ins.op == "STORE":
                self.vars[ins.arg] = self.stack.pop()

            elif ins.op == "ADD":
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)

            elif ins.op == "SUB":
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a - b)

            elif ins.op == "PRINT":
                print(self.stack.pop())

            elif ins.op == "HALT":
                return

            else:
                raise RuntimeError(f"不明な命令: {ins.op}")

            ip += 1
