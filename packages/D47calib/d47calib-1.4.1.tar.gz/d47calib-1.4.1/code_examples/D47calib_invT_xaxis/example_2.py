from matplotlib import pyplot as ppl
from D47calib import OGLS23 as calib

calib.xpower = 4

fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
ax = calib.invT_xaxis(Ti = [1000, 100, 50, 25, 0])
ax.set_xlim((0, 270**-4))
ppl.savefig('example_invT_xaxis_2.png', dpi = 100)