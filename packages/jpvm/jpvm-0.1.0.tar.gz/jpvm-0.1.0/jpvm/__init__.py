# jpvm/__init__.py
from .vm import VM
from .compiler import compile as _compile

class 仮想機械(VM):
    pass

def 実行(ソースコード: str):
    vm = 仮想機械()
    バイトコード = _compile(ソースコード)
    vm.run(バイトコード)

__all__ = ["実行", "仮想機械"]
