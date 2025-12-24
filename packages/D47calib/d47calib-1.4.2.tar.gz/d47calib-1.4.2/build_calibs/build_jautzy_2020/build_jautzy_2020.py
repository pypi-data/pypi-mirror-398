#! /usr/bin/env python3
'''
Generate D47calib regressions for Jautzy et al. (2020) in I-CDES
'''

DEFAULT_SIGMA_T = 1.

from D47crunch import *
from D47calib import D47calib
from pylab import *

D47data.ALPHA_18O_ACID_REACTION = np.exp(3.59 / (70 + 273.15) - 1.79e-3)  # (Kim et al., 2007, calcite)

data = D47data()
data.read('input/jautzy_2020_rawdata.csv')

data.wg()
data.crunch()

# for s in data.sessions:
# # 	data.sessions[s]['scrambling_drift'] = True
# # 	data.sessions[s]['slope_drift'] = True
# 	data.sessions[s]['wg_drift'] = True

data.standardize()
data.summary()
data.plot_sessions(dir = 'sessions')
data.plot_residuals(filename = 'D47residuals.pdf')
data.plot_distribution_of_analyses()
data.summary(dir = 'tables', verbose = False)
data.table_of_sessions(dir = 'tables', verbose = False)
data.table_of_samples(dir = 'tables', verbose = False)
data.table_of_analyses(dir = 'tables', verbose = False)


jautzy_metadata = read_csv('input/jautzy_2020_metadata.csv')
jautzy_calib_samples = [m['Sample'] for m in jautzy_metadata]
jautzy_calib_data = []

for sample in jautzy_calib_samples:
		meta = [m for m in jautzy_metadata if m['Sample'] == sample][0]
		jautzy_calib_data += [{
			'Sample': sample,
			'T': meta['T'],
			'sT': meta['sT'],
			'D47': data.samples[sample]['D47'],
			'sD47': data.samples[sample]['SE_D47'],
			}]

jautzy_CM_D47 = [[data.sample_D4x_covar(sample1, sample2) for sample1 in jautzy_calib_samples] for sample2 in jautzy_calib_samples]
jautzy_CM_T = diag([s['sT']**2 for s in jautzy_calib_data])
# for l in jautzy_CM_T:
# 	print(' '.join([f'{e**.5:04.2f}' if e else '----' for e in l]))

C = D47calib(
	samples = [s['Sample'] for s in jautzy_calib_data],
	D47 = [s['D47'] for s in jautzy_calib_data],
	T = [s['T'] for s in jautzy_calib_data],
	sD47 = jautzy_CM_D47,
	sT = jautzy_CM_T,
	description = 'Jautzy et al. (2020) synthetics, reprocessed in I-CDES',
	label = 'Jautzy et al. (2020)',
	degrees = [0,1,2],
	)

C.export('jautzy_2020', f'../jautzy_2020.py')
C.export_data('jautzy_2020_data.csv', label = True, T_correl = True, D47_correl = True)