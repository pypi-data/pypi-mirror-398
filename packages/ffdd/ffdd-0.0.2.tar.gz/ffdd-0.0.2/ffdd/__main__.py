#!/usr/bin/env python3

'list Files or Directories - an alternative to ls find tree du grep wc nl ...'

from .__init__ import *
from .__init__ import __version__ as VERSION, __doc__ as DESCRIPTION
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from collections import defaultdict
from fnmatch import fnmatch
from grp import getgrgid
from libyare import *
from os import walk, lstat, readlink, popen
from os.path import abspath, expanduser, dirname, isfile, islink, isdir, split as splitpath, join as joinpath, splitext
from pwd import getpwuid
from stat import filemode
from sys import exit, argv, stdin, stderr
from time import localtime

class arg:
    'arguments'
    pass

class var:
    'other global variables'
    num_warning = 0

class Str(str):
    'enhanced str class'
    __truediv__ = yarecsmatch # add '/' to str operators as YARE case-sensitive match operator
    __floordiv__ = yarecimatch # add '//' to str operators as YARE case-insensitive match operator
    __matmul__ = yarecmmatch # add '@' to str operators as YARE case-multiple match operator

K, M, G, T, P, E, Z, Y = [1024 ** j for j in range(1, 9)] # byte multipliers
j2c = letters = 'ablugshtmnocwxyzdefpqr' # column count -> column character
integers = frozenset('ialsmnocwxy') # int attributes
strings = frozenset(letters) - integers # str attributes
c2j = {char: j for j, char in enumerate(j2c)} | {char: j for j, char in enumerate(j2c.upper())} # column character -> column count
ja, jb, jl, ju, jg, js, jh, jt, jm, jn, jo, jc, jw, jx, jy, jz, jd, je, jf, jp, jq, jr = range(22) # j{c} == c2j[c]
eval_globals = {'__builtins__': None}
default = '__default__'
LETTERS = letters.upper()
center_char = '-'
w_default = '3'
w_domain = '0123'
u_default = '6'
u_domain = '56789'
I_default = './*'
I_stdin = '-'
F_domain = D_domain = letters + 'KMGTPEZY'
F_default = D_default = 'True'
S_domain = letters + LETTERS
f_mode_S_default = 'df'
d_mode_S_default = 'd'
W_domain = 'i' + letters + 'I' + LETTERS
W_domain_pct = W_domain + '%'
f_mode_W_default = 'IblugShtmnopqr'
d_mode_W_default = 'IblugShtmnod'
L_default = ''
j_domain = k_domain = '0123456789'
j_default = k_default = '0'

def ancestors(path):
    "yield '/', ..., grandparent and parent directories of path"
    if path != '/':
        yield '/'
        items = [item for item in path.split('/') if item]
        for m in range(1, len(items)):
            yield '/' + '/'.join(items[:m]) + '/'

def chars(pattern):
    return ''.join(chr(j) for j in range(ord(min(pattern)), ord(max(pattern)) + 1) if fnmatchcase(chr(j), pattern))

def compact(W_format):
    """compact -O, see expand()
>>> compact('%i %b %l %o %g %s %u %t %n %m %p %q %r')
'iblogsutmnpqr'"""
    return ''.join(char for jchar, char in enumerate(W_format) if jchar > 0 and W_format[jchar - 1] == '%') if '%' in W_format else W_format

def delquoted(string, quotes='"'"'"):
    'delete quoted substrings from string'
    status = result = ''
    for char in string:
        if not status:
            if char in quotes: status = char
            else: result += char
        elif char == status:
            status = ''
    return result

def double(string, char='%'):
    "double chars into string (char='%' for ArgumentParser() arguments)"
    return string.replace(char, char + char)

def drop(string, forbidden, allowed=''):
    'drop forbidden characters from string'
    return ''.join(allowed if char in forbidden else char for char in string)

def edit(item, char, length=0):
    'convert int/str attribute into str field'
    if char.lower() in integers:
        return f'{item:{length},d}' if char.isupper() else f'{item:{length}d}'
    else: # char.lower() in strings
        return f'{repr(item):{length}}' if char.isupper() else f'{item:{length}}' 

def error(message):
    'print message on stderr and exit'
    exit('ffdd: ERROR: ' + explain(message))

def expand(W_format):
    """expand -O, see compact()
>>> expand('iblogsutmnpqr')
'%i %b %l %o %g %s %u %t %n %m %p %q %r'"""
    return ' '.join('%' + char for char in W_format) if '%' not in W_format else W_format

def explain(message):
    'convert message into readable string'
    return upper_1st(shrink(str(message)))

def local_file(pathfile):
    'return absolute path of a package pathfile'
    return joinpath(dirname(__file__), pathfile)

def longpath(path):
    "expand '~' and return absolute path"
    return abspath(expanduser(path))

def nesting(path):
    "nesting('/') -> 0, nesting('/home/') -> 1, nesting('/home/user/') -> 2, ..."
    return path.count('/') - 1

def parent(path):
    'return parent directory of path'
    return None if path == '/' else '/' if path.count('/') == 2 else '/' + '/'.join([p for p in path.split('/') if p][:-1]) + '/'

def shell(command):
    'execute command and return its stdout as a list of lines'
    return [line.rstrip() for line in popen(command)]

def shrink(string):
    '''drop initial multiple and final blanks from string
>>> shrink('   aaa   bbb   ccc   '
'aaa bbb ccc' '''
    return ' '.join(string.split())

def show(chars):
    return repr(''.join(chars))

def slash(path):
    "terminate by sep ('/' or '\') a directory path"
    return path + (not path.endswith(sep)) * sep

def take(string, allowed, forbidden=''):
    'take allowed characters from string'
    return ''.join(char if char in allowed else forbidden for char in string)

def upper_1st(string):
    'capitalize first character of string'
    return '' if not string else string[0].upper() + string[1:]

def warning(message):
    'if -v: print warning message on stderr and continue'
    if arg.verbose:
        var.num_warning += 1
        print(f'ffdd: WARNING {var.num_warning}: ' + explain(message), file=stderr)

def YmdHMS(time):
    "convert time as seconds since epoch into 'YYYY-mm-dd HH:MM:SS' format"
    return '%04d-%02d-%02d %02d:%02d:%02d' % tuple(localtime(time)[:6])

def ffdd():

    #--------- 2nd level functions ---------

    def eval_expr(arg_short, arg_expr, rec):
        'evaluate boolean Python expression on file or dir record'
        a, b, l, u, g, s, h, t, m, n, o, c, w, x, y, z, d, e, f, p, q, r = rec
        eval_locals = {'a': a, 'b': Str(b), 'l': l, 'u': Str(u),
            'g': Str(g), 's': s, 'h': Str(h), 't': Str(t),
            'm': m, 'n': n, 'o': o, 'c': c, 'w': w, 'x': x, 'y': y, 'z': Str(z),
            'd': Str(d), 'e': Str(e), 'f': Str(f), 'p': Str(p), 'q': Str(q), 'r': Str(r),
            'K': K, 'M': M, 'G': G, 'T': T, 'P': P, 'E': E, 'Z': Z, 'Y': Y}
        try:
            return eval(arg_expr, eval_globals, eval_locals)
        except Exception as exception:
            error(f'{explain(exception)} in {arg_short} {arg_expr!r}')

    def fill_width_from_recs(recs):
        wi = len(edit(len(recs), 'i'))
        wI = len(edit(len(recs), 'I'))
        var.width = {'i': wi, 'I': wI, 'h': var.human_width, 'H': var.human_width + 2, 'b': 10, 'B': 12, 't': 19, 'T': 21}
        if arg.dirs_mode: var.width |= {char: 1 + char.isupper() for char in 'fFeEqQ'}
        for char in compact(arg.output_format):
            if char not in var.width:
                j = c2j[char]
                var.width[char] = max(1, max(len(edit(rec[j], char)) for rec in recs))

    def fill_width_from_rec(i, rec):
        wi = len(edit(i, 'i'))
        wI = len(edit(i, 'I'))
        var.width = {'i': wi, 'I': wI, 'h': var.human_width, 'H': var.human_width + 2, 'b': 10, 'B': 12, 't': 19, 'T': 21}
        for char in compact(arg.output_format):
            if char not in var.width:
                var.width[char] = max(1, len(edit(rec[c2j[char]], char)))

    def print_names_line():
        line = ''
        pct = False
        for char in arg.output_format:
            if char == '%':
                pct = True
            elif pct:
                line += char.center(var.width[char], center_char)
                pct = False
            else:
                line += ' '
        print(line.rstrip())

    def print_rec_line(irec, rec):
        'rec can be var.files[irec-1] or var.dirs[irec-1]'
        line = ''
        pct = False
        for char in arg.output_format:
            if char == '%':
                pct = True
            elif pct:
                if char == '%':
                    line += '%'
                elif char in 'iI':
                    line += edit(irec, char, var.width[char])
                else:
                    line += edit(rec[c2j[char]], char, var.width[char])
                pct = False
            else:
                line += char
        print(line.rstrip())

    #--------- 1st level functions ---------

    def get_arguments():
        parser = ArgumentParser(prog='ffdd', formatter_class=RawDescriptionHelpFormatter, description=DESCRIPTION)
##        parser.add_argument('-H','--browse-manual', action='store_true',
##            help='browse the PDF FFDD User Manual and exit')
        parser.add_argument('-V','--version', action='version', version=f'ffdd {VERSION}')
        parser.add_argument('-v','--verbose', action='store_true',
            help='print warning messages on stderr (default: warning messages are lost)')
        parser.add_argument('-r','--recursive', action='store_true',
            help='dive into subdirectories recursively (default: look at the given directory only)')
        parser.add_argument('-F','--files-if', type=str, default='True',
            help=f"Python boolean expression for selection of files, default: {F_default!r}, "
                 f"domain: {show(F_domain)}, syntax: standard Python3 syntax plus the YARE match operators '/' (case-sensitive) '//' (case-insensitive) and '@' (case-multiple)")
        parser.add_argument('-L','--line-pattern', type=str, default='',
            help=f"YARE pattern for line matching (default: '' = don't read file lines)")
        parser.add_argument('-i','--case-insensitive', action='store_true',
            help=f"-L match is case-insensitive (default: case-sensitive)")
        parser.add_argument('-m','--case-multiple', action='store_true',
            help=f"-L match is case-multiple (default: case-sensitive)")
        parser.add_argument('-j','--match-count', type=str, default=j_default,
            help=f"width of match count prefixed to matching lines, default: {j_default} = no match count, domain: {show(j_domain)}")
        parser.add_argument('-k','--line-count', type=str, default=k_default,
            help=f"width of line count prefixed to matching lines, default: {k_default} = no line count, domain: {show(k_domain)}")
        parser.add_argument('-S','--sort-by', type=str, default=default,
            help=f"keys for sorting of files or dirs, file mode default: {f_mode_S_default!r}, dir mode default: {d_mode_S_default!r}, "
                 f"domain: {show(S_domain)}, lowercase: ascending, uppercase: descending")
        parser.add_argument('-W','--output-format', type=str, default=default,
            help=double(f"format of output lines of files or dirs, files mode default: {f_mode_W_default!r} = {expand(f_mode_W_default)!r}, "
                        f"dirs mode default: {d_mode_W_default!r} = {expand(d_mode_W_default)!r}, domain: {show(W_domain)}, "
                        f"for int attributes: lowercase = as is, uppercase = with thousand commas, "
                        f"for str attributes: lowercase = unquoted, uppercase = quoted"))
        parser.add_argument('-u','--human-width', type=str, default=u_default,
            help=f"width of human-readable size (%%h attribute), default: {u_default}, domain: {show(u_domain)}")
        parser.add_argument('-N','--no-headers', action='store_true',
            help=f"do not write headers with attribute names")
        parser.add_argument('-n','--no-lines', action='store_true',
            help=f"do not write matching lines selected by -L")
        parser.add_argument('-d','--dirs-mode', action='store_true',
            help=f'run in dirs mode, group files by directory and print directories, default: run in files mode, print files')
        parser.add_argument('-a','--add-dir', action='store_true',
            help=double(f"add into each dir the values of the dir itself"))
        parser.add_argument('-t','--tot-dirs', action='store_true',
            help=double(f"totalize into parent dirs the values of son dirs"))
        parser.add_argument('-D','--dirs-if', type=str, default='True',
            help=f"Python boolean expression for selection of dirs, default: {D_default!r}, "
                 f"domain: {show(D_domain)}, syntax: standard Python3 syntax plus the YARE match operators '/' (case-sensitive) '//' (case-insensitive) and '@' (case-multiple)")
        parser.add_argument('path_files', nargs='?', default=I_default,
                            help=f"input [path/]file-pattern, default: {I_default!r}, {I_stdin!r} = read from stdin")
        parser.parse_args(argv[1:], arg)
        arg.use_wc = False ##### True for DEBUG ONLY

    def check_arguments():

        var.root, var.file_pattern = splitpath(longpath(arg.path_files))
        var.root = slash(var.root)
        if not isdir(var.root): error(f'Wrong path_files {arg.path_files!r}, directory {var.root!r} not found')

        if arg.sort_by == default: # -S
            arg.sort_by = d_mode_S_default if arg.dirs_mode else f_mode_S_default
        wrong = drop(compact(arg.sort_by), S_domain)
        if wrong:
            error(f'Wrong {wrong!r} in {"-S " + arg.sort_by}')

        if arg.output_format == default: # -W
            arg.output_format = d_mode_W_default if arg.dirs_mode else f_mode_W_default
        if arg.dirs_mode and '%' not in arg.output_format:
            arg.output_format = drop(arg.output_format, 'fFeEqQrR')
        arg.output_format = expand(arg.output_format)
        wrong = drop(compact(arg.output_format), W_domain)
        if wrong:
            error(f'Wrong {expand(wrong)} in {"-W " + arg.output_format!r}')

        if arg.human_width not in set(u_domain): # -u
            error(f'Wrong {"-u "+arg.human_width!r}')
        var.human_width = int(arg.human_width)

        if arg.case_insensitive and arg.case_multiple:
            error("Wrong '-i' and '-m' together")
        var.L_match = yarecimatch if arg.case_insensitive else yarecsmatch # -i
        var.L_match = yarecmmatch if arg.case_multiple else yarecsmatch # -m

        if arg.match_count not in set(j_domain): # -j
            error(f'Wrong {"-j " + arg.match_count!r}')
        if arg.line_count not in set(k_domain): # -k
            error(f'Wrong {"-k " + arg.line_count!r}')
        var.jk_names_line = shrink(('' if arg.match_count == '0' else 'j'.center(int(arg.match_count), center_char)) + ' ' +
                              ('' if arg.line_count == '0' else 'k'.center(int(arg.line_count), center_char)))

        if arg.human_width not in set(u_domain): # -u
            error(f'Wrong {"-u " + arg.human_width!r}')
        var.human_width = int(arg.human_width)

        var.domains = (compact(arg.output_format).lower() +
                       delquoted(arg.files_if) +
                       arg.dirs_mode * delquoted(arg.dirs_if) + arg.sort_by.lower())
        var.compute_cwxy = bool(take(var.domains, 'cwxy'))
        var.compute_m = bool(take(var.domains, 'm'))

    def read_stdin_and_print_lines_by_L():
        try:
            j = k = 0
            for line in stdin:
                k += 1
                line = line.rstrip()
                if var.L_match(line, arg.line_pattern):
                    j += 1
                    counts = ''
                    if arg.match_count > '0': counts += f'{j:0{arg.match_count}d} '
                    if arg.line_count > '0': counts += f'{k:0{arg.line_count}d} '
                    print(counts + line)
        except Exception as exception:
            warning(explain(exception) + f' reading from stdin')

    def read_files():
        var.files = []
        for dir, subdirs, names in walk(var.root, onerror=warning):
            if not arg.recursive:
                subdirs.clear()
            for name in names:
                if yarecsmatch(name, var.file_pattern):
                    path = joinpath(dir, name)
                    try:
                        stat_path = lstat(path)
                    except FileNotFoundError:
                        warning(f'No such file: {path!r}')
                        continue
                    a = stat_path.st_ino
                    b = filemode(stat_path.st_mode)
                    l = stat_path.st_nlink
                    try:
                        u = getpwuid(stat_path.st_uid).pw_name
                    except KeyError:
                        warning(f'User not found: {path!r}')
                        u = '???'
                    try:
                        g = getgrgid(stat_path.st_gid).gr_name
                    except KeyError:
                        warning(f'Group not found: {path!r}')
                        g = '???'
                    s = stat_path.st_size
                    h = int2human(s, var.human_width)
                    t = YmdHMS(stat_path.st_mtime)
                    m = 1
                    n = nesting(path)
                    o = len(name)
                    c = w = x = y = 0
                    if var.compute_cwxy and b[0] == '-':
                        if arg.use_wc:
                            y, w, c, x = [int(q) for q in shell(f'wc -l -w -m -L {path!r}')[-1].split()[:4]]
                        else:
                            try:
                                for line in open(path):
                                    line = line.rstrip()
                                    c += len(line)
                                    w += len(line.split())
                                    x = max(x, len(line))
                                    y += 1
                            except Exception as exception:
                                c = w = x = y = 0
                                warning(explain(exception) + f' reading from {path!r}')
                    d = slash(dir)
                    z = d[1:-1].split('/')[-1]
                    e = splitext(name)[-1]
                    f = name
                    p = path
                    try:
                        q, r = '->', readlink(p)
                        if not r.startswith('/'):
                            r = d + r
                    except:
                        q = r = ''
                    var.files.append([a, b, l, u, g, s, h, t, m, n, o, c, w, x, y, z, d, e, f, p, q, r])
        if not var.files:
            error(f'No such file found')
        if var.compute_m:
            f2m = defaultdict(int)
            for file in var.files:
                f2m[file[jf]] += 1
            for file in var.files:
                file[jm] = f2m[file[jf]]

    def filter_files_by_L():
        if arg.line_pattern and (arg.dirs_mode or arg.no_lines):
            files = []
            for file in var.files:
                if file[jb][0] == '-':
                    try:
                        for line in open(file[jp]):
                            if var.L_match(line.rstrip(), arg.line_pattern): #####
                                files.append(file)
                                break
                    except Exception as exception:
                        warning(explain(exception) + f' reading from {file[jp]!r}')
            if not files:
                error(f'No such file found')
            var.files = files
        
    def filter_files_by_F():
        if arg.files_if != 'True':
            var.files = [file for file in var.files if eval_expr('-F', arg.files_if, file)]
            if not var.files:
                error(f'No such file found')
        
    def filter_dirs_by_D():
        if arg.dirs_if != 'True':
            var.dirs = [dir for dir in var.dirs if eval_expr('-D', arg.dirs_if, dir)]
        if not var.dirs:
            error(f'No such directory found')
                    
    def sort_files_by_S():
        for char in arg.sort_by[::-1]:
            j = c2j[char.lower()]
            var.files.sort(key=lambda file: file[j], reverse=char.isupper())

    def sort_dirs_by_S():
        for char in drop(arg.sort_by, 'fFeEqQ')[::-1]:
            j = c2j[char.lower()]
            var.dirs.sort(key=lambda dir: dir[j], reverse=char.isupper())

    def print_files_by_W():
        fill_width_from_recs(var.files)
        if not arg.no_headers:
            print_names_line()
        for ifile, file in enumerate(var.files):
            print_rec_line(ifile + 1, file)

    def print_dirs_by_W():
        fill_width_from_recs(var.dirs)
        if not arg.no_headers:
            print_names_line()
        for idir, dir in enumerate(var.dirs):
            print_rec_line(idir + 1, dir)

    def print_files_by_W_with_lines_by_L():
        i = 0
        for file in var.files:
            if file[jb][0] == '-':
                j = k = 0
                try:
                    for line in open(file[jp]):
                        k += 1
                        line = line.rstrip()
                        if var.L_match(line, arg.line_pattern):
                            if j == 0:
                                i += 1
                                fill_width_from_rec(i, file)
                                if not arg.no_headers:
                                    print_names_line()
                                print_rec_line(i, file)
                                if not arg.no_headers and var.jk_names_line:
                                    print(var.jk_names_line)
                            j += 1
                            counts = ''
                            if arg.match_count > '0': counts += f'{j:0{arg.match_count}d} '
                            if arg.line_count > '0': counts += f'{k:0{arg.line_count}d} '
                            print(counts + line)
                except Exception as exception:
                    warning(explain(exception) + f' reading from {file[jp]!r}')

    def group_files_into_dirs():
        var.dset = set(file[jd] for file in var.files) # file dirs
        if arg.tot_dirs:
            var.dset |= set.union(*(set(ancestors(dir)) for dir in var.dset))
        var.d2dir = {}
        for dir in var.dset: # dir rec
            try:
                dir_stat = lstat(dir)
            except FileNotFoundError:
                warning(f'No such directory: {dir!r}')
                continue
            a = dir_stat.st_ino
            b = filemode(dir_stat.st_mode)
            l = dir_stat.st_nlink
            try:
                u = getpwuid(dir_stat.st_uid).pw_name
            except KeyError:
                warning(f'No user of {dir!r}')
                u = '????'
            try:
                g = getpwuid(dir_stat.st_gid).pw_name
            except KeyError:
                warning(f'No group of {dir!r}')
                g = '????'
            s = dir_stat.st_size if arg.add_dir else 0
            h = int2human(s, var.human_width)
            t = YmdHMS(dir_stat.st_mtime) if arg.add_dir else '0000-00-00 00:00:00'
            m = 1 if arg.add_dir else 0
            n = nesting(dir)
            o = c = w = x = y = 0
            d = p = dir
            z = d[1:-1].split('/')[-1]
            e = f = q = r = ''
            var.d2dir[d] = [a, b, l, u, g, s, h, t, m, n, o, c, w, x, y, z, d, e, f, p, q, r]
        try:
            for file in var.files: 
                d = file[jd]
                var.d2dir[d][js] += file[js]
                var.d2dir[d][jt] = max(var.d2dir[d][jt], file[jt])
                var.d2dir[d][jm] += 1
                var.d2dir[d][jz] = max(var.d2dir[d][jz], file[jz])
                var.d2dir[d][jc] += file[jc]
                var.d2dir[d][jw] += file[jw]
                var.d2dir[d][jx] = max(var.d2dir[d][jx], file[jx])
                var.d2dir[d][jy] += file[jy]
        except:
            print(file)
        if arg.tot_dirs: 
            for dir in sorted(var.d2dir, key=nesting, reverse=True):
                if dir != '/':
                    par = parent(dir)
                    var.d2dir[par][js] += var.d2dir[dir][js]
                    var.d2dir[par][jt] = max(var.d2dir[par][jt], var.d2dir[dir][jt])
                    var.d2dir[par][jc] += var.d2dir[dir][jc]
                    var.d2dir[par][jm] += var.d2dir[dir][jm]
                    var.d2dir[par][jz] = max(var.d2dir[par][jz], var.d2dir[dir][jz])
                    var.d2dir[par][jw] += var.d2dir[dir][jw]
                    var.d2dir[par][jx] = max(var.d2dir[par][jx], var.d2dir[dir][jx])
                    var.d2dir[par][jy] += var.d2dir[dir][jy]
        var.dirs = list(var.d2dir.values())
        for dir in var.dirs:
            dir[ju] = int2human(dir[js], var.human_width)

    #--------- main ---------

    get_arguments()
    check_arguments()
    if arg.path_files == '-':
        read_stdin_and_print_lines_by_L()
    else:
        read_files()
        filter_files_by_F()
        if arg.line_pattern and (arg.dirs_mode or arg.no_lines):
            filter_files_by_L() 
        if not arg.dirs_mode:
            # files mode
            sort_files_by_S()
            if arg.line_pattern and not arg.no_lines:
                print_files_by_W_with_lines_by_L()
            else:
                print_files_by_W()
        else:
            # dirs mode
            group_files_into_dirs()
            filter_dirs_by_D()
            sort_dirs_by_S()
            print_dirs_by_W()

def main():
    try:
        ffdd()
    except KeyboardInterrupt:
        pass
    print()
