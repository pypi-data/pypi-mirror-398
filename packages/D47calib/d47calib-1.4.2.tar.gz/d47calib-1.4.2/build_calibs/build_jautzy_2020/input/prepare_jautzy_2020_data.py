#! /usr/bin/env python3
'''
Clean up Jautzy et al. (2020) for processing with D47crunch
'''

from pylab import *
from csv import DictReader
from datetime import datetime

sessionlimits = [
	['2019-05a', '2019-04-29', '2019-05-12'],
	['2019-05b', '2019-05-13', '2019-05-19'],
	['2019-06a', '2019-05-30', '2019-06-09'],
	['2019-06b', '2019-06-09', '2019-06-16'],
	['2019-06c', '2019-06-16', '2019-06-25'],
	['2019-06d', '2019-06-25', '2019-07-02'],
	['2019-07', '2019-07-10', '2019-07-17'],
	['2019-10a', '2019-10-02', '2019-10-04'],
	['2019-10b', '2019-10-04', '2019-10-18'],
	['2019-10c', '2019-10-20', '2019-10-27'],
	['2019-11a', '2019-11-07', '2019-11-10'],
	['2019-11b', '2019-11-10', '2019-11-14'],
	['2019-12a', '2019-12-07', '2019-12-27'],
	['2019-12b', '2019-12-27', '2020-01-03'],
	]

with open('jautzy_2020_aspublished.csv') as fid:
	data = list(DictReader(fid))

samplerank = {s:k for k,s in enumerate(sorted({r['Sample'] for r in data}))}

for r in data:
	r['TimeTag'] = datetime.fromisoformat(f'{r["Date"].replace(" ","-")} {r["Time"]}')
	r['SessionColor'] = 'rgbkcmy'[int(r['Session'])]
	r['SampleRank'] = samplerank[r['Sample']]+1
	newsession = [a for a,x,y in sessionlimits if datetime.fromisoformat(x) < r['TimeTag'] and r['TimeTag'] < datetime.fromisoformat(y)]
	if newsession:
		r['NewSession'] = newsession[0]

with open('jautzy_2020_rawdata.csv', 'w') as fid:
	fid.write('Sample,UID,Session,d45,d46,d47,d48,d49')
	for r in data:
		if 'NewSession' in r:
			fid.write(f"\n{r['Sample']},{r['UID']},{r['NewSession']},{r['d45']},{r['d46']},{r['d47']},{r['d48']},{r['d49']}")
			

fig = figure()
ax = subplot(111)
ax.xaxis.axis_date()

for r in data:
	plot(r['TimeTag'], r['SampleRank'], 'x', mec = r['SessionColor'], mew = 0.5)

for s in samplerank:
	text(r['TimeTag'], samplerank[s]+1, '  '+s, va = 'center')

for name, x, y in sessionlimits:
	axvspan(datetime.fromisoformat(x),datetime.fromisoformat(y), color = 'k', alpha = .15)


yticks([])

# show()