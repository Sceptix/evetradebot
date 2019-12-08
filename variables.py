with open('settings.txt', 'r') as settings:
	for line in settings:
		(key, val) = line.split()
		if key == "minmargin":
			minmargin = float(val)
		elif key == "maxmargin":
			maxmargin = float(val)
		elif key == "capital":
			capital = float(val)
		elif key == "minquantity":
			minquantity = int(val)
		elif key == "maxhandlers":
			maxhandlers = int(val)
		elif key == "tesseractpath":
			tesseractpath = val

def init():
	global itemhandlerlist
	global bidaplh
	global sellaplh
	itemhandlerlist = []
	bidaplh = (None, None)
	sellaplh = (None, None)