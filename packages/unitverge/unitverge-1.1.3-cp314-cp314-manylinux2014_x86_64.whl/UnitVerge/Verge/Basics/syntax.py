class SForm:
    '''
    # Syntax Formater
    Simple formater values and others for bytex.
    '''
    def text(value: str) -> str:
        '''
        ### Simple text format

        Only for simplify code read (returning repr value)
        '''
        return str(repr(value))
    
    def value(value):
        '''
        ### Simple value format

        Only for simplify code read (returning raw value)
        '''
        return value