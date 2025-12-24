#! /usr/bin/env python3

from D47crunch import virtual_data, D47data
from csv import DictReader

args = dict(
	samples = [
		dict(Sample = 'ETH-1', N = 3),
		dict(Sample = 'ETH-2', N = 3),
		dict(Sample = 'ETH-3', N = 3),
		dict(Sample = 'FOO-1', N = 1,
			d13C_VPDB = -5., d18O_VPDB = -10.,
			D47 = 0.51, D48 = 0.15),
		dict(Sample = 'BAR-2', N = 1,
			d13C_VPDB = -15., d18O_VPDB = -2.,
			D47 = 0.68, D48 = 0.2),
		dict(Sample = 'BAZ-3', N = 1,
			d13C_VPDB = -10., d18O_VPDB = -5.,
			D47 = 0.59, D48 = 0.2),
		], rD47 = 0.010, rD48 = 0.030)

session1 = virtual_data(session = 'Session_01', **args, seed = 123)
session2 = virtual_data(session = 'Session_02', **args, seed = 1234)
# session3 = virtual_data(session = 'Session_03', **args, seed = 12345)
# session4 = virtual_data(session = 'Session_04', **args, seed = 123456)

D = D47data(session1 + session2)
D.crunch()
D.standardize()
D.table_of_analyses(verbose = False, save_to_file = True, dir = '.', filename = 'fullexample_rawdata.csv')

with open('fullexample_rawdata.csv') as f:
	data = list(DictReader(f))

fields = 'UID,Sample,Session,d45,d46,d47,d48,d49'.split(',')
sep = '\t'
with open('fullexample_rawdata.csv', 'w') as f:
	f.write(sep.join(fields) + '\n')
	f.write('\n'.join([
		sep.join([
			l[k] for k in fields])
		for l in data
		]))
