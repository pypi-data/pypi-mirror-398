from matplotlib import pyplot as ppl
from D47calib import OGLS23 as calib

fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
ax = calib.invT_xaxis()
ax.set_xlim((0, 270**-2))
ppl.savefig('example_invT_xaxis_1.png', dpi = 100)
