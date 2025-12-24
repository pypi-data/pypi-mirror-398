from D47calib import *

K = [fiebig_2021.samples.index(_) for _ in ['LGB-2', 'DVH-2', 'DHC2-8']]

fiebig_temp = D47calib(
	samples = [fiebig_2021.samples[_] for _ in K],
	T = fiebig_2021.T[K],
	D47 = fiebig_2021.D47[K],
	sT = fiebig_2021.sT[K,:][:,K],
	sD47 = fiebig_2021.sD47[K,:][:,K],
	)

C = combine_D47calibs(
	calibs = [
		anderson_2021_lsce,
		fiebig_temp,
		],
	degrees = [0,2],
	same_T = [
		{'DVH-2', 'DHC2-8'},
		],
	)

C.description = 'Devils Hole & Laghetto Basso from Anderson et al. (2021) &  Fiebig et al. (2021)'
C.label = 'Devils Hole & Laghetto Basso from Anderson et al. (2021) &  Fiebig et al. (2021)'

C.export('devils_laghetto_2023', '../devils_laghetto_2023.py')
C.export_data('devils_laghetto_2023_data.csv', label = True, T_correl = True, D47_correl = True)