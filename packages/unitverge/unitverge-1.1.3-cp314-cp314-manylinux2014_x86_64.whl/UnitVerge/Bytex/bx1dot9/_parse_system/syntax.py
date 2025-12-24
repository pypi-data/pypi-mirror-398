class Syntax:
    syntax = {
        
        'COMMENT': r'//.*',
        
        
        # ! DTYPES
        
        'DTYPE': 
        r'\b(int|str|arr)\b',
        
        'KEYWORDS': 
        r'\b(__debug__|__context__)\b',
        
        
        
        # ! DATA
        
        'STRING':
        r'\"[^\"]*\"',
        
        'FLOAT':
        r'\bf\d+\.\d+\b',
        
        'INTEGER':
        r'\b\d+\b',
        
        'NAME':
        r'\_*\w+(\d*\w*\_*)+',
        
        
        
        # ! SYMBOLS
        
        'LPAREN': r'\(',
        'RPAREN': r'\)',
        
        'SYMBOL':
        r'(=|-|+|/|*)\b',
        
        
        
        # ! OTHER
        
        'NONE':
        r'\s*+',
        
        'UNKNOWN':
        r'.*'
        
    }
