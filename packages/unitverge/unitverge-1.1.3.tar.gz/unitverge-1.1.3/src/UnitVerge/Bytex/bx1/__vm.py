from untvgdev.core.bx1.UnitBytexCore import (
    OutputError, 
    MemorySystemError, 
    PointError, 
    UnknownSyntax,
    VirtualMachineBasics
)


from untvgdev.core.bx1.UnitBytexDevConfig import (
    Debug
)



debugmode = Debug.executor
def print_debug(*data):
    if debugmode: print('debug:', *data)










class VirtualMachine:
    def __init__(self):
        self.vm = VirtualMachineBasics()
    
    def compile_type(self, data):
        data = str(data).replace('~', ' ').replace('``', '~')
        if data.isdigit():
            return int(data)
        try:
            return float(data)
        except ValueError:
            return data

    def compile_int(self, integer):
        inp = float(str(integer)
                  .replace(
                      '?', str(self.vm.position)
                      )
                  .replace(
                      '<', str(self.vm.tape[max(0, self.vm.position-1)])
                      )
                  .replace(
                      '>', str(self.vm.tape[self.vm.position+1])
                    )
                  .replace(
                      '!', str(self.vm.get())
                      ))
        return inp
    
    def jump(self, pos):
        pos = int(pos)
        self.vm.jump(pos)
    
    def set(self, data):
        data = self.compile_type(data)
        self.vm.set(data)
    
    def next(self, iters: int = 1):
        iters = int(iters)
        for i in range(iters):
            self.vm.next()
    
    def prev(self, iters: int = 1):
        iters = int(iters)
        for i in range(iters):
            self.vm.prev()

    def out(self): # out 
        print(self.vm.get(), end='')
    
    def otn(self): # out next
        print('\n', end = '')
    
    def otc(self): # out char
        try: print(
            chr(int(self.vm.get())), 
            end=''
        )
        except TypeError:
            OutputError(f'Invalid data of section to out char: {self.vm.get()}.')
    
    def ott(self): # out type now
        print(type(self.vm.get()), end='')
        
    def otp(self): # out current position
        print(self.vm.position, end='')
    
    def print(self, data):
        print(
            self.compile_type(data), 
            end=''
        )
    
    def instr(self): # input string
        data = input()
        try: 
            data = str(data)
            self.vm.set(data)
        except TypeError:
            OutputError(f'Invalid for input: {data} - type must be str.')
    
    def inint(self): # input integer
        data = input()
        try: 
            data = int(data)
            self.vm.set(data)
        except TypeError:
            OutputError(f'Invalid for input: {data} - type must be int.')
        
    def innum(self): # input any numeric data
        data = input()
        try: 
            data = float(data)
            self.vm.set(data)
        except TypeError:
            OutputError(f'Invalid for input: {data} - type must be number.')
    
    def plus(self, x): # plus any data
        self.vm.tape[
                self.vm.position
        ] += self.compile_type(x)
    
    def plus_int(self, x):
        self.vm.tape[
                self.vm.position
        ] += self.compile_int(x)

    def sub(self, x):
        self.vm.tape[
                self.vm.position
        ] -= self.compile_int(x)
    
    def div(self, x):
        self.vm.tape[
                self.vm.position
        ] /= self.compile_int(x)
    
    def mul(self, x):
        self.vm.tape[
                self.vm.position
        ] *= self.compile_int(x)
    
    def pow(self, x):
        self.vm.tape[
                self.vm.position
        ] **= self.compile_int(x)

     


























class Machine(VirtualMachine):
    def __init__(self):
        super().__init__()
        self.variables = {}   
    
    def new_var(self, name, value, type: str = 'basic'):
        value = self.compile_data(value)
        self.variables[name] = {'val': value, 'typ': type}
        
    def get_from_var(self, name):
        if name in self.variables:
            return self.variables[name]
        else:
            raise MemorySystemError(
        f"Variable '{name}' is not found."
            )

    def set_var(self, name, value):
        value = self.compile_data(value)
        if name in self.variables:
            var = self.variables[name]
            if var['typ'] != 'const':
                self.variables[name]['val'] = value
            else:
                raise MemorySystemError(
        f"Variable '{name}' is not muttable."
            )
        else:
            raise MemorySystemError(
        f"Variable '{name}' is not found."
            )

    def compile_data(self, data):
        data = str(data)
        if data.startswith('$'):
            if data[1:] in self.variables:
                return self.variables[data[1:]]['val']
        elif data.startswith('%'):
            data = self.compile_path(data[1:])
            if isinstance(data, int) and \
            data in range(len(self.vm.tape)):
                return self.vm.tape[data]
        elif data == '!':
            return self.vm.get()
        elif data == '?':
            return self.vm.position
        elif data == '<':
            return self.vm.tape[self.vm.position-1]
        elif data == '>':
            return self.vm.tape[self.vm.position+1]
        return self.compile_type(data)

    def compile_path(self, data):
        data = str(data)
        if data.startswith('$'):
            if data[1:] in self.variables:
                return self.variables[data[1:]]['val']
        elif data == '!':
            return self.vm.get()
        elif data == '?':
            return self.vm.position
        elif data == '<':
            return self.vm.position-1
        elif data == '>':
            return self.vm.position+1
        return self.compile_type(data)
    
    def swap(self, pos):
        pos = self.compile_data(pos)
        curr = self.vm.get()
        oth = self.vm.tape[pos]
        self.vm.set(oth)
        self.vm.tape[pos] = curr
    
    def copy(self, pos):
        pos = self.compile_data(pos)
        curr = self.vm.get()
        self.vm.tape[pos] = curr


























