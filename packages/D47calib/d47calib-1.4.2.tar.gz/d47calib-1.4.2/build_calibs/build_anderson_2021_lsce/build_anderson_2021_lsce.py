#! /usr/bin/env python3
'''
Generate D47calib regressions for DVH-2 and LGB-2 in I-CDES
'''
from D47crunch import *
from D47calib import D47calib
from pylab import *

rawdata = D47data()
rawdata.read('input/devils_laghetto_2021_data.csv')

rawdata.wg()
rawdata.crunch()
rawdata.standardize()
rawdata.plot_sessions(dir = 'sessions')
rawdata.summary(dir = 'tables', verbose = False)
rawdata.table_of_sessions(dir = 'tables', verbose = False)
rawdata.table_of_samples(dir = 'tables', verbose = False)
rawdata.table_of_analyses(dir = 'tables', verbose = False)

devils_laghetto_2021_metadata = read_csv('input/devils_laghetto_2021_metadata.csv')
calib_samples = [m['Sample'] for m in devils_laghetto_2021_metadata]
calib_data = []

for sample in calib_samples:
		meta = [m for m in devils_laghetto_2021_metadata if m['Sample'] == sample][0]
		calib_data += [{
			'Sample': sample,
			'T': meta['T'],
			'sT': meta['sT'],
			'D47': rawdata.samples[sample]['D47'],
			'sD47': rawdata.samples[sample]['SE_D47'],
			}]

CM_D47 = [[rawdata.sample_D4x_covar(sample1, sample2) for sample1 in calib_samples] for sample2 in calib_samples]

C = D47calib(
	samples = [s['Sample'] for s in calib_data],
	D47 = [s['D47'] for s in calib_data],
	T = [s['T'] for s in calib_data],
	sD47 = CM_D47,
	sT = [s['sT'] for s in calib_data],
	description = 'Devils Hole & Laghetto Basso from Anderson et al. (2021), processed in I-CDES',
	name = 'anderson_2021_lsce',
	label = 'Slow-growing calcites from Anderson et al. (2021)',
	degrees = [0,2],
	)

C.export('anderson_2021_lsce', '../anderson_2021_lsce.py')
C.export_data('anderson_2021_lsce_data.csv', label = True, T_correl = True, D47_correl = True)
