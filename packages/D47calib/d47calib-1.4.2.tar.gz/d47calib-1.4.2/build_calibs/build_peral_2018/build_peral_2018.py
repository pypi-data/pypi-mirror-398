#! /usr/bin/env python3
'''
Generate D47calib regressions for Peral et al. (2018) in I-CDES
'''

from D47crunch import *
from D47calib import D47calib
from pylab import *

### Read binned sample names from metadata:
metadata = read_csv('foram_D47_calibration_data.csv')
metadata = [
	_ for _ in metadata
	if _['Ref'] == 'Peral et al. (2018)'
	and _['Type'] == 'planktic'
	]

Ts = {}
for site in {_['Site'] for _ in metadata}:
	Ts[site] = mean([_['Tiso_species'] for _ in metadata if _['Site'] == site])

metadata = sorted(metadata, key = lambda _: Ts[_['Site']])

# ptable = [['Sample', 'Core', 'T', 'd18Ow', 'sd18Ow', 'd18Oc', 'sd18Oc']] +[
# 	[
# 		_['Sample'],
# 		_['Site'],
# 		f"{_['Tiso_species']:5.2f}",
# 		f"{_['d18Osw']:.2f}",
# 		f"{_['SE_d18Osw']:.2f}",
# 		f"{_['d18O_VPDB']:.2f}",
# 		f"{_['SE_d18O_VPDB']:.2f}",
# 		] for _ in metadata
# 	]
# print(pretty_table(ptable))

### COMPUTE CORREL BETWEEN Tiso_species_500m VALUES

samples = [_ for _ in metadata]
N = len(samples)

R = eye(N)

for i, s1 in enumerate(samples):
	for j, s2 in enumerate(samples):
		if j > i and s1['Site'] == s2['Site']:


			assert s1['d18Osw_500m'] == s2['d18Osw_500m'], f"d18Osw_500m should be the same for samples {s1['Sample']} and {s2['Sample']}"
			assert s1['SE_d18Osw_500m'] == s2['SE_d18Osw_500m'], f"SE_d18Osw_500m should be the same for samples {s1['Sample']} and {s2['Sample']}"				
			
			d18w, sd18w = s1['d18Osw_500m'], s1['SE_d18Osw_500m']
			d18c_1, sd18c_1 = s1['d18O_VPDB'], s1['SE_d18O_VPDB']
			d18c_2, sd18c_2 = s2['d18O_VPDB'], s2['SE_d18O_VPDB']

			_computation = '''
			cov(klna18_1, klna18_2) = 1e6 * cov(log(1+d18c_1/1e3) - log(1+d18w/1e3), log(1+d18c_2/1e3) - log(1+d18w/1e3))
			cov(klna18_1, klna18_2) = 1e6 * cov(log(1+d18w/1e3), log(1+d18w/1e3))
			cov(klna18_1, klna18_2) = sd18w**2 / (1+d18w/1e3)**2

			cov(klna18_1, klna18_1) = sd18c_1**2 / (1+d18c_1/1e3)**2 + sd18w**2 / (1+d18w/1e3)**2

			cov(klna18_2, klna18_2) = sd18c_2**2 / (1+d18c_2/1e3)**2 + sd18w**2 / (1+d18w/1e3)**2

			correl(klna18_1, klna18_2) = (
				sd18w**2 / (1+d18w/1e3)**2
				/ (sd18c_1**2 / (1+d18c_1/1e3)**2 + sd18w**2 / (1+d18w/1e3)**2)**.5
				/ (sd18c_2**2 / (1+d18c_2/1e3)**2 + sd18w**2 / (1+d18w/1e3)**2)**.5
				)
			'''

			correl_s1_s2 = (
				sd18w**2 / (1+d18w/1e3)**2
				/ (sd18c_1**2 / (1+d18c_1/1e3)**2 + sd18w**2 / (1+d18w/1e3)**2)**.5
				/ (sd18c_2**2 / (1+d18c_2/1e3)**2 + sd18w**2 / (1+d18w/1e3)**2)**.5
				)
			R[i,j] = correl_s1_s2
			R[j,i] = correl_s1_s2

T = [
	_['Twoa23_1500m'] if _['Sample'] == 'MD04-2720_pachyD' else _['Tiso_species']
	for _ in metadata
	]
sT = [
	_['SE_Twoa23_1500m'] if _['Sample'] == 'MD04-2720_pachyD' else _['SE_Tiso_species']
	for _ in metadata
	]

CM_T = diag(sT) @ R @ diag(sT)



### Process data with different size fractions treated as different samples:
rawdata = D47data()
	
rawdata.read('peral_2018_rawdata.csv')
rawdata.wg()
rawdata.crunch()
rawdata.standardize()
rawdata.summary(dir = 'output', verbose = False)
rawdata.table_of_sessions(dir = 'output', verbose = False)
rawdata.table_of_samples(dir = 'output', verbose = False)
rawdata.table_of_analyses(dir = 'output', verbose = False)

### Define sample groups to bin together:
groups = {l['Sample']: [] for l in metadata}
for r in groups:
	groups[r] += [s for s in rawdata.samples if s.startswith(r)]

samples_new, D47_new, CM_new = rawdata.combine_samples(groups)

reorder = [samples_new.index(s['Sample']) for s in samples]

samples_new = [samples_new[_] for _ in reorder]
D47_new = D47_new[reorder]
CM_new = CM_new[reorder,:][:,reorder]


C = D47calib(
	samples = list(samples_new),
	D47 = D47_new,
	T = T,
	sD47 = CM_new,
	sT = CM_T,
	description = 'Peral et al. (2018, 10.1016/j.gca.2018.07.016) planktic foraminifer calibration, as reprocessed by Daëron & Gray (in review)',
	label = 'Peral et al. (2018)',
	degrees = [0,2],
	)

C.export('peral_2018', '../peral_2018.py')
C.export_data('peral_2018_data.csv', label = True, T_correl = True, D47_correl = True)