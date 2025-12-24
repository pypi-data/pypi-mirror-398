from matplotlib import pyplot as ppl
from D47calib import huyghe_2022 as calib

fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
ax = calib.invT_xaxis(Ti = [-10,10,25])
ppl.gca().set_xlim([-10, 30])
calib.plot_data(label = True)
ppl.ylabel('$Δ_{47}$ (‰ I-CDES)')
ppl.legend()
ppl.savefig('example_plot_data.png', dpi = 100)
