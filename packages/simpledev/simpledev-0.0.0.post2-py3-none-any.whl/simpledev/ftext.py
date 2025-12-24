font = {
    'none': '\033[0m',
    'bold-on': '\033[1m', 'italic-on': '\033[3m', 'line-on': '\033[4m', 'inv-on': '\033[7m', 'cross-on': '\033[9m',
    'bold-of': '\033[22m', 'italic-of': '\033[23m', 'line-of': '\033[24m', 'inv-of': '\033[27m', 'cross-of': '\033[29m'
}
# Foreground color
color = {
    'black': '\033[30m', 'D_red': '\033[31m', 'D_green': '\033[32m', 'D_yellow': '\033[33m', 'D_blue': '\033[34m',
    'D_magenta': '\033[35m', 'D_cyan': '\033[36m', 'D_gray': '\033[90m', 'gray': '\033[37m', 'red': '\033[91m',
    'green': '\033[92m', 'yellow': '\033[93m', 'blue': '\033[94m', 'magenta': '\033[95m', 'cyan': '\033[96m',
    'white': '\033[97m', 'def': '\033[39m'
}
# Background color
b_color = {
    'black': '\033[40m', 'D_red': '\033[41m', 'D_green': '\033[42m', 'D_yellow': '\033[43m', 'D_blue': '\033[44m',
    'D_magenta': '\033[45m', 'D_cyan': '\033[46m', 'D_gray': '\033[100m', 'gray': '\033[47m', 'red': '\033[101m',
    'green': '\033[102m', 'yellow': '\033[103m', 'blue': '\033[104m', 'magenta': '\033[105m', 'cyan': '\033[106m',
    'white': '\033[107m', 'def': '\033[49m'
}
# Color by ID
i_color = list(color.values())


def _test_print_format(text: str = 'Aa Bb Cc Dd 01234567 . ! % ? ■') -> None:
    for name in [font, color, b_color]:
        print(*[f'{i}: {name[i]}{text}\033[0m' for i in name], sep='\n')
