import re
import sys
from typing import Any
from .exceptions import PipelineError
from .logger import Logger


class instruction:
    '''
    # Framework instruction metaclass 
    For your Verge-instructions. Only system methods for Verge.
    '''
    def __init__(self, name: str) -> None:
        self.name = str(name)
    def __repr__(self):
        return f'instruction-{self.name}'







class generatable(instruction):
    '''
    # Framework generate metaclass-instruction
    Metclass for code-generators.

    Methods:

    - new_point (name: str) -> None

        : Method for create code point

    - set_point (name: str) -> None

        : Method for set current point for generation code
    
    - pipeline (pipeline: list[str]) -> None

        : Set pipeline for get code
    
    - get_code () -> list[str]

        : Get full code builded by pipeline
    
    - get_str () -> str

        : Get full str code builded by pipeline

    - _append (code: list[str]) -> None
        
        : Method for append code for current point

    - _log(text: str, status: str) -> None

        : Method for add log
    '''
    def __init__(self) -> None:
        super().__init__('generatable')
        self.POINTS: dict[str, dict[str, list[str]]] = {
            'main': {'code': [], 'logs': []}
        }
        self.BUILDCONF: dict[str, list | dict] = {'pipeline': []}
        self.TEMP: dict[str, Any] = {'POINT': 'main', 'LOGGER': Logger()}
    
    def _log(self, text: str, status: str = 'MESSAGE'):
        log = self.TEMP['LOGGER'].format(text, status)
        self.POINTS[self.TEMP['POINT']]['logs'].append(log)
    
    def new_point(self, name: str) -> None:
        self.POINTS[name] = {'code': [], 'logs': []}
        self._log(f'created point {name}')
    
    def set_point(self, name: str) -> None:
        if name not in self.POINTS:
            raise KeyError(f"Point '{name}' doesn't exist")
        self.TEMP['POINT'] = name
        self._log(f'switched to point {name}')
    
    def _append(self, code: list[str]) -> None:
        self.POINTS[self.TEMP['POINT']]['code'].extend(code)
    
    def pipeline(self, pipeline: list[str]) -> None:
        self.BUILDCONF['pipeline'] = pipeline
        self._log(f'created pipeline {pipeline}')
    
    def get_code(self) -> list[str]:
        if not self.BUILDCONF['pipeline']:
            return ""
        
        ppl = self.BUILDCONF['pipeline']
        code_lines = []

        for point in ppl:
            if point not in self.POINTS:
                raise PipelineError(f'Unknown pipeline node: {point} (all: {self.POINTS})')
            code_lines.extend(self.POINTS[point]['code'])
        
        self._log(f'get code')
        
        return code_lines
    
    def get_str(self) -> str:
        return '\n'.join(self.get_code())









class builder(instruction):
    '''
    # Framework build metaclass-instruction
    Metclass for commands and instructions for Verge.

    Methods:
    - instruction (ins: object) -> None : add instruction
    '''

    def __init__(self) -> None:
        super().__init__('builder')
        self.INSTRUCTIONS: list[Any] = []
        self.name = 'generatable'

    def instruction(self, ins: object) -> None: 
        self.INSTRUCTIONS.append(ins)







def UVObj(obj_type: str = 'generatable'):
    '''
    # Basic metaclasses of framework

    Get basic unitverge metaclass.

    Types:
    - generatable: basic context metaclass
    - builder: basic instructions orchestrator
    - instruction: basic metaclass for Verge instructions
    '''
    if obj_type == 'generatable':
        return generatable
    elif obj_type == 'builder':
        return builder
    elif obj_type == 'instruction':
        return instruction
    else:
        raise ValueError(f'Unknown UVObj type: {obj_type}.')