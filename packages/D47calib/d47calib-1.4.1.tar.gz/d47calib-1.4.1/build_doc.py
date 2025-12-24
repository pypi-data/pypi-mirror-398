#! /usr/bin/env uv run python
'''
Apply an arbitrary filter to each docstring
'''

from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path
import shutil
import pdoc



for code_input, code_output in [
	('code_examples/D47calib_init/example.py', 'code_examples/D47calib_init/output.txt'),
	('code_examples/D47calib_invT_xaxis/example_1.py', ''),
	('code_examples/D47calib_invT_xaxis/example_2.py', ''),
	]:

	with open(code_input) as fid:
		code = fid.read()

	f = StringIO()
	with redirect_stdout(f):
		exec(code)

	if code_output:
		with open(code_output, 'w') as fid:
			fid.write(f.getvalue())


substitutions = [
	('δ13C_VPDB', 'δ<sup>13</sup>C<sub>VPDB</sub>'),
	('δ18O_VPDB', 'δ<sup>18</sup>O<sub>VPDB</sub>'),
	('δ18O_VSMOW', 'δ<sup>18</sup>O<sub>VSMOW</sub>'),
	('δ13CVPDB', 'δ<sup>13</sup>C<sub>VPDB</sub>'),
	('δ18OVPDB', 'δ<sup>18</sup>O<sub>VPDB</sub>'),
	('δ18OVSMOW', 'δ<sup>18</sup>O<sub>VSMOW</sub>'),
	('δ13C', 'δ<sup>13</sup>C'),
	('δ18O', 'δ<sup>18</sup>O'),
	('12C', '<sup>12</sup>C'),
	('13C', '<sup>13</sup>C'),
	('16O', '<sup>16</sup>O'),
	('17O', '<sup>17</sup>O'),
	('18O', '<sup>18</sup>O'),
	('δ4x', 'δ<sub>4x</sub>'),
	('δ45', 'δ<sub>45</sub>'),
	('δ46', 'δ<sub>46</sub>'),
	('δ47', 'δ<sub>47</sub>'),
	('δ48', 'δ<sub>48</sub>'),
	('δ49', 'δ<sub>49</sub>'),
	('Δ4x', 'Δ<sub>4x</sub>'),
	('Δ4x', 'Δ<sub>4x</sub>'),
	('Δ47', 'Δ<sub>47</sub>'),
	('Δ48', 'Δ<sub>48</sub>'),
	('Δ49', 'Δ<sub>49</sub>'),
	('χ2', 'χ<sup>2</sup>'),
	('χ^2', 'χ<sup>2</sup>'),
	('CO2', 'CO<sub>2</sub>'),
	('T47', 'T<sub>47</sub>'),
	]

from matplotlib import pyplot as ppl
from D47calib import *

# mycalib = D47calib(
#         samples     = ['FOO', 'BAR'],
#         T           = [0.   , 25.  ],
#         D47         = [0.7  , 0.6  ],
#         sT          = 1.,
#         sD47        = 0.01,
#         regress_now = True,
#         )
# T, sT = mycalib.T47(D47 = 0.650) # yields T = 11.7, sT = 1.9
# print(T, sT)


shutil.move(
	'./example_invT_xaxis_1.png',
	'docs/example_invT_xaxis_1.png',
	)
shutil.move(
	'./example_invT_xaxis_2.png',
	'docs/example_invT_xaxis_2.png',
	)


calib = ogls_2023

# fig = ppl.figure(figsize = (5,3))
# ppl.subplots_adjust(bottom = .25, left = .15)
# ax = calib.invT_xaxis()
# ax.set_xlim((0, 270**-2))
# ppl.savefig('docs/example_invT_xaxis_2.png', dpi = 100)
# ppl.close(fig)

calib.xpower = 4
fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
ax = calib.invT_xaxis(Ti = [1000, 100, 50, 25, 0])
ax.set_xlim((0, 270**-4))
ppl.savefig('docs/example_invT_xaxis_4.png', dpi = 100)
ppl.close(fig)
calib.xpower = 2

calib = huyghe_2022

fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
calib.invT_xaxis(Ti = [0,10,25])
calib.plot_data(label = True)
ppl.legend()
ppl.ylabel('$Δ_{47}$ (‰ I-CDES)')
ppl.savefig('docs/example_plot_data.png', dpi = 100)
ppl.close(fig)


fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
calib.invT_xaxis(Ti = [0,10,25])
calib.plot_error_bars(alpha = .4)
calib.plot_data(label = True)
ppl.ylabel('$Δ_{47}$ (‰ I-CDES)')
ppl.legend()
ppl.savefig('docs/example_plot_error_bars.png', dpi = 100)

fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
calib.invT_xaxis(Ti = [0,10,25])
calib.plot_error_ellipses(alpha = .4)
calib.plot_data(label = True)
ppl.ylabel('$Δ_{47}$ (‰ I-CDES)')
ppl.legend()
ppl.savefig('docs/example_plot_error_ellipses.png', dpi = 100)

fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
calib.invT_xaxis(Ti = [0,10,25])
calib.plot_bff(label = True, dashes = (8,2,2,2))
calib.plot_data()
ppl.ylabel('$Δ_{47}$ (‰ I-CDES)')
ppl.legend()
ppl.savefig('docs/example_plot_bff.png', dpi = 100)

fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
calib.invT_xaxis(Ti = [0,10,25])
calib.plot_bff_ci(alpha = .15)
calib.plot_bff(label = True, dashes = (8,2,2,2))
calib.plot_data()
ppl.ylabel('$Δ_{47}$ (‰ I-CDES)')
ppl.legend()
ppl.savefig('docs/example_plot_bff_ci.png', dpi = 100)

import numpy as np
calib = ogls_2023

X = np.linspace(1473**-2, 270**-2)
D47, sD47 = calib.T47(T = X**-0.5 - 273.15)

fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
calib.invT_xaxis()
ppl.plot(X, 1000 * sD47, 'r-')
ppl.ylabel('Calibration SE on $Δ_{47}$ values (ppm)')
ppl.savefig('docs/example_SE47.png', dpi = 100)

calib = devils_laghetto_2023
fig = ppl.figure(figsize = (3.5,4))
ppl.subplots_adjust(bottom = .2, left = .15)
calib.plot_T47_errors(
	calibname = 'Devils Laghetto calibration',
	Nr = [1,2,4,16],
	Tmin  =0,
	Tmax = 40,
	)
ppl.savefig('docs/example_SE_T.png', dpi = 100)

huyghe_2022.export_data(
			csvfile = 'docs/example_export_data.csv',
			D47_correl = True,
			)

with open('docs/example_export_data.csv') as fid:
	lines = fid.readlines()
N = len(lines[0].split(','))
lines = [lines[0]] + [','.join(['----' for _ in range(N)])] + lines[1:]
for k in range(len(lines)):
	lines[k] = '|' + lines[k].strip().replace(',', '|') + '|'
with open('docs/example_export_data.md', 'w') as fid:
	fid.write('<style>td, th {font-size: 80%; line-height: 80%;}</style>\n\n' + '\n'.join(lines) + '\n\n')








		

def myfilter(docstr):
	work = docstr.split('```')
	for k in range(len(work)):
		if k:
			work[k] = work[k].lstrip('`')
		if k%2 == 0:
			work[k] = work[k].split('`')
			for j in range(len(work[k])):
				if not j%2:
					for x,y in substitutions:
						work[k][j] = work[k][j].replace(x,y)
			work[k] = '`'.join(work[k])
	return ('```'.join(work))

pdoc.render.env.filters['myfilter'] = myfilter
pdoc.render.configure(template_directory = 'pdoc_templates', search = False)

with open('docs/index.html', 'w') as fid:
	fid.write(pdoc.pdoc('D47calib'))

