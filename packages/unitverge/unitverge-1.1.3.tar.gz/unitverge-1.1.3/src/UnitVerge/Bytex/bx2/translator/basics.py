from . import __version__
import time

core = f'''

class Memory:...



import threading
import pickle
import time
import abc
from UnitVerge.Bytex.bx2.BYTEX2_back import Memory, Memory2


class VMEXCEPTION(Exception): pass
class EXECUTIONERROR(Exception): pass



try: from numba import jit
except:
    def jit(*args, **kwargs):
        def wrap(func):
            return func
        return wrap
    



# METADATA
meta = """
date: {time.time()}
version = {__version__}
development by pt, 2025
"""


points = []
libs = []
ver = {__version__}
_is_lib = False
MEM = Memory()
MEM2 = Memory2()



class language:
    _ = 0
    @property
    def register(self):
        return MEM.CURSOR
    @property
    def section(self):
        return MEM.POINTER
    @property
    def getdata(self):
        return MEM.getdata()
    @property
    def nextreg(self):
        return MEM.CURSOR + 1
    @property
    def prevreg(self):
        return MEM.CURSOR - 1
    @property
    def nextsec(self):
        return MEM.POINTER + 1
    @property
    def prevsec(self):
        return MEM.POINTER - 1
    def haslib(self, name: str):
        return name in libs
    def getp(self, index: int):
        return MEM.getfrom_p(int(index))
    def setp(self, index: int, data):
        return MEM.setto_p(int(index), data)

LANG = language()

'''.split('\n')