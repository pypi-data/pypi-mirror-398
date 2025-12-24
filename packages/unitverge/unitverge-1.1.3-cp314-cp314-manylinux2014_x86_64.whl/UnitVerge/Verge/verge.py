from .Basics._base import UVObj




class Verge:
    '''
    # Verge
    KeyClass for interprete instructions.

    ## Methods:
    - `interprete(instructions)` : interprete list of instructions.
    - `compile` : get verge code.
    - `__call__(instructions)` : interprete list of instructions and get result.
    - `other systems...`

    ## Example:
    >>> v = Verge()
    >>> v.interprete(editor, unit1, unit2)
    >>> final_code = v.compile()
    >>> local = Bytex2().current['ex'](final_code)

    ### or just
    >>> final_code = Verge()(editor, unit1, unit2)
    >>> local = Bytex2().current['ex'](final_code)
    '''
    def __init__(self, **kwargs) -> None:
        self.instruction = {
            'generatable':{'type':'build', 'getcode':'get_code'},
            'builder':{'type':'edit', 'inst_attr':'INSTRUCTIONS'},
        }
        self.type = {
            'build': self.build,
            'edit': self.edit,
        }
        self.code = [] \
            if '__code' not in kwargs.keys() else kwargs['__code'] # for repr
    
    def interprete(self, instructions: list) -> Verge:
        '''
        # Interprete
        interprete list of instructions method
        '''
        if not isinstance(instructions, (list, tuple)):
            raise TypeError(f"instructions must be list, got {type(instructions)}")
        ins: object # just type hint for editor
        for ins in instructions:
            # all instructions must be extends from [instruction] metaclass
            # instruction metaclass has [__repr__] and other methods to confirm this checks
            ins_type = repr(ins)
            if not ins_type.startswith('instruction-'):
                raise ValueError(f'Bad instruction {repr(ins)}')
            try: ins_type = ins.name
            except: raise ValueError(f'Bad instruction {repr(ins)} : has no attribute name.')
            if ins_type in self.instruction.keys():
                # interprete instrucrion
                self.work(ins, ins_type)
            else: 
                raise ValueError(f'Instruction {repr(ins)} ({ins_type}) not in Verge instructions')
        return self
    
    def work(self, instruction: object, typ: str) -> Verge:
        'interprete one instruction method'
        # get instruction type
        _type = self.instruction[typ]['type']
        try: # try get handler for instruction by type
            handler = self.type[_type] 
        except:
            raise ValueError(f'Bad instruction {repr(instruction)} : unknown type {_type} : has no handler.')
        handler(instruction, typ)
        return self

    def build(self, ins: object, typ: str) -> Verge:
        'handler for build-type instructions'
        try: # try to get name of method to get all code
            method = self.instruction[typ]['getcode'] 
        except: raise ValueError(f'Bad instruction {repr(ins)} : has no key getcode with name of attribute.')
        # get attribute for get code
        attr = ins.__getattribute__(method)
        try: # try get code
            code = attr()
        except Exception as e:
            raise ValueError(f'Bad instruction {repr(ins)} : error in handler : {e}')
        if not isinstance(code, list):
            raise ValueError(f'Bad handler : returning type is {type(code)}, but must be list')
        # append code to self.code
        for line in code: self.code.append(line)
        return self
    
    def edit(self, ins: object, typ: str) -> Verge:
        'handler for type '
        try:

            method = self.instruction[typ]['inst_attr']
        except: raise ValueError(f'Bad instruction {repr(ins)} : has no key INSTRUCTIONS with list of instructions.')
        attr = ins.__getattribute__(method)
        if not isinstance(attr, list):
            raise ValueError(f'Bad instruction {repr(ins)} : INSTRUCTIONS must be list, not {type(attr)}.')
        for sub_ins in attr:
            try: sub_ins(self)
            except Exception as e: 
                raise ValueError(f'Bad instruction {repr(sub_ins)} : bad INSTRUCTIONS for Verge : {e}.')
        return self

    def compile(self) -> list[str]:
        '''
        # Compile
        ### -> CODE ( list[str] )
        Get code of Verge. Returns list of str with interpreted code.
        '''
        return self.code
    
    def __call__(self, instructions: list[str]) -> list[str]:
        '''
        # Interprete and get code
        ### -> CODE ( list[str] )
        'UI' for verge. Interprete list of instructions and get code.
        '''
        self.interprete(instructions)
        return self.compile()
    
    def __repr__(self):
        return f'__code = {repr(self.code)}; Verge(__code = __code)'
