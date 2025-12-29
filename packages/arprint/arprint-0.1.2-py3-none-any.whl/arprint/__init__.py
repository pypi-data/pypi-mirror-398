import arabic_reshaper
from bidi.algorithm import get_display
import getpass
import sys

COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'reset': '\033[0m'
}

def _apply_style(text, color):
    if color and color.lower() in COLORS:
        return f"{COLORS[color.lower()]}{text}{COLORS['reset']}"
    return text

def arprint(text, color=None):
    artext = arabic_reshaper.reshape(text)
    arrtext = get_display(artext)
    
    final_text = _apply_style(arrtext, color)
    print(final_text)

def arinput(text, color=None, password=False):
    artext = arabic_reshaper.reshape(text)
    arrtext = get_display(artext)
    prompt = _apply_style(arrtext + " ", color)
    
    if password:
        return getpass.getpass(prompt)
    else:
        return input(prompt)