from UnitVerge.Bytex import lang
import time
execute = lang


def prog1():
    print('\n === PROG 1 === \n')
    execute('''
    mem var iters 0;
    mem var k 2;
    point test; 
        p:test work ife 0 set 1;
        p:test op * $k;
        p:test print !;
        p:test out n;
    print Input iterations number:~;
    in num; mem edit iters !; >;
    out n; print $iters; out n;
    work repeat $iters goto test;
    load 10 test data for output;
    print data in 10 from~; print ?; print :~; print %10;
    ''')




def prog2():
    print('\n === PROG 2 === \n')
    execute('''
    # configs and systems;
    point input; p:input jump 1234;
    point basic; p:basic jump 0;
    point temp; p:temp jump 8421;
    
    point main;
        p:main goto temp;
        p:main copy 1235;
        p:main goto input;
        p:main op * >;
        p:main out .;
    # program;
    goto temp; print Input num 1:~; in num; goto basic;
    goto input; print Input num 2:~; in num; goto basic;
    goto main;
    >;
    ''')



def find_letter(string, symbol):
    # fast findin letter
    # example "prod" code architecture
    max = len(string) + 3
    code = f'''
# systems ------;       mem var max {max}; rlim 500; malloc $max; jump 0; mem var split_in -1;
# load input ---;       {'\n'.join([f'set {i}; >;' for i in string])}{f'prev {len(string)};'}
# search block;

point go; 
point find;
point plus;

ps:find;
    mem var temp_pos ?;
    jump {max-1};
    set $split_in;
    work ife -1 mem edit split_in $now;
    jump $temp_pos;
pe:find;

ps:go; 
    mem var now ?;
    load  $max $split_in;
    work ifins {symbol} goto find; 
    >;
pe:go;

# return;
work repeat {len(string)} goto go; set $split_in; return;
'''
    return execute(code)








'''
Main rules of clean Bytex code and best practices 
for code-generation -
- Comentaries
- Code sections
- Optimal realization
- Full setting lang while begin
- Adaptive parameters and arch
Good example - find.
'''

if __name__ == '__main__':
    tests_count = 100
    times_bytex = []
    for i in range(tests_count): 
        time_s = time.time()
        print('iteration: ', i, ', res:', find_letter('1234567890123456789012345678901234567890', str(i)))
        time_e = time.time()
        times_bytex.append(time_e-time_s)
    print('bytex:', sum(times_bytex) / len(times_bytex) )
    times_vanila = []
    for i in range(tests_count): 
        time_s = time.time()
        print(i, '1234567890123456789012345678901234567890'.find(str(i)))
        time_e = time.time()
        times_vanila.append(time_e-time_s)
    print('vanila:', sum(times_vanila) / len(times_vanila) )