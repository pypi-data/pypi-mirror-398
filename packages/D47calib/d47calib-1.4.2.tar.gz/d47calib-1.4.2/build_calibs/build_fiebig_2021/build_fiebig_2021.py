#! /usr/bin/env python3
'''
Data processing for:
"Calibration of the dual clumped isotope thermometer for carbonates"
by Fiebig et al. (2021)
'''

__author__    = 'Mathieu Daëron'
__contact__   = 'daeron@lsce.ipsl.fr'
__copyright__ = 'Copyright (c) 2020 Mathieu Daëron'
__license__   = 'Modified BSD License - https://opensource.org/licenses/BSD-3-Clause'
__date__      = '2021-03-18'
__version__   = '0.5'

from copy import deepcopy
import xlrd
from glob import glob
from D47calib import *
from D47crunch import *
from matplotlib.ticker import MultipleLocator
from pylab import *

CUT_SESSIONS = True

def plot_ETH_drift(data, filename):
	fig = figure(figsize = (8,4))
	subplots_adjust(.125,.2,.95,.85, .4, .4)
	
	ax = subplot(121)
	color = (.75,0,.25)
	X = [mean([r['Date'] for r in data.sessions[s]['data'] if 'Sample_original' in r and r['Sample_original'] in ['ETH-1', 'ETH-2']]) for s in data.sessions]
	X = [x - min(X) for x in X]
	Y, sY = zip(*[data.sample_average([f'ETH-1__{s}', f'ETH-2__{s}'], [.5, .5]) for s in data.sessions])
	eY = [sy*data.t95 for sy in sY]
	errorbar(X, Y, eY, ls = 'None', marker = 'None', ecolor = color, elinewidth = 1, capthick = 1, capsize = 3)
	plot(X, Y, 'wo', mec = color, mew = 1)

	ax.yaxis.set_major_locator(MultipleLocator(.01))
	xlabel('Time (days)')
	ylabel('Δ$_{47}$ average of ETH-1 and ETH-2\nfor each session (CDES, ‰)', labelpad = 10)
	grid(alpha = 0.2, axis = 'y')
	x1,x2,y1,y2 = axis()
	h = 0.03
	axis([x1,x2,(y1+y2-h)/2,(y1+y2+h)/2])
	axhline((0.2052+0.2085)/2, color = color, lw = 2, alpha = .25)
	text(280, (0.2052+0.2085)/2 - 0.0001, 'InterCarb\nvalue', linespacing = 1.6, size = 9, color = color, alpha = .5, va = 'center', ha = 'center')


	ax = subplot(122)
	color = (0,.25,.75)
	X = [mean([r['Date'] for r in data.sessions[s]['data'] if 'Sample_original' in r and r['Sample_original'] in ['ETH-3']]) for s in data.sessions]
	X = [x - min(X) for x in X]
	Y = [data.samples[f'ETH-3__{s}']['D47'] for s in data.sessions]
	sY = [data.samples[f'ETH-3__{s}']['SE_D47'] for s in data.sessions]
	eY = [sy*data.t95 for sy in sY]
	errorbar(X, Y, eY, ls = 'None', marker = 'None', ecolor = color, elinewidth = 1, capthick = 1, capsize = 3)
	plot(X, Y, 'wo', mec = color, mew = 1)
	axhline(0.6132, color = color, lw = 2, alpha = .25)
	text(280, 0.6132-0.0001, 'InterCarb\nvalue', linespacing = 1.6, size = 9, color = color, alpha = .5, va = 'center', ha = 'center')

	ax.yaxis.set_major_locator(MultipleLocator(.01))
	xlabel('Time (days)')
	ylabel('Δ$_{47}$ average of ETH-3\nfor each session (CDES, ‰)', labelpad = 10)
	grid(alpha = 0.2, axis = 'y')
	x1,x2,y1,y2 = axis()
	h = 0.03
	axis([x1,x2,(y1+y2-h)/2,(y1+y2+h)/2])

	savefig(filename)
	close(fig)

def plot_ETH3_drift(data, filename):
	fig = figure(figsize = (4,4))
	subplots_adjust(.25,.2,.9,.85, .4, .4)
	
	ax = subplot(111)
	color = (0,.25,.75)
	X = [mean([r['Date'] for r in data.sessions[s]['data'] if 'Sample_original' in r and r['Sample_original'] in ['ETH-3']]) for s in data.sessions]
	X = [x - min(X) for x in X]
	Y = [data.samples[f'ETH-3__{s}']['D47'] for s in data.sessions]
	sY = [data.samples[f'ETH-3__{s}']['SE_D47'] for s in data.sessions]
	eY = [sy*data.t95 for sy in sY]
	errorbar(X, Y, eY, ls = 'None', marker = 'None', ecolor = color, elinewidth = 1, capthick = 1, capsize = 3)
	plot(X, Y, 'wo', mec = color, mew = 1)
	axhline(0.6132, color = color, lw = 2, alpha = .25)
	text(280, 0.6132-0.0001, 'InterCarb\nvalue', linespacing = 1.6, size = 9, color = color, alpha = .5, va = 'center', ha = 'center')

	ax.yaxis.set_major_locator(MultipleLocator(.01))
	xlabel('Time (days)')
	ylabel('Δ$_{47}$ average of ETH-3\nfor each session (CDES 90, ‰)', labelpad = 10)
	# we use "CDES 90" in the paper, because it is equivalent to I-CDES ignoring ETH-3 and using gas constraints (see dicusiion in the paper)
	grid(alpha = 0.2, axis = 'y')
	x1,x2,y1,y2 = axis()
	h = 0.03
	axis([x1,x2,(y1+y2-h)/2,(y1+y2+h)/2])

	savefig(filename)
	close(fig)


def plot_residuals(data, filename, title_txt, _ylabel = None, with_sessions = True):
	fig = figure(figsize = (8,4))
	subplots_adjust(.1, .15, .8, .9)
	X0 = min([r['Date'] for r in data])
	labels = []
	for sample in data.samples:
		X = [r['Date'] - X0 for r in data if r['Sample'] == sample]
		Y = [1000 * (r['D47'] - data.samples[sample]['D47']) for r in data if r['Sample'] == sample]
		if 'HG' in sample:
			color = (1,0,0)
			marker = 'v'
			label = None if 'HG' in labels else 'HG'
		elif '25G' in sample:
			color = (0,.7,0)
			marker = '^'
			label = None if '25G' in labels else '25G'
		elif 'ETH-3' in sample:
			color = (0,.67,.67)
			marker = 'D'
			label = None if 'ETH-3' in labels else 'ETH-3'
		elif (('ETH-1' in sample or 'ETH-2' in sample) and ('-1100' not in sample)):
			color = (0,0,1)
			marker = 's'
			label = None if 'ETH-1/2' in labels else 'ETH-1/2'
		else:
			color = (.33,.33,.33)
			marker = 'o'
			label = None if 'other' in labels else 'other'
		labels += [label]
		plot(X, Y, ls = 'None', marker = marker, mec = color, mfc = (1,1,1,0), mew = .75, label = label, ms = 4)

	if with_sessions:
		for session, y in zip(data.sessions, [36, 32, 36, 33, 36, 33, 30, 27]):
			X = [r['Date'] - X0 for r in data if r['Session'] == session]
			x1, x2 = min(X), max(X)
			plot([x1, x2], [y]*2, 'k-', lw = 4, alpha = .25, solid_capstyle = 'butt')
			if session[-1] not in 'bcd':
				text((x1+x2)/2, y, f'{session}\n', va = 'center', ha = 'center', size = 8, linespacing = 2)
			else:
				text(x2, y, f' {session[-2:]}', va = 'center', ha = 'left', size = 8, linespacing = 2)
		
	
	axhspan(-data.repeatability['r_D47']*1000, data.repeatability['r_D47']*1000, color = 'k', alpha = .05, lw = 1)
	text(axis()[1], data.repeatability['r_D47']*1000, f"   SD = {data.repeatability['r_D47']*1000:.1f} ppm", size = 9, alpha = .75, va = 'center')

	axhspan(-data.repeatability['r_D47']*1000*data.t95, data.repeatability['r_D47']*1000*data.t95, color = 'k', alpha = .05, lw = 1)
	text(axis()[1], data.repeatability['r_D47']*1000*data.t95, f"   95% CL: ± {data.repeatability['r_D47']*1000*data.t95:.1f} ppm", size = 9, alpha = .75, va = 'center')

	axhline(0, color = 'k', lw = .5)

	if _ylabel is None:
		ylabel('Δ$_{47}$ residuals from long-term average (ppm)')
	else:
		ylabel(_ylabel)
	xlabel('Time (days)')
	title(title_txt)
	legend(loc = 'lower left', bbox_to_anchor = (1.01, 0), fontsize = 8)
	savefig(filename)
	close(fig)
	

def rawdata_import():
	keychange = { # for spreadsheet conversion
		'Sample': 'Sample',
		'ID': 'Date',
		'δ45 WG': 'd45',
		'δ46 WG': 'd46',
		'δ47 WG': 'd47',
		'δ48 WG': 'd48',
		'δ49 WG': 'd49',
		}

	rawdata = []
	for filename in sorted(glob('rawdata/Session*.xlsx')):
		session = 'Session_' + filename.split('rawdata/Session ')[1][:2].strip()
# 		print(f'Reading book {filename}')
		book = xlrd.open_workbook(filename)
		for s in range(1,len(book.sheets())):
			sheet = book.sheet_by_index(s)
# 			print(f'  Reading sheet {sheet.name}')
			keys = [cell.value for cell in sheet.row(0)]
			keyindex = {i:k for i,k in enumerate(keys)}
			for r in range(2, sheet.nrows-1):
				row = sheet.row(r+1)
				if row[0].value != '':
					rawdata += [{
						**{'Session': session},
						**{keychange[keyindex[i]]:cell.value
							for i,cell in enumerate(row)
							if keyindex[i] in ['Sample', 'δ45 WG', 'δ46 WG', 'δ47 WG', 'δ48 WG', 'δ49 WG', 'ID']}
						}]
				else:
					break

	rawdata = sorted(rawdata, key = lambda r: int(r['Session'].split('_')[-1].replace('a','1').replace('b','2').replace('c','3').replace('d','4'))*1e9 + r['Date'])

	for k,r in enumerate(rawdata):
		r['Sample'] = r['Sample'].strip()
		if 'HG' in r['Sample'] or r['Sample'] == 'hg50':
			r['Sample'] = 'HG'
		elif '25G' in r['Sample']:
			r['Sample'] = '25G'
		elif 'DVH' in r['Sample']:
			r['Sample'] = 'DVH-2'
		elif r['Sample'] in ['66-465', '66-645', 'MV 66 4 65']:
			r['Sample'] = '66-465'
		elif 'BUK' in r['Sample']:
			r['Sample'] = 'BUK-' + r['Sample'][-1]
		elif r['Sample'][:2] == 'JR':
			r['Sample'] = 'JR'
		elif r['Sample'][:2] == 'MD':
			r['Sample'] = 'MD-' + r['Sample'][-1]
		elif r['Sample'][:2] == 'CA':
			r['Sample'] = 'CA-' + r['Sample'][2:]
		elif r['Sample'][:2] == 'CM':
			r['Sample'] = 'CM-' + r['Sample'][2:]
		elif r['Sample'] == 'SK':
			r['Sample'] = 'GU-1'
		elif r['Sample'][:2] == 'DH':
			r['Sample'] = 'DHC2-8'
		elif r['Sample'] == 'Dest+0':
			r['Sample'] = '25G'
		elif r['Sample'] == 'MHD1':
			r['Sample'] = 'MHD-1'
		elif r['Sample'] == 'KAK1':
			r['Sample'] = 'KAK-1'
		elif r['Sample'] == 'FAS2':
			r['Sample'] = 'FAS-2'
		elif r['Sample'] == 'SZE3':
			r['Sample'] = 'SZE-3'
		elif 'LGB' in r['Sample']:
			r['Sample'] = 'LGB-2'
		elif '143a' in r['Sample']:
			r['Sample'] = 'Mv-143b'
		elif 'PG1' in r['Sample']:
			r['Sample'] = 'PC1_2005'
		elif r['Sample'] == 'ETH1-1100':
			r['Sample'] = 'ETH-1-1100'
		elif r['Sample'] == 'ETH2-1100':
			r['Sample'] = 'ETH-2-1100'
		elif 'ETH' in r['Sample']:
			if '1' in r['Sample']:
				r['Sample'] = 'ETH-1'
			elif '2' in r['Sample']:
				r['Sample'] = 'ETH-2'
			elif '3' in r['Sample']:
				r['Sample'] = 'ETH-3'
# 		if r['Session'] == 'Session_2':
# 			if r['Date'] < 43795:
# 				r['Session'] = r['Session'] + 'a'
# 			else:
# 				r['Session'] = r['Session'] + 'b'
# 		if r['Session'] == 'Session_1':
# 			if k > 75:
# 				r['Session'] = 'Session_1b'
# 			else:
# 				r['Session'] = 'Session_1a'
		r['TimeTag'] = r['Date']
# 		r['Session'] = {
# 			'Session_1a': 'Session_1',
# 			'Session_1b': 'Session_2',
# 			'Session_2a': 'Session_3',
# 			'Session_2b': 'exclude',
# 			'Session_3': 'Session_4',
# 			'Session_4': 'Session_5_1',
# 			'Session_5': 'Session_5_2',
# 			'Session_6': 'Session_5_3',
# 			'Session_7': 'Session_5_4',
# 			}[r['Session']]

	rawdata = [r for r in rawdata if r['Session'] != 'exclude']

# 	print(f'Finished importing {len(rawdata)} analyses.')
# 	for s in sorted({r['Sample'] for r in rawdata}): print(s)
	return rawdata

def cdes_process(_rawdata_):
	rawdata = deepcopy(_rawdata_)

	basedir = 'CDES'
	if not os.path.exists(basedir):
		os.makedirs(basedir)

	D47data.Nominal_D47 = {
		'25G': fCO2eqD47_Petersen(25),
		'HG': fCO2eqD47_Petersen(1000),
		}
	D47data.LEVENE_REF_SAMPLE = '25G'
	data = D47data(rawdata)

	fig = figure(figsize = (6,4))
	subplots_adjust(0.02, 0.03, 0.88, 0.85)
	ax = data.plot_distribution_of_analyses(vs_time = False, output = 'ax')
	savefig('Distribution_of_analyses.pdf')
	close(fig)

	dir = f'{basedir}/no_drift_corrections'

	data.wg()
	data.crunch()
	data.split_samples([s for s in data.unknowns], 'by_session')
	data.standardize()
	data.table_of_samples(dir = dir, filename = 'subsamples.csv')
	data.unsplit_samples()
	data.table_of_samples(dir = dir, filename = 'samples.csv')
	plot_residuals(data, filename = f'{dir}/D47_residuals.pdf', title_txt = 'Δ$_{47}$ residuals (CDES, no drift corrections)')

	### Now correct drifts:
	dir = f'{basedir}/with_drift_corrections'
	data.sessions['Session_2']['wg_drift'] = True
	data.sessions['Session_3']['wg_drift'] = True
	data.sessions['Session_4']['wg_drift'] = True
	data.split_samples([s for s in data.unknowns], 'by_session')
	data.standardize()
	data.table_of_samples(dir = dir, filename = 'subsamples.csv')
	plot_ETH_drift(data, filename = f'{dir}/drift_of_ETH_CDES.pdf')

	data.unsplit_samples()
	data.table_of_samples(dir = dir, filename = 'samples.csv')
	plot_residuals(data, filename = f'{dir}/D47_residuals.pdf', title_txt = 'Δ$_{47}$ residuals (CDES, with drift corrections)')


def cdes_process48(_rawdata_):
	rawdata = deepcopy(_rawdata_)

	basedir = 'CDES'
	if not os.path.exists(basedir):
		os.makedirs(basedir)

	D47data.Nominal_D47 = {
		'25G': 0.345,
		'HG':  0.000,
		}
	D47data.LEVENE_REF_SAMPLE = '25G'
	data = D47data(rawdata)

	dir = f'{basedir}/no_drift_corrections'

	data.wg()
	data.crunch()
	for r in data:
		r['d47'] = r['d48']
		r['D47raw'] = r['D48raw']
	data.split_samples([s for s in data.unknowns], 'by_session')
	data.standardize()
	data.unsplit_samples()
	plot_residuals(data, filename = f'{dir}/D48_residuals.pdf', title_txt = 'Δ$_{48}$ residuals (CDES, no drift corrections)', _ylabel = 'Δ$_{48}$ residuals from long-term average (ppm)', with_sessions = False)


def icdes_process(_rawdata_):

	basedir = 'I-CDES'
	if not os.path.exists(basedir):
		os.makedirs(basedir)

	D47data.Nominal_D47 = {
		'ETH-1':   0.2052,
		'ETH-2':   0.2085,
		}
	D47data.LEVENE_REF_SAMPLE = 'ETH-1'

	data = D47data(deepcopy(_rawdata_))

	dir = f'{basedir}/with_drift_corrections'

	data.sessions['Session_2']['wg_drift'] = True
	data.sessions['Session_3']['wg_drift'] = True
	data.sessions['Session_4']['wg_drift'] = True
	data.wg()
	data.crunch()
	data.split_samples(grouping = 'by_session')
	data.standardize(constraints = {
		f'D47_25G__{pf(s)}': f'D47_HG__{pf(s)} + {fCO2eqD47_Petersen(25)-fCO2eqD47_Petersen(1000)}'
		for s in data.sessions
		})
	data.table_of_sessions(verbose = False, dir = dir, filename = 'sessions.csv')
# 	data.table_of_samples(dir = dir, filename = 'subsamples.csv')

	data = D47data(deepcopy(_rawdata_))

	data.sessions['Session_2']['wg_drift'] = True
	data.sessions['Session_3']['wg_drift'] = True
	data.sessions['Session_4']['wg_drift'] = True
	data.wg()
	data.crunch()
	data.split_samples(['HG', '25G', 'ETH-3'], 'by_session')
	data.standardize(constraints = {
		f'D47_25G__{pf(s)}': f'D47_HG__{pf(s)} + {fCO2eqD47_Petersen(25)-fCO2eqD47_Petersen(1000)}'
		for s in data.sessions
		})

	data.summary()
	data.plot_sessions(dir = 'sessions')
	data.plot_residuals(filename = 'D47residuals.pdf')
	data.summary(dir = 'tables', verbose = False)
	data.table_of_sessions(dir = 'tables', verbose = False)
	data.table_of_samples(dir = 'tables', verbose = False)
	data.table_of_analyses(dir = 'tables', verbose = False)

# 	data.table_of_samples(dir = dir, filename = 'samples.csv')
# 	plot_residuals(data, filename = f'{dir}/D47_residuals_with_drift_corrections.pdf', title_txt = 'Δ$_{47}$ residuals (I-CDES)')
# 	plot_ETH3_drift(data, filename = f'{dir}/drift_of_ETH3_ICDES.pdf')
	
	calib_data = {
		'LGB-2':      {'T':    7.9, 'sT':  0.2},
		'DVH-2':      {'T':   33.7, 'sT':  0.2},
		'DHC2-8':     {'T':   33.7, 'sT':  0.2},
		'CA-120':     {'T':  120.0, 'sT':  2.0},
		'CA-170':     {'T':  170.0, 'sT':  2.0},
		'CA-200':     {'T':  200.0, 'sT':  2.0},
		'CA-250A':    {'T':  250.0, 'sT':  2.0},
		'CA-250B':    {'T':  250.0, 'sT':  2.0},
		'CM-351':     {'T':  726.85, 'sT': 10.0},
		'ETH-1-1100': {'T': 1100.0, 'sT': 10.0},
		'ETH-2-1100': {'T': 1100.0, 'sT': 10.0},
		}

	calib_samples = sorted(calib_data.keys())

	# covar between DHC2-8 and DVH-2
	sT = diag([calib_data[s]['sT'] for s in calib_samples])**2
	j,k = calib_samples.index('DVH-2'), calib_samples.index('DHC2-8')
	sT[j,k], sT[k,j] = sT[j,j], sT[j,j]

	C = D47calib(
		samples = calib_samples,
		D47 = [data.samples[s]['D47'] for s in calib_samples],
		sD47 = [[data.sample_D4x_covar(s1, s2) for s1 in calib_samples] for s2 in calib_samples],
		T = [calib_data[s]['T'] for s in calib_samples],
		sT = sT,
		description = 'Fiebig et al. (2021) in I-CDES with additional constraints from 100 °C and 25 °C equilibrated CO2',
		label = 'Fiebig et al. (2021)',
		degrees = [0,1,2],
		)

	C.export('fiebig_2021', '../fiebig_2021.py')
	C.export_data('fiebig_2021_data.csv', label = True, T_correl = True, D47_correl = True)	

if __name__ == '__main__':

	rawdata = rawdata_import()
# 	cdes_process(rawdata)
# 	cdes_process48(rawdata)
	icdes_process(rawdata)

