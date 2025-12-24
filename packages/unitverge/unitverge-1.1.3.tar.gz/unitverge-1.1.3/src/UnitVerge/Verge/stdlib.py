class Standarts:
    '''
    # Standarts
    Get standart functions and code templates.
    '''
    _ = ''
    def simpleparser(self) -> str:
        '''
        get code of bytex2 parser and splitter
        '''
        code = """
def parse(code: str) -> list[list[str]]:
    '''
    # Parser
    Simple Bytex2 code splitter and parser.
    '''
    code = code.replace(';', '\n')
    commands = []
    for i in code.split('\n'):
        command = []
        i = i.strip()
        for j in i.split(' '):
            command.append(j)
        if command != ['']:
            commands.append(command)
    return commands
        """
        return code