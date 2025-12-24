from D47calib import *

# from scipy.stats import chi2

# l = 7

# for calib in [
# 	breitenbach_2018,
# 	peral_2018,
# 	jautzy_2020,
# 	anderson_2021_mit,
# # 	anderson_2021_lsce,
# 	fiebig_2021,
# 	huyghe_2022,
# 	]:
# 	print('\n'+calib.label.upper())
# 	print(f'{"DEGREES":<{12:.0f}} {"RCHISQ":>{l:.0f}} {"AIC":>{l:.0f}} {"BIC":>{l:.0f}}')
# 	print('-'*12 + ' ' + '-'*l + ' ' + '-'*l + ' ' + '-'*l)
# 	for degs in (
# 		[0,2],
# 	# 	[0,2,3],
# 		[0,1,2,3],
# 		[0,1,2],
# 		):
# 
# 		C = combine_D47calibs(calibs = [calib], degrees = degs)
# 		try:
# 			print(f'{str(C.degrees):<{12:.0f}} {C.red_chisq:>{l:.0f}.4f} {C.aic:>{l:.0f}.1f} {C.bic:>{l:.0f}.1f}')
# 		except TypeError:
# 			pass
# 	print('-'*12 + ' ' + '-'*l + ' ' + '-'*l + ' ' + '-'*l)

# print('\nCOMBINED')
# print(f'{"DEGREES":<{12:.0f}} {"RCHISQ":>{l:.0f}} {"PCHISQ":>{l:.0f}} {"AIC":>{l:.0f}} {"BIC":>{l:.0f}}')
# print('-'*12 + ' ' + '-'*l + ' ' + '-'*l + ' ' + '-'*l + ' ' + '-'*l)
# for degs in (
# 	[0,2],
# 	[0,1,2,3],
# 	[0,1,2],
# 	):
# 
# 	C = combine_D47calibs(
# 		calibs = [
# 			breitenbach_2018,
# 			peral_2018,
# 			jautzy_2020,
# 			anderson_2021_mit,
# 			anderson_2021_lsce,
# 			fiebig_2021,
# 			huyghe_2022,
# 			],
# 		degrees = degs,
# 		same_T = [
# 			{'ETH-1-1100-SAM', 'ETH-1-1100'},
# 			{'ETH-2-1100-SAM', 'ETH-2-1100'},
# 			{'DVH-2', 'DHC2-8'},
# 			],
# 		)
# 
# 	C.color = (0,0,0)
# 	C.description = 'Combined I-CDES calibration'
# 	C.label = 'Combined'
# 
# 	p_chisq = chi2.cdf(C.chisq, C.Nf)
# 
# 	print(f'{str(C.degrees):<{12:.0f}} {C.red_chisq:>{l:.0f}.4f} {p_chisq:>{l:.0f}.3f} {C.aic:>{l:.0f}.1f} {C.bic:>{l:.0f}.1f}')
# 
# print('-'*12 + ' ' + '-'*l + ' ' + '-'*l + ' ' + '-'*l + ' ' + '-'*l)

C = combine_D47calibs(
	calibs = [
		breitenbach_2018,
		peral_2018,
		jautzy_2020,
		anderson_2021_mit,
		anderson_2021_lsce,
		fiebig_2021,
		huyghe_2022,
		],
	degrees = [0,1,2],
	same_T = [
		{'ETH-1-1100-SAM', 'ETH-1-1100'},
		{'ETH-2-1100-SAM', 'ETH-2-1100'},
		{'CA726', 'CM-351'},
		{'DVH-2', 'DHC2-8'},
		{'CA-120', 'CA120'},
		{'CA-170', 'CA170'},
		{'CA-200', 'CA200'},
		{'CA-250A', 'CA250_06'},
		{'CA-250B', 'CA250_09'},
		],
	)


C.color = (0,0,0)
C.description = 'Combined I-CDES calibration'
C.name = 'OGLS23'
C.label = 'Combined I-CDES calibration'

C.export('OGLS23', 'OGLS23.py')
C.export_data('OGLS23_data.csv', label = True, T_correl = True, D47_correl = True)

with open('../src/D47calib/_calibs.py', 'a') as fid:
		with open('OGLS23.py') as gid:
			fid.write(gid.read())
			fid.write('\nogls_2023 = OGLS23\n')