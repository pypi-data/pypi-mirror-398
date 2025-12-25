```
usage: ffdd [-h] [-V] [-v] [-r] [-F FILES_IF] [-L LINE_PATTERN] [-i] [-m]
            [-j MATCH_COUNT] [-k LINE_COUNT] [-S SORT_BY] [-W OUTPUT_FORMAT]
            [-u HUMAN_WIDTH] [-N] [-n] [-d] [-a] [-t] [-D DIRS_IF]
            [path_files]

list Files or Directories - an alternative to ls find tree du grep wc nl ...

 ┌─────┬──────┬────────────────────────────────────────────────────────┐
 │ VAR │ TYPE │                       CONTENT                          │
 ├─────┼──────┼────────────────────────────────────────────────────────┤
 │  i  │ int  │ line count (in -W only)                                │
 │  a  │ int  │ file's inode number                                    │
 │  b  │ str  │ file's permission bits '-rwxrwxrwx' or 'lrwxrwxrwx'    │
 │  l  │ int  │ number of links pointing to this file                  │
 │  u  │ str  │ file's user name                                       │
 │  g  │ str  │ file's group name                                      │
 │  s  │ int  │ file's size in bytes                                   │
 │  h  │ str  │ file's size as human-readable number                   │
 │  t  │ str  │ file's last modification time 'YYYY-mm-dd HH:MM:SS'    │
 │  m  │ int  │ file's multiplicity = number of homonym files          │
 │  n  │ int  │ file's nesting = number of '/' in path minus one       │
 │  o  │ int  │ filename length                                        │
 │  c  │ int  │ number of characters in file                           │
 │  w  │ int  │ number of words in file                                │
 │  x  │ int  │ max line length in file                                │
 │  y  │ int  │ number of lines in file                                │
 │  z  │ str  │ last level of directory (no '/')                       │
 │  d  │ str  │ abs path of directory (ending with '/')                │
 │  f  │ str  │ filename                                               │
 │  e  │ str  │ filename extension (always starting with '.')          │
 │  p  │ str  │ abs path %d%f = directory + filename                   │
 │  q  │ str  │ '->' if file is a link else ''                         │
 │  r  │ str  │ target if file is a link else ''                       │
 │  K  │ int  │ 1024      (in -F only)                                 │
 │  M  │ int  │ 1024 ** 2 (in -F only)                                 │
 │  G  │ int  │ 1024 ** 3 (in -F only)                                 │
 │  T  │ int  │ 1024 ** 4 (in -F only)                                 │
 │  P  │ int  │ 1024 ** 5 (in -F only)                                 │
 │  E  │ int  │ 1024 ** 6 (in -F only)                                 │
 │  Z  │ int  │ 1024 ** 7 (in -F only)                                 │
 │  Y  │ int  │ 1024 ** 8 (in -F only)                                 │
 └─────┴──────┴────────────────────────────────────────────────────────┘

                               Figure a. File Variables

 ┌─────┬──────┬────────────────────────────────────────────────────────┐
 │ VAR │ TYPE │                       CONTENT                          │
 ├─────┼──────┼────────────────────────────────────────────────────────┤
 │  i  │ int  │ line count (in -W only)                                │
 │  a  │ int  │ dir's inode number                                     │
 │  b  │ str  │ dir's permission bits 'drwxrwxrwx'                     │
 │  l  │ int  │ number of links pointing to this dir                   │
 │  u  │ str  │ dir's user name                                        │
 │  g  │ str  │ dir's group name                                       │
 │  s  │ int  │ tot size in bytes of dir's files                       │
 │  h  │ str  │ tot size of dir's files as human-readable number       │
 │  t  │ str  │ max last mod time of dir's files 'YYYY-mm-dd HH:MM:SS' │
 │  m  │ int  │ tot number of dir's files                              │
 │  n  │ int  │ dir's nesting = number of '/' in path minus one        │
 │  o  │ int  │ max length of dir's filenames                          │
 │  c  │ int  │ tot number of characters in dir's files                │
 │  w  │ int  │ tot number of words in dir's files                     │
 │  x  │ int  │ max line length in dir's files                         │
 │  y  │ int  │ tot number of lines in dir's files                     │
 │  z  │ str  │ last level of directory (no '/')                       │
 │  d  │ str  │ abs path of directory (ending with '/')                │
 │  e  │ str  │ ''                                                     │
 │  f  │ str  │ ''                                                     │
 │  p  │ str  │ abs path of directory (ending with '/')                │
 │  q  │ str  │ ''                                                     │
 │  r  │ str  │ ''                                                     │
 │  K  │ int  │ 1024      (in -D only)                                 │
 │  M  │ int  │ 1024 ** 2 (in -D only)                                 │
 │  G  │ int  │ 1024 ** 3 (in -D only)                                 │
 │  T  │ int  │ 1024 ** 4 (in -D only)                                 │
 │  P  │ int  │ 1024 ** 5 (in -D only)                                 │
 │  E  │ int  │ 1024 ** 6 (in -D only)                                 │
 │  Z  │ int  │ 1024 ** 7 (in -D only)                                 │
 │  Y  │ int  │ 1024 ** 8 (in -D only)                                 │
 └─────┴──────┴────────────────────────────────────────────────────────┘

                               Figure b. - Dir Variables

Examples:

    $ ffdd '.*' # list hidden files only
    $ ffdd '[!.]*' # list unhidden files only
    $ ffdd '^.*' # list unhidden files only (another way)
    $ ffdd -r -F 'M<=s<2*M' # list files big at least 1 MB but less than 2 MB
    $ ffdd -r -d -F 'M<=s<2*M' # list dirs having files big at least 1 MB but less than 2 MB
    $ ffdd -r -d -D 'M<=s<2*M' # list dirs big at least 1 MB but less than 2 MB
    $ ffdd -F 'b[0]=="l"' # list links only, not files
    $ ffdd -F 'b/"l*"' # list links only, not files (another way)
    $ ffdd -r -F 'm>1' -Sfd # list groups of homonym files
    $ ffdd -F '"2014"<=t<"2018"' # list files saved in years 2014-2017
    $ ffdd -F 't/"201[4-7]*"' # list files saved in years 2014-2017 (another way)
    $ ffdd -L '=[!#]&(def *,* def *,class *,* class *)' -j4 -k4 '*.py'
    $    # show 'def' and 'class' statements in Python files, excluding lines with comments
    $ ffdd -L '*' -j4 - <xyz.py >nnnn-xyz.py # create a copy with numbered lines
    $ ffdd -r -W 'rm -v %P # %i' '~/*.back' | bash # remove all .back files
    $ ffdd -r -W 'mv -v %P ~/Pictures # %i' '~/*.jpg' | bash # gather together all .jpg files

Versions:

   • 0.0.4
        • experimental
        • bug: '|' operator not allowed between dicts in Python 3.6, fixed

    • 0.0.3
        • experimental
        • now uses libyare 1.2.1

    • 0.0.2
        • experimental
        • attribute 'u', renamed as 'h'
        • attribute 'o', renamed as 'u'
        • attribute 'z', renamed as 'o'
        • attribute 'z' = last level of directory, added
        • in -W uppercase name for int attributes now inserts thousand commas
        • -c argument, removed

    • 0.0.1
        • experimental
        • bug: wrong path in r variable, fixed
        • bug: wrong value in g variable, fixed
        • format of t variable, changed from 'YYYY-mm-dd_HH:MM:SS' into 'YYYY-mm-dd HH:MM:SS'

    • 0.0.0
        • experimental
        • first version published on pypi.org

For details about YARE (Yet Another Regular Expression), see:

    https://pypi.org/project/libyare

positional arguments:
  path_files            input [path/]file-pattern, default: './*', '-' = read
                        from stdin

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -v, --verbose         print warning messages on stderr (default: warning
                        messages are lost)
  -r, --recursive       dive into subdirectories recursively (default: look at
                        the given directory only)
  -F FILES_IF, --files-if FILES_IF
                        Python boolean expression for selection of files,
                        default: 'True', domain:
                        'ablugshtmnocwxyzdefpqrKMGTPEZY', syntax: standard
                        Python3 syntax plus the YARE match operators '/'
                        (case-sensitive) '//' (case-insensitive) and '@'
                        (case-multiple)
  -L LINE_PATTERN, --line-pattern LINE_PATTERN
                        YARE pattern for line matching (default: '' = don't
                        read file lines)
  -i, --case-insensitive
                        -L match is case-insensitive (default: case-sensitive)
  -m, --case-multiple   -L match is case-multiple (default: case-sensitive)
  -j MATCH_COUNT, --match-count MATCH_COUNT
                        width of match count prefixed to matching lines,
                        default: 0 = no match count, domain: '0123456789'
  -k LINE_COUNT, --line-count LINE_COUNT
                        width of line count prefixed to matching lines,
                        default: 0 = no line count, domain: '0123456789'
  -S SORT_BY, --sort-by SORT_BY
                        keys for sorting of files or dirs, file mode default:
                        'df', dir mode default: 'd', domain:
                        'ablugshtmnocwxyzdefpqrABLUGSHTMNOCWXYZDEFPQR',
                        lowercase: ascending, uppercase: descending
  -W OUTPUT_FORMAT, --output-format OUTPUT_FORMAT
                        format of output lines of files or dirs, files mode
                        default: 'IblugShtmnopqr' = '%I %b %l %u %g %S %h %t
                        %m %n %o %p %q %r', dirs mode default: 'IblugShtmnod'
                        = '%I %b %l %u %g %S %h %t %m %n %o %d', domain:
                        'iablugshtmnocwxyzdefpqrIABLUGSHTMNOCWXYZDEFPQR', for
                        int attributes: lowercase = as is, uppercase = with
                        thousand commas, for str attributes: lowercase =
                        unquoted, uppercase = quoted
  -u HUMAN_WIDTH, --human-width HUMAN_WIDTH
                        width of human-readable size (%h attribute), default:
                        6, domain: '56789'
  -N, --no-headers      do not write headers with attribute names
  -n, --no-lines        do not write matching lines selected by -L
  -d, --dirs-mode       run in dirs mode, group files by directory and print
                        directories, default: run in files mode, print files
  -a, --add-dir         add into each dir the values of the dir itself
  -t, --tot-dirs        totalize into parent dirs the values of son dirs
  -D DIRS_IF, --dirs-if DIRS_IF
                        Python boolean expression for selection of dirs,
                        default: 'True', domain:
                        'ablugshtmnocwxyzdefpqrKMGTPEZY', syntax: standard
                        Python3 syntax plus the YARE match operators '/'
                        (case-sensitive) '//' (case-insensitive) and '@'
                        (case-multiple)
```
