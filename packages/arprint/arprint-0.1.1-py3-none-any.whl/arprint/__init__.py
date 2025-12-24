import sys
from arabic_reshaper import reshape
from bidi.algorithm import get_display

def arprint(text):
    if sys.stdout.isatty():
        reshaped_text = reshape(text)
        bidi_text = get_display(reshaped_text)
        print(bidi_text)
    else:
        print(text)

