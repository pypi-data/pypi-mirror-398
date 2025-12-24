'''
# ByteX

UnitBytex language.

System assembler-like language for UnitVerge framework programms.

Executing in Vurtual machine.

By pt.

'''

__version__ = '2.0'


def get_from_ver(__version__: str = '2.0'):
    if __version__ == '1.0':
        from .bx1 import lang
    elif __version__ == '2.0':
        from .bx2 import lang
    else: 
        print(f'ByteX {__version__} not allwoed now. Exiting...')
        exit()
    return lang

lang = get_from_ver('2.0')