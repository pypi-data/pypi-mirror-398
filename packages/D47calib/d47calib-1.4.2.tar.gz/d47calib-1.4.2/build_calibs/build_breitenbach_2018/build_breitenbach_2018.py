#! /usr/bin/env python3
'''
Data reprocessing in I-CDES for:
Breitenbach et al. (2018)
https://doi.org/10.1016/j.gca.2018.03.010
'''

__author__    = 'Mathieu Daëron'
__contact__   = 'daeron@lsce.ipsl.fr'
__copyright__ = 'Copyright (c) 2020 Mathieu Daëron'
__license__   = 'Modified BSD License - https://opensource.org/licenses/BSD-3-Clause'
__date__      = '2021-03-22'
__version__   = '0.1'

from datetime import date
from copy import deepcopy
import xlrd
from glob import glob
from D47calib import D47calib
from D47crunch import *
# from D47crunch_snapshot import *
from matplotlib.ticker import MultipleLocator
from pylab import *

CUT_SESSIONS = True

def plot_ETH_drift(data, filename):
	fig = figure(figsize = (8,4))
	subplots_adjust(.125,.2,.95,.85, .4, .4)
	
	ax = subplot(121)
	color = (.75,0,.25)
	X = [mean([r['TimeTag'] for r in data.sessions[s]['data'] if 'Sample_original' in r and r['Sample_original'] in ['ETH-1', 'ETH-2']]) for s in data.sessions]
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
	X = [mean([r['TimeTag'] for r in data.sessions[s]['data'] if 'Sample_original' in r and r['Sample_original'] in ['ETH-3']]) for s in data.sessions]
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
	X = [mean([r['TimeTag'] for r in data.sessions[s]['data'] if 'Sample_original' in r and r['Sample_original'] in ['ETH-3']]) for s in data.sessions]
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


# def plot_residuals(data, filename, title_txt, _ylabel = None, with_sessions = False):
# 	fig = figure(figsize = (8,4))
# 	subplots_adjust(.1, .15, .8, .9)
# 	X0 = min([r['TimeTag'] for r in data])
# 	labels = []
# 	for sample in data.samples:
# 		X = [r['TimeTag'] - X0 for r in data if r['Sample'] == sample]
# 		Y = [1000 * (r['D47'] - data.samples[sample]['D47']) for r in data if r['Sample'] == sample]
# 		if 'HG' in sample:
# 			color = (1,0,0)
# 			marker = 'v'
# 			label = None if 'HG' in labels else 'HG'
# 		elif '25G' in sample:
# 			color = (0,.7,0)
# 			marker = '^'
# 			label = None if '25G' in labels else '25G'
# 		elif 'ETH-3' in sample:
# 			color = (0,.67,.67)
# 			marker = 'D'
# 			label = None if 'ETH-3' in labels else 'ETH-3'
# 		elif (('ETH-1' in sample or 'ETH-2' in sample) and ('-1100' not in sample)):
# 			color = (0,0,1)
# 			marker = 's'
# 			label = None if 'ETH-1/2' in labels else 'ETH-1/2'
# 		else:
# 			color = (.33,.33,.33)
# 			marker = 'o'
# 			label = None if 'other' in labels else 'other'
# 		labels += [label]
# 		plot(X, Y, ls = 'None', marker = marker, mec = color, mfc = (1,1,1,0), mew = .75, label = label, ms = 4)
# 
# 	if with_sessions:
# 		for session, y in zip(data.sessions, [36, 32, 36, 33, 36, 33, 30, 27]):
# 			X = [r['TimeTag'] - X0 for r in data if r['Session'] == session]
# 			x1, x2 = min(X), max(X)
# 			plot([x1, x2], [y]*2, 'k-', lw = 4, alpha = .25, solid_capstyle = 'butt')
# 			if session[-1] not in 'bcd':
# 				text((x1+x2)/2, y, f'{session}\n', va = 'center', ha = 'center', size = 8, linespacing = 2)
# 			else:
# 				text(x2, y, f' {session[-2:]}', va = 'center', ha = 'left', size = 8, linespacing = 2)
# 		
# 	
# 	axhspan(-data.repeatability['r_D47']*1000, data.repeatability['r_D47']*1000, color = 'k', alpha = .05, lw = 1)
# 	text(axis()[1], data.repeatability['r_D47']*1000, f"   SD = {data.repeatability['r_D47']*1000:.1f} ppm", size = 9, alpha = .75, va = 'center')
# 
# 	axhspan(-data.repeatability['r_D47']*1000*data.t95, data.repeatability['r_D47']*1000*data.t95, color = 'k', alpha = .05, lw = 1)
# 	text(axis()[1], data.repeatability['r_D47']*1000*data.t95, f"   95% CL: ± {data.repeatability['r_D47']*1000*data.t95:.1f} ppm", size = 9, alpha = .75, va = 'center')
# 
# 	axhline(0, color = 'k', lw = .5)
# 
# 	if _ylabel is None:
# 		ylabel('Δ$_{47}$ residuals from long-term average (ppm)')
# 	else:
# 		ylabel(_ylabel)
# 	xlabel('Time (days)')
# 	title(title_txt)
# 	legend(loc = 'lower left', bbox_to_anchor = (1.01, 0), fontsize = 8)
# 	savefig(filename)
# 	show()
# 	close(fig)
	

def rawdata_import():
	keychange = { # for spreadsheet conversion
		'SA/STD': 'Sample',
		'Run': 'Session',
		'Date+Time': 'TimeTag',
		}

	rawdata = []

	filename = 'rawdata/1-s2.0-S0016703718301613-mmc9.xlsx'
# 	print(f'Reading book {filename}')
	book = xlrd.open_workbook(filename)
	sheet = book.sheet_by_index(0)
# 	print(f'  Reading sheet {sheet.name}')
	keys = [cell.value for cell in sheet.row(0)]
	for r in range(0, sheet.nrows-1):
		row = sheet.row(r+1)
		if row[0].value != '':
			rawdata += [{
				**{(keychange[k] if k in keychange else k):cell.value
					for k,cell in zip(keys,row)
					if k in ['SA/STD', 'd45', 'd46', 'd47', 'd48', 'Run', 'Date+Time']}
				}]

	filename = 'rawdata/1-s2.0-S0016703718301613-mmc6.xlsx'
# 	print(f'Reading book {filename}')
	book = xlrd.open_workbook(filename)
	sheet = book.sheet_by_index(0)
# 	print(f'  Reading sheet {sheet.name}')
	keys = [cell.value for cell in sheet.row(0)]
	for r in range(0, sheet.nrows-1):
		row = sheet.row(r+1)
		if row[0].value != '' and row[7].value == '':
			rawdata += [{
				**{(keychange[k] if k in keychange else k):cell.value
					for k,cell in zip(keys,row)
					if k in ['SA/STD', 'd45', 'd46', 'd47', 'd48', 'Run', 'Date+Time']}
				}]

	for r in rawdata:
		if r['Sample'] == 'BaerPool1':
			r['Sample'] = 'BSP-1'
		elif r['Sample'] == 'DSP1':
			r['Sample'] = 'DSP-1'
		elif r['Sample'] == 'GCP-1':
			r['Sample'] = 'GPC-1'
		elif 'NAICA' in r['Sample']:
			r['Sample'] = 'NAICA-1'
		elif 'OWB' in r['Sample']:
			r['Sample'] = 'OWB-1'
		elif 'ETH1' in r['Sample']:
			r['Sample'] = 'ETH-1'
		elif 'ETH2' in r['Sample']:
			r['Sample'] = 'ETH-2'
		elif 'ETH3' in r['Sample']:
			r['Sample'] = 'ETH-3'
		elif 'ETH4' in r['Sample']:
			r['Sample'] = 'ETH-4'
		if isinstance(r['TimeTag'], float):
			r['TimeTag'] = xlrd.xldate_as_tuple(r['TimeTag'], 0)
		else:
			try:
				d,m,y = r['TimeTag'].split('.')
			except:
				try:
					m,d,y = r['TimeTag'].split('/')
				except:
					print([r['TimeTag']])
					exit()
			r['TimeTag'] = (2000+int(y), int(m), int(d), 0, 0, 0)
		r['TimeTag'] = (date(*r['TimeTag'][:3]) - date(2015, 1, 1)).days - 228

		if CUT_SESSIONS:
			if r['TimeTag'] < 33:
				r['Session'] = 'Session_A'
			elif r['TimeTag'] < 150:
				r['Session'] = 'Session_B'
			elif r['TimeTag'] < 260:
				r['Session'] = 'Session_C'
			else:
				r['Session'] = 'Session_D'
		else:
			r['Session'] = 'Session_1' if r['Session'] < 70 else 'Session_2'

# 	for s in sorted({r['Sample'] for r in rawdata}):
# 		print(s)		

	rawdata = sorted(rawdata, key = lambda r: r['TimeTag'])

	ignore_days = [211, 212, 283, 294, 295, 296, 298][:]
	rawdata = [r for r in rawdata if r['TimeTag'] not in ignore_days]

# 	ignore_sessions = [
# 		s for s in sorted({r['Session'] for r in rawdata})
# 		if len({r['Sample'] for r in rawdata if r['Session'] == s and 'ETH-' in r['Sample']})<3
# 		]
# 	rawdata = [r for r in rawdata if r['Session'] not in ignore_sessions]

	for session in sorted({r['Session'] for r in rawdata}):
		samples = sorted({r['Sample'] for r in rawdata if r['Session'] == session})
# 		print('\t'.join([session, *samples]))

# 	for r in rawdata:
# 		print(r)

	return rawdata
	


def icdes_process(_rawdata_):

	basedir = 'I-CDES'
	if not os.path.exists(basedir):
		os.makedirs(basedir)

	data = D47data(deepcopy(_rawdata_))
	ignore = ['876', '880', '882', '883', '1101', '1102', '1103', '1104', '1105', '1106', '1107', '1122', '1123', '1124', '1125', '1126', '1127', '1128', '1129', '1130', '1131', '1132', '1133', '1148', '1149', '1150', '1151']
	data = D47data([r for r in data if r['UID'] not in ignore])

	dir = f'{basedir}'

	if CUT_SESSIONS:
		data.sessions['Session_B']['wg_drift'] = True

	data.wg()
	data.crunch()
# 	print([r['UID'] for r in data if r['D47raw'] < -1])
# 	exit()

# 	hist([r['D47raw'] for r in data])
# 	show()

# 	data.split_samples(grouping = 'by_session')
	data.standardize()
	data.summary()

	data.table_of_sessions(verbose = False, dir = dir, filename = 'sessions.csv')
	data.table_of_samples(dir = dir, filename = 'samples.csv')
	data.table_of_analyses(dir = dir, filename = 'analyses.csv')
	data.plot_distribution_of_analyses(dir = dir, filename = 'distribution_of_analyses.pdf')

	data.plot_residuals(dir = dir, filename = 'D47_residuals_with_drift_corrections.pdf')

	calib_data = {
		'BSP-1':     {'T':    8.9, 'sT':  0.5},
		'DSP-1':     {'T':    3.2, 'sT':  0.5},
		'GPC-1':     {'T':   24.5, 'sT':  0.5},
		'MCP-1':     {'T':   18.6, 'sT':  0.5},
		'NAICA-1':   {'T':   47.0, 'sT':  0.5},
		'OWB-1':     {'T':    9.1, 'sT':  0.5},
		}

	calib_samples = sorted(calib_data.keys())

	sT = diag([calib_data[s]['sT'] for s in calib_samples])**2

	C = D47calib(
		samples = calib_samples,
		D47 = [data.samples[s]['D47'] for s in calib_samples],
		sD47 = [[data.sample_D4x_covar(s1, s2) for s1 in calib_samples] for s2 in calib_samples],
		T = [calib_data[s]['T'] for s in calib_samples],
		sT = sT,
		description = 'Breitenbach et al. (2018) cave pearls in I-CDES',
		label = 'Breitenbach et al. (2018) cave pearls',
		degrees = [0,2],
		)

	C.export('breitenbach_2018', '../breitenbach_2018.py')
	C.export_data('breitenbach_2018_data.csv', label = True, T_correl = True, D47_correl = True)
	
if __name__ == '__main__':

	rawdata = rawdata_import()
	
# 	samplerank = {s:k for k,s in enumerate(sorted({r['Sample'] for r in rawdata}))}
# 	sessions = sorted({r['Session'] for r in rawdata})
# 	for session in sessions:
# 		print(
# 			session,
# 			min([r['TimeTag'] for r in rawdata if r['Session'] == session]),
# 			max([r['TimeTag'] for r in rawdata if r['Session'] == session]),
# 			)
# 	sessioncolor = {s:'r' if k%2 else 'b' for k,s in enumerate(sessions)}
# 
# 	fig = figure()
# 	ax = subplot(111)
# 	ax.xaxis.axis_date()
# 
# 	for k,r in enumerate(rawdata):
# 		plot(r['TimeTag']+k/1000, samplerank[r['Sample']], 'x', mec = sessioncolor[r['Session']], mew = 0.5)
# 
# 	for s in samplerank:
# 		text(r['TimeTag'], samplerank[s], '  '+s, va = 'center')
# 
# # 	for name, x, y in sessionlimits:
# # 		axvspan(datetime.fromisoformat(x),datetime.fromisoformat(y), color = 'k', alpha = .15)
# 
# # 	yticks([])
# 
# 	show()
	
	icdes_process(rawdata)

