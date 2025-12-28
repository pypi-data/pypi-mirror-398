# jpvm/compiler.py
from .instr import Instr

def _atom(token: str):
    token = token.strip()
    if token.isdigit():
        return [Instr("PUSH", int(token))]
    return [Instr("LOAD", token)]

def compile(src: str) -> list[Instr]:
    code: list[Instr] = []

    for line in src.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("表示 "):
            expr = line[3:].strip()
            if "+" in expr:
                a, b = map(str.strip, expr.split("+", 1))
                code += _atom(a) + _atom(b) + [Instr("ADD"), Instr("PRINT")]
            elif "-" in expr:
                a, b = map(str.strip, expr.split("-", 1))
                code += _atom(a) + _atom(b) + [Instr("SUB"), Instr("PRINT")]
            else:
                code += _atom(expr) + [Instr("PRINT")]
            continue

        if "=" in line:
            name, val = map(str.strip, line.split("=", 1))
            code += _atom(val) + [Instr("STORE", name)]
            continue

        raise SyntaxError(f"解釈できない文: {line}")

    code.append(Instr("HALT"))
    return code
