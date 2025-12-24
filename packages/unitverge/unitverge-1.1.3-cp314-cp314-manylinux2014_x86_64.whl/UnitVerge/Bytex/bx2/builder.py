from .translator.translator import Translator
from .translator import __version__





def build(code: str):
    translated = '\n'.join(Translator().translate(code))
    return translated




def bin(code: str, fileout: str = 'a.out'):
    built = build(code)
    with open(fileout, 'w') as f:
        f.write(built)
    return built
    

def execute(code: str):
    localscope = locals()
    exec(build(code), localscope, localscope)
    return localscope