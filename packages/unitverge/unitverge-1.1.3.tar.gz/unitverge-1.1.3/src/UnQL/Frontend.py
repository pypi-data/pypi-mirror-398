from .backend.back import Generator

class Frontend:
    def __init__(self) -> None:
        self.gen = Generator()
    
    def query(self, line: str):
        self.gen.py(line)
        return self.gen.build()

    def load(self, name: str):
        self.query(f'MEM2.load({repr(name)})')
        return self
    
    def save(self, name: str):
        self.query(f'MEM2.save({repr(name)})')
        return self
    
    def clear(self):
        self.query(f"MEM2.clear()")
        return self
    
    def setto(self, key, data, repricate = True):
        self.query(
            f"MEM2.setto(key = {repr(key)}, data = {repr(data) if repricate else data})"
        )
        return self
    
    def getfrom(self, key, out = 'res'):
        self.query(f"{out} = MEM2.getfrom({repr(key)})")
        return self
    
    def select(self, condition: str, ):
        code = f'''
result = {{}}
try:
    for key in MEM2.keys():
        value = MEM2.getfrom(key)
        if {condition.replace('$', 'value')}:
            result[key] = value
except IndexError as e:
    print(f'\\nSelect Error:\\n{{e}}')
        '''
        self.query(code)
        return self
    
    def exec(self):
        lclscp = locals() # localscope
        exec('\n'.join(self.gen.build()), lclscp, lclscp)
        return lclscp





class Query(Frontend):
    def __init__(self, database: str) -> None:
        super().__init__()
        self.db = database
        self.scope = {}
    def __enter__(self):
        self.load(self.db)
        return self
    def __exit__(self, *args, **kwars):
        self.save(self.db)
        self.scope = self.exec()


def NewDB(name: str):
    Frontend().save(name).exec()