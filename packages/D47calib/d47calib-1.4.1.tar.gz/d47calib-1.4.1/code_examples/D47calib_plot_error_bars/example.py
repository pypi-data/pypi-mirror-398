from matplotlib import pyplot as ppl
from D47calib import huyghe_2022 as calib

fig = ppl.figure(figsize = (5,3))
ppl.subplots_adjust(bottom = .25, left = .15)
calib.invT_xaxis(Ti = [0,10,25])
calib.plot_error_bars(alpha = .4)
calib.plot_data(label = True)
ppl.ylabel('$Δ_{47}$ (‰ I-CDES)')
ppl.legend()
ppl.savefig('example_plot_error_bars.png', dpi = 100)
