from .__vm import *
import sys, gc


class Executor(Machine):
    def __init__(self):
        super().__init__()
        self.points_code = {}
        self.points = []
        self.add_to_point = [False, '']
        self.to_return = None



    def exec(self, command: list):
        cmd = command[0]
        args = command[1:]

        if self.add_to_point[0] and \
        not cmd.startswith('pe:'):
            args = [cmd] + args
            cmd = f'p:{self.add_to_point[1]}'
            print_debug(cmd, args)

        def err_syntax(other = ''):
                raise UnknownSyntax(f"Unknown syntax: {' '.join(command)}. " + str(other))
        def check_args_len(length):
            if len(args) != length:
                err_syntax(
                    f'\nBad arguments length ({len(args)} while must be {length}).'
            )

        print_debug(f'Input - {command}, cmd - {cmd}, args - {args}')

        if cmd.startswith('p:'):
            name = cmd[2:]
            if name in self.points:
                # add to point code from command
                self.points_code[name].append(args)
            else:
                # if name of point is not found
                raise PointError(f'Unknown name to add code to point: {name}')
        elif cmd.startswith('ps:'): # point block start
            name = cmd[3:]
            if name in self.points:
                self.add_to_point[0] = True
                self.add_to_point[1] = name
            else:
                raise PointError(f'Unknown name to start point block: {name}')
        elif cmd.startswith('pe:'): # point block end
            name = cmd[3:]
            if name in self.points:
                self.add_to_point[0] = False
                self.add_to_point[1] = ''
            else:
                raise PointError(f'Unknown name to end point block: {name}')
        else:
            match cmd:
                case 'jump':
                    check_args_len(1)
                    arg = self.compile_path(args[0])
                    self.jump(arg)

                case 'set':
                    check_args_len(1)
                    arg = self.compile_data(args[0])
                    self.set(arg)

                case 'return':
                    self.to_return = self.vm.tape[
                    self.vm.position
                ]

                case 'load':
                    if len(args) < 2:
                        err_syntax(
                        f'\nBad arguments length ({len(args)} while must be 2 and more).'
                    )
                    pos = self.compile_path(args[0])
                    data = self.compile_data(' '.join(args[1:]))
                    pre = self.vm.position
                    self.vm.position = pos
                    self.set(data)
                    self.vm.position = pre


                case '>':
                    self.next()

                case '<':
                    self.prev()

                case 'next':
                    check_args_len(1)
                    arg = self.compile_data(args[0])
                    self.next(arg)

                case 'prev':
                    check_args_len(1)
                    arg = self.compile_data(args[0])
                    self.prev(arg)

                case 'out':
                    check_args_len(1)
                    arg = args[0]
                    if arg in ('.', 'data', 'd'):
                        self.out()
                    elif arg in ('next', 'n'):
                        self.otn()
                    elif arg in ('char', 'c'):
                        self.otc()
                    elif arg in ('type', 't'):
                        self.ott()
                    elif arg in ('pos', 'p', '?'):
                        self.otp()
                    else:
                        err_syntax(f'Unknown out type: {arg}.')

                case 'op': # operation
                    check_args_len(2)
                    arg = args[0]
                    x = self.compile_data(args[1])
                    if arg in ('plus'):
                        self.plus(x)
                    elif arg in ('+'):
                        self.plus_int(x)
                    elif arg in ('-'):
                        self.sub(x)
                    elif arg in ('/'):
                        self.div(x)
                    elif arg in ('*'):
                        self.mul(x)
                    elif arg in ('^'):
                        self.pow(x)
                    else:
                        err_syntax(f'Unknown op type: {arg}.')

                case 'work':
                    self.workparser(args)

                case 'malloc':
                    check_args_len(1)
                    self.vm.recreate(
                        int(self.compile_data(args[0]))
                    )

                case 'rlim':
                    check_args_len(1)
                    sys.setrecursionlimit(
                        int(self.compile_data(args[0]))
                    )

                case 'in':
                    check_args_len(1)
                    arg = args[0]
                    if arg in ('str', 's'):
                        self.instr()
                    elif arg in ('int', 'i'):
                        self.inint()
                    elif arg in ('num', 'n'):
                        self.innum()
                    else:
                        err_syntax(f'Unknown input type: {arg}.')

                case 'print':
                    arg = self.compile_data(
                        ' '.join(args)
                    )
                    self.print(arg)

                case 'point': # declarate point
                    name = args[0]
                    self.points.append(name)
                    self.points_code[name] = [['#', 'start']]

                case 'goto': # use point
                    name = self.compile_data(args[0])
                    if name in self.points_code.keys():
                        for linelocal in self.points_code[name]:
                            self.exec(linelocal)
                    else:
                        raise PointError(f'Unknown name for go to point: {name}')

                case 'copy':
                    check_args_len(1)
                    arg = self.compile_path(args[0])
                    self.copy(arg)

                case 'swap':
                    check_args_len(1)
                    arg = self.compile_path(args[0])
                    self.swap(arg)

                case 'mem':
                    arg = args[0]
                    if arg == 'var':
                        check_args_len(3)
                        self.new_var(args[1], args[2])
                    elif arg == 'const':
                        check_args_len(3)
                        self.new_var(args[1], args[2], 'const')
                    elif arg == 'edit':
                        check_args_len(3)
                        self.set_var(args[1], args[2])
                    elif arg == 'temp':
                        self.temp_use(args[1], args[2:])
                    else:
                        err_syntax(f'Unknown mem arg: {arg}.')

                case '#':
                    pass

                case 'dlall': # delete all
                    gc.collect(0)
                    gc.collect(1)
                    gc.collect(2)

                case 'del': # delete trash
                    arg = args[0]
                    match arg:
                        case 'collect':
                            typ = args[1]
                            if typ == 'all':
                                gc.collect(0)
                                gc.collect(1)
                                gc.collect(2)
                            elif typ == 'trash':
                                gc.collect(2)
                            else:
                                gc.collect(
                                    int(self.compile_int(typ))
                                )
                        case 'off':
                            gc.disable()
                        case 'on':
                            gc.enable()
                        case _: err_syntax(f'Unknown del arg: {arg}.')

                case _:
                    if str(cmd).strip() != '':
                        err_syntax()
        return self



    def work_ife(self, condition, command: list): # work if equal
        condition = self.compile_data(condition)
        if self.vm.get() == condition:
            self.exec(command)

    def work_ifin(self, condition, command: list): # work if in
        condition = self.compile_data(condition)
        if self.vm.get() in condition:
            self.exec(command)

    def work_ifins(self, condition, command: list): # work if in (string version)
        condition = self.compile_data(condition)
        if str(self.vm.get()) in str(condition):
            self.exec(command)

    def work_ifne(self, condition, command: list): # work if not equal
        condition = self.compile_data(condition)
        if self.vm.get() == condition:
            return
        self.exec(command)

    def work_ifm(self, condition, command: list): # work if more
        condition = self.compile_data(condition)
        if self.vm.get() > condition:
            self.exec(command)

    def work_ifl(self, condition, command: list): # work if less
        condition = self.compile_data(condition)
        if self.vm.get() < condition:
            self.exec(command)

    def work_ifme(self, condition, command: list): # work if more or equal
        condition = self.compile_data(condition)
        if self.vm.get() >= condition:
            self.exec(command)

    def work_ifle(self, condition, command: list): # work if less or equal
        condition = self.compile_data(condition)
        if self.vm.get() <= condition:
            self.exec(command)

    def temp_use(self, var, command: list):
        var_name = self.compile_data(var)
        pos = self.vm.position
        self.jump(0)
        self.set(self.get_from_var(var_name)['val'])
        self.exec(command)
        self.jump(pos)

    def workparser(self, args):
        arg = args[0]

        if arg == 'ife':
            self.work_ife(args[1], args[2:])
        elif arg == 'ifin':
            self.work_ifin(args[1], args[2:])
        elif arg == 'ifins':
            self.work_ifins(args[1], args[2:])
        elif arg == 'ifne':
            self.work_ifne(args[1], args[2:])
        elif arg == 'ifl':
            self.work_ifl(args[1], args[2:])
        elif arg == 'ifm':
            self.work_ifm(args[1], args[2:])
        elif arg == 'ifme':
            self.work_ifme(args[1], args[2:])
        elif arg == 'ifle':
            self.work_ifle(args[1], args[2:])

        elif arg == 'whlne': # while not equal
            args[1] = self.compile_data(args[1])
            while self.vm.get() != args[1]:
                self.exec(args[2:])
        elif arg == 'whle': # while equal
            args[1] = self.compile_data(args[1])
            while self.vm.get() == args[1]:
                self.exec(args[2:])
        elif arg == 'whlm': # while more
            args[1] = self.compile_data(args[1])
            while self.vm.get() > args[1]:
                self.exec(args[2:])
        elif arg == 'whlnme': # while more or equal
            args[1] = self.compile_data(args[1])
            while self.vm.get() >= args[1]:
                self.exec(args[2:])
        elif arg == 'whll': # while less
            args[1] = self.compile_data(args[1])
            while self.vm.get() < args[1]:
                self.exec(args[2:])
        elif arg == 'whlle': # while less or equal
            args[1] = self.compile_data(args[1])
            while self.vm.get() <= args[1]:
                self.exec(args[2:])

        elif arg == 'repeat':
            iterations = int(
                self.compile_data(args[1])
            )
            for _ in range(iterations):
                self.exec(args[2:])
        else:
            raise UnknownSyntax(f'Unknown work type: {arg}.')