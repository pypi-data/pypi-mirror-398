from untvgdev.core.bx1.UnitBytexCore import Parser, InterpreteError
from .__executor import Executor
import sys

# for cycles
sys.setrecursionlimit(16384)



class Interpreter:
    def __init__(self):
        self.exec = Executor()
        self.points_code = {}
        self.points = []
    
    def execute(self, code):
        code_spl = Parser(code) # splitted code
        for line in code_spl:
            try: 
                result = self.exec.exec(line)
            except Exception as e:
                raise InterpreteError(f"\n{e.__class__}: {e}\nLine {code_spl.index(line)}:\n>  {' '.join(line)}")
            if result.to_return != None: 
                return result.to_return
        return self




def execute(code: str) -> int | None:
    return Interpreter().execute(code)




if __name__ == '__main__':
    execute('''
point input; p:input jump 1234;
point basic; p:basic jump 0;
point temp; p:temp jump 8421;
point main;
    p:main goto temp;
    p:main copy 1235;
    p:main goto input;
    p:main op * >;
    p:main out .;
goto temp; print Введите число 1:~; in num; goto basic;
goto input; print Введите число 2:~; in num; goto basic;
goto main;
>;
    ''')