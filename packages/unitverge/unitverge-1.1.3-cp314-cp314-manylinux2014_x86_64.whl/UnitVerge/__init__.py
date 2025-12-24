'''
# UnitVerge Framework
'''

__version__ = '0.9.5'

'UV - UNITVERGE'
from .Verge import Verge as Verge
from .Verge.Basics.syntax import SForm as SForm
from .Verge import UVObj
from .Verge import Unit as Unit





class Bytex:
    '''
    # Bytex lang content.
    ## Methods:
    - `get()` -> `dict[str, object]` : get `_current` (from parameter ver) version lang 
    - `current` -> `dict[str, type]` : get bytex2 lang version
    - `exec_main(code, main_method)` : `dict[object, Any]` : execute code by method
    - `translator()` -> `type[Translator]` : get language translator (bytex2)
    '''
    _current = '2.0'
    def get(self):
        'get lang with _current parameter version'
        from .Bytex import get_from_ver
        return get_from_ver(self._current)()
    @property
    def current(self) -> dict[str, type[any]]:
        'get bytex2 lang version'
        from .Bytex.bx2 import lang
        return lang()
    def exec_main(
        self, 
        code: list [str] | str, 
        main_method: str = 'main'
    ) -> dict[str, any]:
        'execute bytex code with main method'
        if isinstance(code, list): code = '\n'.join(code)
        code += f'\ndo {main_method}'
        return self.current['ex'](code)
    @property
    def translator(self):
        'get bytex2 translator'
        from .Bytex.bx2 import Translator
        return Translator




def compile(VergeObject: Verge.Verge) -> dict[str, object]:
    '''
    # Compile and run code
    Compile and run code (bytex2) from Verge and get locals.
    '''
    # get code from verge
    code = '\n'.join(VergeObject.compile())
    # execute btx2 code and get localscope
    locals = Bytex().current['ex'](code)
    # return localscope
    return locals
