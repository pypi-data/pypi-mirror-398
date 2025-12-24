#! /usr/bin/env python3
'''
Generate D47calib regressions for Anderson et al. (2021) in I-CDES
'''


ANDERSON_DEFAULT_SIGMA_T = 1.0

# import ogls
# ogls.logger.add(sys.stderr, format="{time} {level} {message}", level="DEBUG")

from D47crunch import *
from D47calib import D47calib
from pylab import *


anderson_data = D47data()
anderson_data.read('input/anderson_2021_data.csv')

for r in anderson_data:
	r['Session'] = f'session_{int(r["Session"][7:]):02.0f}'
anderson_data = D47data([r for r in anderson_data if r['Session'][-2:] not in ['05', '25']]) # sessions 05 and 25 don't have enough analyses

anderson_data.refresh()

anderson_data.wg()
anderson_data.crunch()
anderson_data.standardize()
anderson_data.summary()
anderson_data.plot_sessions(dir = 'sessions')
anderson_data.plot_residuals(filename = 'D47residuals.pdf')
anderson_data.plot_distribution_of_analyses()
anderson_data.summary(dir = 'tables', verbose = False)
anderson_data.table_of_sessions(dir = 'tables', verbose = False)
anderson_data.table_of_samples(dir = 'tables', verbose = False)
anderson_data.table_of_analyses(dir = 'tables', verbose = False)

anderson_metadata = read_csv('input/anderson_2021_metadata.csv')
anderson_calib_samples = [m['Sample'] for m in anderson_metadata]
anderson_calib_data = []

for sample in anderson_calib_samples:
		meta = [m for m in anderson_metadata if m['Sample'] == sample][0]
		anderson_calib_data += [{
			'Sample': sample,
			'T': meta['Temperature'],
			'sT': meta['sT'],
			'D47': anderson_data.samples[sample]['D47'],
			'sD47': anderson_data.samples[sample]['SE_D47'],
			}]
# 		print(pretty_listofdict(anderson_calib_data))

anderson_CM_D47 = [[anderson_data.sample_D4x_covar(sample1, sample2) for sample1 in anderson_calib_samples] for sample2 in anderson_calib_samples]
anderson_CM_T = diag([float(s['sT'])**2 for s in anderson_calib_data])

# anderson_CM_T = eye(len(anderson_metadata)) * ANDERSON_DEFAULT_SIGMA_T**2
# 
# for k,s in enumerate(anderson_calib_samples):
# 	if '-1100-SAM' in s:
# 		anderson_CM_T[k,k] = 10**2

C = D47calib(
	samples = [s['Sample'] for s in anderson_calib_data],
	D47 = [s['D47'] for s in anderson_calib_data],
	T = [s['T'] for s in anderson_calib_data],
	sD47 = anderson_CM_D47,
	sT = anderson_CM_T,
	description = 'Anderson et al. (2021) calibration, processed in I-CDES',
	label = 'Anderson et al. (2021)',
	degrees = [0,2],
	)

C.export('anderson_2021_mit', '../anderson_2021_mit.py')
C.export_data('anderson_2021_mit_data.csv', label = True, T_correl = True, D47_correl = True)

fig = figure()
C.invT_xaxis()
C.plot_error_bars()
C.plot_data()
C.plot_bff()
C.plot_bff_ci()

savefig(f'anderson_2021_mit.pdf')
