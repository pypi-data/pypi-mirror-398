from .syntax import Syntax
import re







class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.tokens = []
    
    def tokenize(self):
        while self.pos < len(self.code):
            matched = False
            if re.match(r'\s', self.code[self.pos]):
                self.pos += 1
                continue
            for token_type, pattern in Syntax.syntax.items():
                regex = re.compile(pattern)
                match = regex.match(self.code, self.pos)
                if match:
                    if token_type not in ['COMMENT', 'NONE']:
                        self.tokens.append({
                            'type': token_type,
                            'value': match.group(),
                            'position': self.pos
                        })
                    self.pos = match.end()
                    matched = True
                    break
            if not matched:
                raise SyntaxError(f"Unknown syntax: {self.code[self.pos]}")
        
        return self.tokens
    
    
    

code = '''
int test = 10
'''


print(Lexer(code).tokenize())