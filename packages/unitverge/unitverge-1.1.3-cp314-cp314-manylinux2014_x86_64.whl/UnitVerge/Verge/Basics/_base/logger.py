import time


class Logger:
    '''
    # Simple logger
    Simple logger for code generation in Unit.

    Methods:
    - format (text: str, status: str) -> str

        : Format text to log
    
    - log (text: str, status: str) -> None
    
        : Orint formatted log
    '''
    def __init__(self):
        self.logs = []

    def format(self, text: str = 'empty', status: str = 'MESSAGE') -> str:
        return (f'LOG: [{time.time()}] : [{status}] : [{text}]')
    
    def log(self, text: str, status: str = 'MESSAGE') -> None:
        text = self.format(text, status)
        self.logs.append(text)
        print(text)