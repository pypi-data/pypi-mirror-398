from .builder import build, bin, execute, __version__, Translator

def lang():
    return {
        'bu': build, 
        'bi': bin,
        'ex': execute,
        'tr': Translator
    }