with open('../src/D47calib/_calibs.py', 'w') as fid:

	fid.write('from D47calib import D47calib')

	for file in [
		'breitenbach_2018.py',
		'peral_2018.py',
		'jautzy_2020.py',
		'anderson_2021_mit.py',
		'anderson_2021_lsce.py',
		'fiebig_2021.py',
		'huyghe_2022.py',
		'devils_laghetto_2023.py',
		]:
	
		try:
			with open(file) as gid:
				fid.write(gid.read())
		except FileNotFoundError:
			pass