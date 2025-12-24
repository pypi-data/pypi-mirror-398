from .Frontend import Frontend, Query


class UnQL:
    def __init__(self, database: str = 'unitdb', format: str = 'undb') -> None:
        self._f = Frontend()
        self.name = f"{database}.{format}"
    
    def request(self, type = 'GET', loc = locals(), **kwargs):
        type = type.lower()
        loc['Query'] = Query
        loc['Frontend'] = Frontend
        def check(length, required: list[str] = ['Not Stated']):
            if len(kwargs.keys()) != length:
                raise ValueError(
                    f'Invalid argument length. Required: {", ".join(required)} ({len(required)}). Got: {len(kwargs.keys())}'
                )
        match type:
            case 'get':
                check(1, ['FROM'])
                RESULT = '_res'
                code = f'''
with Query({repr(self.name)}) as q:
    q.getfrom({repr(kwargs['FROM'])}, out={repr(RESULT)})
{RESULT} = q.scope[{repr(RESULT)}]
                '''
                exec(code, loc, loc)
                return loc[RESULT]
            case 'put':
                check(2, ['TO', 'DATA'])
                code = f'''
with Query({repr(self.name)}) as q:
    q.setto(key = {repr(kwargs['TO'])}, data = {repr(kwargs['DATA'])})
                '''
                exec(code, loc, loc)
                return self
            case 'select':
                check(1, ['WHEN'])
                RESULT = '_result'
                code = f'''
with Query({repr(self.name)}) as q:
    q.select(condition = {repr(kwargs['WHEN'])})
{RESULT} = q.scope[{repr(RESULT)}]
                '''
                exec(code, loc, loc)
                return loc[RESULT]
            case _:
                raise SyntaxError(f'Unknow request type: {type}')
        
    def __call__(self, *args, **kwargs):
        return self.request(*args, **kwargs)

    def __getitem__(self, __i):
        return self.request('GET', FROM=__i)
    
    def __setitem__(self, __i, __o):
        self.request('PUT', TO=__i, DATA=__o)