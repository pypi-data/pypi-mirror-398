class RuntimeError(Exception):
    def __init__(self, error, text = '', line = [], code = []):
        super().__init__(
            (f"\nBYTEX2 Runtime Error:" ) +
            (f"\n{error}" if error else '') +
            (f"\nerr: {text}") +
            (f"\n     line: {" ".join(line)}" if line else '') +
            (f"\n     line: {code.index(line) + 1}" if line else '')
        )
        
class TranslationError(RuntimeError):
    def __init__(self, error = '', text='', line=[], code=[], type: int = 0):
        super().__init__(f'TranslationError: {type}' if error == '' else error, 
                         text, line, code)

class MemoryError(RuntimeError):
    def __init__(self, error = '', text='', line=[], code=[], type: int = 0):
        super().__init__(f'MemoryError: {type}' if error == '' else error, 
                         text, line, code)

class Bytex2Error(RuntimeError):
    def __init__(self, error = '', text='', line=[], code=[], type: int = 0):
        super().__init__(f'Bytex2Error: {type}' if error == '' else error, 
                         text, line, code)


