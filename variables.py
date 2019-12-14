def init():
	global itemhandlerlist
	global bidaplh
	global sellaplh
	global minmargin
	global maxmargin
	global capital
	global minquantity
	global maxhandlers
	global tesseractpath
	global sleepmultiplier
	itemhandlerlist = []
	bidaplh = (None, None)
	sellaplh = (None, None)
	with open('settings.txt', 'r') as settings:
		for line in settings:
			if line.isspace():
				continue
			print(line.split(None, 1))
			(key, val) = line.split(None, 1)
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
			elif key == "sleepmultiplier":
				sleepmultiplier = float(val)