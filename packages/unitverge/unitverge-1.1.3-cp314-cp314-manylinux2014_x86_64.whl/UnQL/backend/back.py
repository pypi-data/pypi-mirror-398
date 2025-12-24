from UnitVerge import *



class Generator:
    def __init__(self) -> None:
        self.unit = Unit()
        self.unit.new_point('pre')
        self.unit.new_point('post')
        self.unit.pipeline(['pre', 'main', 'post'])
        self.btx = Bytex().translator()
    
    def goto(self, name):
        self.unit.set_point(name)
    
    def __call__(self, line: str) -> Unit:
        return self.unit(line)
    
    def py(self, line: str):
        self.unit.python(line)
    
    def build(self):
        verge = Verge()
        verge.interprete([self.unit])
        return self.btx.translate('\n'.join(verge.compile()))