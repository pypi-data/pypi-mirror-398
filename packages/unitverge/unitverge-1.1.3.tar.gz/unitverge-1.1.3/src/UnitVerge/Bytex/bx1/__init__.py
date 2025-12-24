'''
# UnitBytex language

System assembler-like language for UnitVerge framework programms.

Executing in Vurtual machine.

By pt.

## Bytex 1.0
'''



__version__ = '1.0'

from ._lang import execute, Executor

def lang():
    return {
        'bu': lambda *args, **kwrgs: None, 
        'bi': bin,
        'ex': execute,
        'tr': lambda *args, **kwrgs: None
    }