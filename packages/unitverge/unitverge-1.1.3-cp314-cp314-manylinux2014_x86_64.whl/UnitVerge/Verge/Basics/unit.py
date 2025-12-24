from ._base import generatable


class _UnitMeta(generatable):
    '''
    Basic Unit metaclass and functions.
    '''

    def __init__(self) -> None:
        super().__init__()
        self._counter = 0

    @property
    def _temp(self) -> int:
        'system'
        # method to get counter
        self._counter += 1
        return self._counter

    @property
    def _unique_name(self):
        'system'
        # method to get auto-id
        return f"__auto_{self._counter}_{id(self)}"

    def condblock(Self, cond_type: str = 'if'):
        '''
        Create condition block.

        Condition types:

        - if
        - elif
        - else
        '''
        if cond_type not in ('if', 'elif', 'else'):
            raise ValueError(f"Invalid condition type [{cond_type}] (can be only if/elif/else)")

        class _cond:
            def __init__(self, condtition: str) -> None:
                '''
                # Condition
                Create condition

                ## Args:
                - condition: str
                '''
                self.localself = Self
                self.cond = condtition
                self.__name = self.localself._temp

            def __enter__(self):
                self.localself.raw(f'stdfunc cond{self.__name} MEM, LANG')
                return self

            def __call__(self, *args: any, **kwds: any) -> 'Unit':
                return self.localself

            def __exit__(self, *args, **kwargs):
                self.localself.raw([
                    f'end',
                    f'var __cond{self.__name} {self.cond}',
                    f'src {cond_type} __cond{self.__name}:',
                    f'$addtabs',
                    f'do cond{self.__name} MEM, LANG',
                    f'$subtabs',
                ])

        return _cond

    @property
    def function(Self):
        '''
        Create function block.
        '''

        class _func:
            def __init__(self, name: str, args: list[str] = [], type: str = 'std') -> None:
                '''
                # Function
                Create function.

                ## Args:
                - name: str - name of function
                - args: list[str] - list of arguments.

                    format can be: ['arg', 'arg: int', 'arg: int = 10']

                - type: str - type of function. Types:

                    - 'std' : default function

                    - 's' : stctic class method

                    - 'cls' : class function (1st argument - self)
                '''
                self.name = name
                self.type = type
                self.args = args
                self.localself = Self

            def __enter__(self):
                self.localself.raw(
                    f'{self.type if self.type != "cls" else ""
                    }func {self.name} {", ".join(self.args)}'
                )
                return self

            def __exit__(self, *args, **kwargs):
                self.localself.raw(f'end')

            def call(self, *args: str, variable_name='result') -> str:
                '''
                Call function and create variable in code with result of function.

                -> str : name of variable
                '''
                self.localself.raw(f'src {variable_name} = {self.name}({", ".join(args)})')
                return variable_name

            def __call__(self, *args: any, **kwds: any) -> 'Unit':
                return self.localself

        return _func

    @property
    def classblock(Self):
        '''
        Create class block.
        '''

        class _class:
            def __init__(self, name: str, extends: str | None = None) -> None:
                '''
                # Class
                Create class.

                ## Args
                - name: str - name of class
                - extends: str - name of metaclass
                '''
                self.meta = extends
                self.name = name
                self.localself = Self

            def __enter__(self):
                self.localself.raw(f'struct {self.name}({self.meta})')
                return self

            def __call__(self, *args: any, **kwds: any) -> 'Unit':
                return self.localself

            def __exit__(self, *args, **kwargs):
                self.localself.raw('endstruct')

        return _class

    @property
    def iterable(Self):
        '''
        Create iterable block.
        '''

        class _iters:
            '''
            # Iterable
            Create block with repeats.

            ## Args:
            - iters: int - repeats count
            '''

            def __init__(self, iters: int = 0) -> None:
                self.iters = int(iters)
                self._id = Self._temp
                self.localself = Self

            def __enter__(self):
                self.localself.raw(f'stdfunc iters{self._id}')
                return self

            def __call__(self, *args: any, **kwds: any) -> 'Unit':
                return self.localself

            def __exit__(self, *args, **kwargs):
                self.localself.raw(f'end')
                self.localself.raw(f'iters iters{self._id} {self.iters}')

        return _iters

    def raw(self, code: list[str] | str):
        '''
        Add raw bytex2-code to context.
        '''
        if isinstance(code, list):
            self._append(code)
        elif isinstance(code, str):
            self._append([code])
        else:
            raise ValueError('Unknown input type')
        return self

    def python(self, code: str):
        '''
        Add raw python to context.
        '''
        if isinstance(code, str):
            code = code.replace('    ', '\\tab|')
        else:
            raise ValueError('Unknown input type')
        self.raw(['python'] + code.split('\n') + ['python'])
        return self

    def start_context(self, name: str):
        'system'
        self.raw(f"stdfunc {name}")
        return self

    def end_context(self):
        'system'
        self.raw('end')
        return self


class _UnitFrontendMeta(_UnitMeta):
    '''
    Unit aliases and simples metaclass.
    '''

    @property
    def ifblock(self):
        'Get if block'
        return self.condblock('if')

    @property
    def elifblock(self):
        'Get elif block'
        return self.condblock('elif')

    @property
    def elseblock(self):
        'Get else block'
        return self.condblock('else')

    def delay_btx(self, time_ms: int = 0):
        'Delay method'
        if not isinstance(time_ms, int):
            raise ValueError(f"Bad input for delay: [{type(time_ms)}{time_ms}], muste be int.")
        self.raw(f'delay {time_ms}')
        return self

    def spawn_btx(self, name: str):
        'Start thread method'
        self.raw(f'spawn {name}')

    def import_py(self, module: str):
        'Import pyhton lib to bytex2 method'
        if not isinstance(module, str):
            raise ValueError(f"Bad input for delay: [{type(module)}{module}], muste be int.")
        self.raw(f'#import {module}')
        return self

    def debug_btx(self):
        'Simple debuger (work only in runtime)'
        self.raw('debug')
        return self

    def callfunc_btx(self, func_name: str, *args: str, return_var: str = 'result'):
        '''
        Call function and create variable in code with result of function.

        -> str : name of variable
        '''
        self.raw(f'src {return_var} = {func_name}({", ".join(args)})')
        return return_var

    def inputint_btx(self, prompt: str = ''):
        'Input integer method'
        self.println(prompt)
        self.raw('in')
        return self

    def var_btx(self, name: str, value):
        'Create variable method'
        self.raw(f"var {name} {value}")
        return self

    def println_btx(self, text, to_repr: bool = False):
        'Println method'
        text = repr(text) if to_repr else text
        self.raw(f"echoln {text}")
        return self

    def print_btx(self, text, to_repr: bool = False):
        'Print method'
        text = repr(text) if to_repr else text
        self.raw(f"echo {text}")
        return self

    def loadto_sec(self, value: int):
        'Load integer to current section method'
        if not isinstance(value, int):
            raise ValueError(f"Bad input to load: [{type(value)}{value}], muste be int.")
        self.raw(f"load {int(value)}")
        return self

    def set_hand(self, handname: str):
        'Set current hand method'
        self.raw(f"switch {handname}")
        return self

    def new_hand(self, handname: str):
        'Create new hand method'
        self.raw(f"new {handname}")
        return self

    def next_reg(self):
        'Jump to next register method'
        self.raw('>')
        return self

    def prev_reg(self):
        'Jump to prev register method'
        self.raw('<')
        return self

    def jumpto_reg(self, regindex: int):
        'Jump to registre method'
        if not isinstance(regindex, int):
            raise ValueError(f"Bad input to jump: [{type(regindex)}{regindex}], muste be int.")
        self.raw(f"moveto {int(regindex)}")
        return self

    def jumpto_sec(self, secindex: int):
        'Jump to section in register method'
        if not isinstance(secindex, int):
            raise ValueError(f"Bad input to jump: [{type(secindex)}{secindex}], muste be int.")
        self.raw(f"jump {int(secindex)}")
        return self

    def operation_sec(self, value: int, operation: str, copyto_regsec: str | None = '0:0'):
        'Do operation and copy value to register'
        # check types
        if not isinstance(value, int):
            raise ValueError(f"Bad input to opertion: [{type(value)}{value}], muste be int.")
        if not isinstance(operation, str):
            raise ValueError(f"Bad input to opertion: [{type(operation)}{operation}], muste be int.")
        if copyto_regsec is not None and not isinstance(copyto_regsec, str):
            raise ValueError(f"Bad input to opertion: [{type(copyto_regsec)}{copyto_regsec}], muste be int.")
        operations = {
            'add': 'add', 'plus': 'add', '+': 'add',
            'sub': 'sub', 'subdivission': 'sub', 'minus': 'sub', '-': 'sub',
            'div': 'div', 'divission': 'div', '/': 'div',
            'mul': 'mul', 'mull': 'mul', 'multyply': 'mul', '*': 'mul',
            'pow': 'pow', 'power': 'pow', '**': 'pow', '^': 'pow',
        }
        raw_op = operation
        operation = operations.get(operation)
        # check operation
        if operation is None:
            raise ValueError(f'Unknown operation: [{raw_op}].')
        if operation == 'add' and value == 1:
            self.raw(['+'])
        if operation == 'sub' and value == 1:
            self.raw(['-'])
        self.raw([
            f"var __currh MEM.hand",
            f"new TEMP",
            f"switch TEMP",
            f"reg -1",
            f"var __currr LANG.register",
            f"moveto -1",
            f"jump 4095",  # jump to last section
            f"load {int(value)}",
            f"jump 0",
            f"{operation} MEM.POINTER 4095",
            f"copy {copyto_regsec}" if copyto_regsec else ''
        ])
        return self

    def save_context(self, name: str):
        'Save current context'
        self.raw(f'save "{name}.btxf"')
        return self

    def open_context(self, name: str):
        'Load to current context'
        self.raw(f"open {name}.btxf")
        return self

    def append_context(self, name: str):
        'Append bytex file to bytex code'
        self.raw(f'#append {name}')
        return self


class Unit(_UnitFrontendMeta):
    '''
    # Unit
    Code context class.

    Contain all code-generation methods.
    '''

    def __init__(self, name: str = 'unk') -> None:
        super().__init__()
        self.plugins = {}
        self.contextname = name

    def __enter__(self):
        self.start_context(self.contextname)
        return self

    def __exit__(self, *args, **kwargs):
        self.end_context()

    def plugin(self, name: str, handler: object):
        '''
        Create your plugin (Method) in unit.
        Handler first argument is [Self] object of Unit, other is user args.
        '''
        if hasattr(self, name):
            raise ValueError(f"Plugin name '{name}' conflicts with built-in method")
        self.plugins[name] = handler
        return self

    def register_plugin(self, name: str):
        'Create your plugin by function and name.'
        def handler(func):
            self.plugin(name, func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return handler

    def compile(self) -> str:
        'Get str-code of unit'
        return self.get_str()

    def __getattr__(self, name):
        try:
            rawattr = self.plugins[name]

            def attr_plugin_handler(*args, **kwargs):
                return rawattr(self, *args, **kwargs)

            return attr_plugin_handler
        except:
            try:
                return self.__getattribute__(name)
            except AttributeError as e:
                raise AttributeError(f"Unknown attrubute '{name}'. \n(Error: {e})")

    def __call__(self, line: str):
        return self.raw(line)