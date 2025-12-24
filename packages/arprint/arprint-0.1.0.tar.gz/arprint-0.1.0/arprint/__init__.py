import arabic_reshaper
from bidi.algorithm import get_display

def arprint(text):
	
	ReshapedText = arabic_reshaper.reshape(text)
	BidiText = get_display(ReshapedText)
	print(BidiText)

