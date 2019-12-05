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
			minquantity = float(val)

itemhandlerlist = []