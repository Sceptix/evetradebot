with open('settings.txt', 'r') as settings:
	for line in settings:
		(key, val) = line.split()
		if key == "profitableratio":
			profitableratio = float(val)
		elif key == "capital":
			capital = float(val)

itemhandlerlist = []