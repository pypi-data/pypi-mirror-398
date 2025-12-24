'''
# BYTEX2
Main file of bytex translator.

## Extend:
    parse(code: str) -> list[list[str]]

        : Simple language parser and splitter.
    
    Generator : metaclass

        : Metaclass for code generation.
    
    Translator : class

        : Main class for translation bytex to python instructions.
'''



from .exceptions import *
from .basics import core



def parse(code: str) -> list[list[str]]:
    '''
    # Parser
    Simple Bytex2 code splitter and parser.
    '''
    code = code.replace(';', '\n')
    commands = []
    for i in code.split('\n'):
        command = []
        i = i.strip()
        for j in i.split(' '):
            command.append(j)
        if command != ['']:
            commands.append(command)
    return commands

















# metaclass
class Generator:
    '''
    # Generator
    Metaclass for code generation.
    '''
    def __init__(self):
        self._code = []
        self._pre = []
        self._end = []
        self._log = []
        self.tabs = 0
    
    def _line(self, code: str):
        '''
        Add code (to _code)
        '''
        self._code.append('    ' * self.tabs + code)
    
    @property
    def code(self):
        '''
        Returning all builded code in format:

        - core code
        - raw code   (_log)
        - pre code   (_pre)
        - main code  (_code)
        - pos code   (_end)
        '''
        code = f'''
# =============================
#         core code
# =============================
{'\n'.join(core)}



# =============================
#          raw code
# =============================
RAW = """
{'\n'.join(self._log)}
"""


# =============================
#      compiled code: pre
# =============================
{'\n'.join(self._pre)}


# =============================
#     compiled code: main
# =============================
{'\n'.join(self._code)}



# =============================
#     compiled code: post
# =============================
{'\n'.join(self._end)}
        '''
        return code.split('\n')











class Translator(Generator):
    def __init__(self, safemode: bool = False):
        super().__init__()
        self.in_struct = 0
        self.included = []
        self.user_structs = {
            'COMMAND':{'PARSER': lambda context, line: 0 } # EXAMPLE
            # context - [Translator] object
            # line - full line ([0] - is command)
        }
        self.writepython = False
        self.safe = safemode
        
    def translate(self, code: str):
        code = parse(code)
        self.parse(code)
        return self.code
    
    def command(self, command: str, parser: object):
        '''
        Add command to language.
        
        Args:
            - command : str 
                - command to parse
            
            - parser : object - function (context: Translator, line: list[str])
                - object to parse command
        '''
        self.user_structs[command] = {'PARSER': parser}
        return self
    
    def pre_edit(self, code: list[str]):
        for line in code: 
            self._pre.append(line)
        return self

    def post_edit(self, code: list[str]):
        for line in code: 
            self._end.append(line)
        return self

    def main_edit(self, code: list[str]):
        for line in code: 
            self._code.append(line)
        return self
    
    def plugin(self, type: str = 'command'):
        '''
        Add Plugin to language. 
        
        types: 
            - command 
                -> function (command: str, parser: object)
                : add command to language
            - main
                -> function (code: list[str])
                : edit main code
            - pre 
                -> function (code: list[str])
                : edit code preprocess
            - post
                -> function (code: list[str])
                : edit finalization code
        '''
        if type == 'command':
            return self.command
        elif type == 'pre':
            return self.pre_edit
        elif type == 'post':
            return self.post_edit
        elif type == 'main':
            return self.main_edit
        else:
            raise Bytex2Error('Plugin error', f'Unknown type of plugin: {type}')
        
    def parse(self, code: list):
        for line in code:
            try: 
                self._log.append(
                    str(code.index(line)) + "- " +
                    ' '.join(line)
                )
                if self.writepython and line[0] != 'python': 
                    if not self.safe:
                        self._line(" ".join(line).replace('\\tab|', '    '))
                    else:
                        raise RuntimeError('Safemode error', 'Turn off safe mode.')
                else:
                    self.work(line)
            except Exception as e: 
                raise TranslationError('Interpritation error', str(e), line, code, 1)
                
    
    
    
    def work(self, line: list[str]):
        command = line[0]
        self._line(f'# line: {repr(" ".join(line))}')
        if command.startswith('#') and command != '#':
            self._preprocess(line)
            return
        elif command.startswith(('$', '@')):
            self._system(line)
            return
        elif command.startswith('!'):
            self._param(line)
            return
        elif command in self.user_structs.keys():
            try: self.user_structs[command]['PARSER'](self, line)
            except Exception as e:
                raise Bytex2Error(f'Plugin exception', str(e))
        else:
            self._main(line)
            return
    
    
    
    
    
    def _preprocess(self, line):
        command = line[0]
        args = line[1:]
        def checklen(length: int = 0, operator: str = "!="):
            if not eval(f'len(args) {operator} length'):
                raise SyntaxError(f"Invalid argument length: {len(args)} (must be {length})")
        match command:
            case '#append':
                checklen(1, '==')
                try:
                    with open(f"{args[0]}.btx", 'r') as f:
                        content = f.read()
                except FileNotFoundError:
                    raise Bytex2Error('Include error', 
                            f"Module {name} is not found.")
                compiled = Translator().translate(content)
                self._pre.append(f'# APPEND: {args[0]}')
                self._pre.append(f'class {args[0].split("/")[-1]}:')
                [self._pre.append('    ' + str(i))
                for i in compiled]
            
            case '#include':
                checklen(1, '>=')
                if self.safe:
                    raise Bytex2Error("Include error', 'Include is not available in safemode. Turn off safemode or use '#append'.")
                name = args[0]
                libs = [name] if len(args) == 1 else args[1:]
                append = f'{name}{libs}'
                if append in self.included: return
                else: 
                    self.included.append(append)
                try:
                    with open(f"{name}.btx", 'r') as f:
                        content = f.read()
                except FileNotFoundError:
                    raise Bytex2Error('Include error', 
                            f"Module {name} is not found.")
                localscope = locals()
                code = Translator().translate(content)
                code = '\n'.join(code)
                exec(code, localscope, localscope)
                if localscope['_is_lib']:
                    if localscope['in_lib']:
                        raise Bytex2Error('Include error', 
                            "Lib is not finished or unknown syntax. Did you forget add '#ELIB' block?")
                    for lib in libs:
                        try:self.pre_edit([f'{lib} = """{localscope[f"LIB{lib}"]}"""'])
                        except KeyError:
                            raise Bytex2Error('Include error', 
                                f"Lib {lib} is not found in file.")
                        self.pre_edit([f'exec({lib})'])
                        self.pre_edit([f'libs.append("{lib}")'])
                        self.work(['create', 'lib_' + lib, lib])
                else:
                    raise Bytex2Error('Include error', "File has no lib. Did you mean '#append'?")
           
            case '#import':
                checklen(1, '>=')
                libs = args[0:]
                for lib in libs:
                    try:
                        __import__(str(lib))
                    except ImportError:
                        raise Bytex2Error('Import error', f"Lib {lib} is not found.")
                    self._pre.append(f'import {lib}')
            
            case '#SLIB': # start LIB
                checklen(1, '==')
                self._line('in_lib = True')
                self._line(f'LIB{args[0]} = """\n')
                self.work(['struct', "lib_" + args[0]])
            
            case '#ELIB': # end LIB
                checklen(0, '==')
                self.work(['endstruct'])
                self._line('"""; in_lib = False')
            
            case _:
                raise SyntaxError('Unknown preprocess command')
    
    
    
    
    
    def _system(self, line):
        command = line[0]
        args = line[1:]
        def checklen(length: int = 0, operator: str = "!="):
            if not eval(f'len(args) {operator} length'):
                raise SyntaxError(f"Invalid argument length: {len(args)} (must be {length})")
        match command:
            case '@islib':
                checklen(0, '==')
                self._pre.append(f'_is_lib = True')
                
            case '$jit':
                self._line(f'@jit({" ".join(args)})')
            
            case '$check':
                arg = args[0]
                match arg:
                    case 'unsafe':
                        if not self.safe:
                            self._line('raise SystemError("\nCode execution must be in safemode.")')
                    case 'safe':
                        if self.safe:
                            self._line('raise SystemError("\nCode execution must be without safemode.")')
                    case 'lib':
                        self.main_edit([
                            'if not _is_lib:'
                            '    raise SystemError("\nCode must be lib.")'
                        ])
                    case _:
                        cond = " ".join(args[0:])
                        self._line(f'if {cond}:')
                        self._line(f'    raise SystemError("\\nSystem check failed ({cond}).")') 
            
            case '$require':
                self._line(f'if not LANG.haslib("{args[0]}"):')
                self._line(f'''    raise ImportError("Lib {args[0]} is not included. Did you forgot wtite '#include [module] {args[0]}'?")''')
            
            case '$addtabs':
                self.tabs += 1

            case '$subtabs':
                self.tabs -= 1
            
            case _:
                raise SyntaxError('Unknown system command')
    
    
    
    
    def _param(self, line):
        command = line[0]
        args = line[1:]
        def checklen(length: int = 0, operator: str = "!="):
            if not eval(f'len(args) {operator} length'):
                raise SyntaxError(f"Invalid argument length: {len(args)} (must be {length})")
        match command:
            case '!ldtp': # load data to parameter
                checklen(2, '==')
                addr = args[0]
                self._line(f'MEM.setto_p({args[1]}, {addr})')
            
            case '!ldfp': # load data from parameter
                checklen(1, '==')
                self._line(f'MEM.setdata(\n{"    " * (self.tabs + 1)}MEM.getfrom_p({args[0]})\n{"    " * self.tabs})')
            
            case '!gdfp': # get data from parameter
                checklen(2, '==')
                addr = args[0]
                self._line(f'{args[1]} = MEM.getfrom_p({addr})')
            
            case _:
                raise SyntaxError('Unknown parameter command')
    
    
    
    def _main(self, line):
        command = line[0]
        args = line[1:]
        def operation(a, b, op):
            self._line(f'# operation {a} {op} {b}')
            self._line(f'__res = MEM.getdata({a}) {op} MEM.getdata({b})')
            self._line(f'MEM.setdatato({a}, __res)')
        def operationreg(rega, regb, a, b, op):
            self._line(f'# register operation')
            self._line(f'# {rega}:{a} {op} {regb}:{b}')
            self._line(f'__res = MEM.getreg({rega})[{a}] {op} MEM.getreg({regb})[{b}]')
            self._line(f'MEM.regs[{rega}][{a}] = __res')
        def checklen(length: int = 0, operator: str = "!="):
            if not eval(f'len(args) {operator} length'):
                raise SyntaxError(f"Invalid argument length: {len(args)} (must be {length})")
                
        match command:
            case 'start': # declarate point
                self._line(f'# start of point {args[0]}')
                self._pre.append(f'points.append("{args[0]}")')
                self._line(f'def {args[0]}():')
                self.tabs += 1
                self._line('pass')
            
            case 'python':
                self.writepython = not self.writepython
            
            case 'func': # declarate function
                checklen(1, ">=")
                self._line(f'# start of function {args[0]}')
                if self.in_struct:
                    func_args = "self, " + " ".join(args[1:])
                    self._line(f'def {args[0]}({func_args}):')
                    self.tabs += 1
                    self._line('pass')
                else:
                    raise SyntaxError('Must be in struct')
        
            case 'sfunc': # declarate static function
                checklen(1, ">=")
                self._line(f'# start of function {args[0]}')
                func_args = " ".join(args[1:])
                self._line("@staticmethod")
                self._line(f'def {args[0]}({func_args}):')
                self.tabs += 1
                self._line('pass')
            
            case 'stdfunc':
                checklen(1, ">=")
                self._line(f'# start of function {args[0]}')
                func_args = " ".join(args[1:])
                self._line(f'def {args[0]}({func_args}):')
                self.tabs += 1
                self._line('pass')
            
            case 'struct':
                checklen(1, "==")
                self._line(f'# start of structure {args[0]}')
                self._line(f'class {args[0]}:')
                self.in_struct += 1
                self.tabs += 1
                self._line('_ = None')

            case 'VM':
                checklen(1, ">=")
                self._line(f'MEM.{args[0]} {" ".join(args[1:])}')
            
            case 'self':
                checklen(1, ">=")
                if self.in_struct:
                    self._line(f'self.{args[0]} {" ".join(args[1:])}')
                else:
                    raise SyntaxError('Must be in struct')
            
            case 'create':
                checklen(2, ">=")
                self._line(f'# creating object')
                class_name = args[0]
                obj_name = args[1]
                constr_args = args[2:] if len(args) > 2 else []
                self._line(f'{obj_name} = {class_name}({" ".join(constr_args)})')
            
            case 'do':
                checklen(1, ">=")
                func_name = args[0]
                func_args = args[1:] if len(args) > 1 else []
                self._line(f'{func_name}({" ".join(func_args)})')

            case 'loop':
                checklen(0, "==")
                self._line(f'# loop')
                self._line(f'while True:')
                self.tabs += 1
                self._line('None')

            case 'repeat':
                checklen(1, "==")
                self._line(f'# repeat loop')
                self._line(f'for i in range({args[0]}):')
                self.tabs += 1
                self._line('None')
            
            case 'iters':
                checklen(2, "==")
                self._line(f"if {repr(args[0])} in points: MEM.repeat({args[0]}, {args[1]})")
            
            case 'delay':
                checklen(1, "==")
                self._line(f'time.sleep({args[0]} * 0.001)')
                
            case 'break':
                self._line(f'# break loop')
                if len(args) > 0:
                    if args[0] == 'if':
                        operator = args[1]
                        value = args[2]
                        self._line(f'if MEM.getdata() {operator} {value}:break')
                else: self._line('break')
            
            case 'end': # end of block
                checklen(0, "==")
                if self.tabs >= 1: self.tabs -= 1
            
            case 'endstruct': # end of structure
                checklen(0, "==")
                if self.tabs >= 1: 
                    self.tabs -= 1; 
                    self.in_struct -= 1
                
            case 'try':
                checklen(0, "==")
                self._line('try:')
                self.tabs += 1
                self._line('None')

            case 'err':
                checklen(0, "==")
                self._line('except Exception as e:')
                self.tabs += 1
                self._line('None')
            
            case 'handle':
                checklen(0, "==")
                self._line('except Exception as e: print(e)')
                
            case 'debug':
                checklen(0, "==")
                self._line('print(f"DEBUG: CURSOR={MEM.CURSOR}, ' \
                    'POINTER={MEM.POINTER}, DATA={MEM.getdata()}, HAND={MEM.hand}")')
                
            case 'goto':
                checklen(1, "==")
                self._line(f'if "{args[0]}" in points:')
                self.tabs += 1
                self._line(f'{args[0]}()')
                self.tabs -= 1
                self._line(f'else:')
                self.tabs += 1
                self._line(f'raise EXECUTIONERROR("Unknown point: {args[0]}")')
                self.tabs -= 1
            
            case 'save':
                checklen(1, "==")
                name = args[0]
                self._line(f'with open({name}, "wb") as f:')
                self._line(f'    pickle.dump(MEM, f)')
                
            case 'open':
                checklen(1, "==")
                name = args[0]
                self._line(f'with open({name}, "rb") as f:')
                self._line(f'    content = pickle.load(f)')
                self._line(f'MEM = content')
                
            case 'copy':
                checklen(1, "==")
                spl = args[0].split(':')
                self._line(f'MEM.setdataraw({spl[0]}, {spl[1]}, MEM.getdata())')
                
            case 'move':
                checklen(2, "==")
                self._line(f'MEM.setdatato({args[0]}, MEM.getdata())')
            
            case 'moveto':
                checklen(1, "==")
                self._line(f'MEM.CURSOR = int({args[0]})')
                
            case 'spawn':
                checklen(1, "==")
                point = args[0]
                self._line(f'threading.Thread(target={point}).start()')
                
            case 'error':
                checklen(1, "==")
                name = f'Error{args[0]}'
                self._line(f'class {name}(Exception):pass')
                self._line(f'raise {name}')
                
            case 'jump':
                checklen(1, "==")
                self._line(f'MEM.POINTER = int({args[0]})')
                
            case 'load':
                checklen(1, "==")
                self._line(f'MEM.setdata({args[0]})')
                
            case 'src':
                checklen(1, ">=")
                if not self.safe:
                    self._line(' '.join(args))
                else:
                    raise SyntaxError \
                (f"Unknown syntax: System commands is not available in safemode")
            
            case '>':
                checklen(0, "==")
                self._line('__p = MEM.CURSOR')
                self._line('MEM.CURSOR = __p + 1')
            
            case '<':
                checklen(0, "==")
                self._line('__p = MEM.CURSOR')
                self._line('MEM.CURSOR = __p - 1')
            
            case '+':
                checklen(0, "==")
                self._line(f'__a = MEM.getdata()')
                self._line(f'MEM.setdatato(MEM.POINTER, __a + 1)')
            
            case '-':
                checklen(0, "==")
                self._line(f'__a = MEM.getdata()')
                self._line(f'MEM.setdatato(MEM.POINTER, __a - 1)')
            
            case 'in':
                checklen(0, "==")
                self._line('MEM.setdata(int(input()))')
            
            case 'sum':
                checklen(2, "==")
                reg = args[0]
                name = args[1]
                self._line(f'{name} = MEM.getsum({reg})')
            
            case 'var':
                checklen(2, ">=")
                self._line(f'{args[0]} = {" ".join(args[1:])}')
                
            case 'add':
                checklen(2, "==")
                a = args[0]
                b = args[1]
                operation(a, b, '+')
            
            case 'sub':
                checklen(2, "==")
                a = args[0]
                b = args[1]
                operation(a, b, '-')
                
            case 'mul':
                checklen(2, "==")
                a = args[0]
                b = args[1]
                operation(a, b, '*')
                
            case 'div':
                checklen(2, "==")
                a = args[0]
                b = args[1]
                operation(a, b, '/')
                
            case 'pow':
                checklen(2, "==")
                a = args[0]
                b = args[1]
                operation(a, b, '**')
                
            case 'addreg':
                checklen(2, "==")
                a_spl = args[0].split(':')
                b_spl = args[1].split(':')
                operationreg(a_spl[0], b_spl[0], a_spl[1], b_spl[1], '+')
            
            case 'subreg':
                checklen(2, "==")
                a_spl = args[0].split(':')
                b_spl = args[1].split(':')
                operationreg(a_spl[0], b_spl[0], a_spl[1], b_spl[1], '-')
                
            case 'divreg':
                checklen(2, "==")
                a_spl = args[0].split(':')
                b_spl = args[1].split(':')
                operationreg(a_spl[0], b_spl[0], a_spl[1], b_spl[1], '/')
                
            case 'mullreg':
                checklen(2, "==")
                a_spl = args[0].split(':')
                b_spl = args[1].split(':')
                operationreg(a_spl[0], b_spl[0], a_spl[1], b_spl[1], '*')
                
            case 'powreg':
                checklen(2, "==")
                a_spl = args[0].split(':')
                b_spl = args[1].split(':')
                operationreg(a_spl[0], b_spl[0], a_spl[1], b_spl[1], '**')
                
            case 'switch':
                checklen(1, "==")
                self._line(f'MEM.sethand("{args[0]}")')
                
            case 'new':
                checklen(1, "==")
                self._line(f'MEM.newhand("{args[0]}")')
                
            case 'reg':
                checklen(1, "==")
                self._line(f'MEM._create_reg({args[0]})')
                
            case 'workif':
                checklen(3, "==")
                operator = args[0]
                value = args[1]
                call = args[2]
                self._line(f'if MEM.getdata() {operator} {value}:{call}()')
                
            case 'out.':
                checklen(0, "==")
                self._line('print(MEM.getdata(), end = "")')
                
            case 'outch':
                checklen(0, "==")
                self._line('print(chr(MEM.getdata()), end = "")')
                
            case 'echo':
                self._line(f'print({" ".join(args)}, end = "")')
            
            case 'echoln':
                self._line(f'print({" ".join(args)})')
                
            case '#': self._line(f'# {" ".join(args)}')
            
            case _:
                raise SyntaxError(f"Unknown syntax: {' '.join(line)}")