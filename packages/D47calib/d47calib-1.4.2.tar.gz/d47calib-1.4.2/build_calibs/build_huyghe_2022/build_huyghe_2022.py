#! /usr/bin/env python3

from D47crunch import *
from D47calib import D47calib
from pylab import *

Tdata = {
	'TW': 26.8, # env
	'BDV-S': 18.7, # env?
	'BDV-W': 11.01,
	'BDV-J': 7.5,
	'TES-S': 22.5, # env?
	'TES-W': 12.23,
	'PY': 13.44, # env
	'Ad': -1.8, # env
	}

sTdata = {
	'TW': 0.85,
	'BDV-S': 0.75,
	'BDV-W': 1.0,
	'BDV-J': 0.9,
	'TES-S': 2.1,
	'TES-W': 1.0,
	'PY': 0.06,
	'Ad': 0.5,
	}

rawdata = D47data()
rawdata.read('rawdata.csv')

for r in rawdata:
	if r['Sample'].startswith('BDV') and r['Sample'].endswith('H'):
		r['Sample'] = r['Sample'].replace('H', 'W')
	elif r['Sample'].startswith('BDV') and r['Sample'].endswith('E'):
		r['Sample'] = r['Sample'].replace('E', 'S')
	elif r['Sample'].startswith('TES') and r['Sample'].endswith('E'):
		r['Sample'] = r['Sample'][:-1] + 'S'
	elif r['Sample'].startswith('TES') and r['Sample'].endswith('H'):
		r['Sample'] = r['Sample'].replace('H', 'W')
	
rawdata = D47data([r for r in rawdata if r['Sample'] not in ['PNS-1', 'TES-13W']])

rawdata.wg()
rawdata.crunch()
rawdata.standardize()
rawdata.summary()
rawdata.table_of_sessions()
rawdata.table_of_samples()
rawdata.table_of_analyses()

groups = {
	'Ad': {s for s in rawdata.unknowns if s.startswith('Ad')},
	'PY': {s for s in rawdata.unknowns if s.startswith('PY')},
	'TW': {s for s in rawdata.unknowns if s.startswith('TW')},
	'BDV-S': {s for s in rawdata.unknowns if s.startswith('BDV') and s.endswith('S')},
	'BDV-W': {s for s in rawdata.unknowns if s.startswith('BDV') and s.endswith('W')},
	'TES-S': {s for s in rawdata.unknowns if s.startswith('TES') and s.endswith('S')},
	'TES-W': {s for s in rawdata.unknowns if s.startswith('TES') and s.endswith('W')},
	}

SAMPLES, D47, sD47 = rawdata.combine_samples(groups)

T = [Tdata[k] for k in SAMPLES]
sT = [sTdata[k] for k in SAMPLES]

C = D47calib(
	samples = SAMPLES,
	D47 = D47,
	T = T,
	sD47 = sD47,
	sT = sT,
	description = 'Huyghe et al. (2022) marine bivalves in I-CDES',
	label = 'Huyghe et al. (2022) marine bivalves',
	degrees = [0,2],
	)

C.export('huyghe_2022', '../huyghe_2022.py')
C.export_data('huyghe_2022_data.csv', label = True, T_correl = True, D47_correl = True)

fig = figure()
C.invT_xaxis()
C.plot_error_bars()
C.plot_data()
C.plot_bff()
C.plot_bff_ci()

savefig(f'huyghe_2022.pdf')
