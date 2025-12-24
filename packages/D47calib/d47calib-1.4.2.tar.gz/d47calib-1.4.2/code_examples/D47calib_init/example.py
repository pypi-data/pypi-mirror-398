from D47calib import D47calib

mycalib = D47calib(
        samples     = ['FOO', 'BAR'],
        T           = [0.   , 25.  ],
        D47         = [0.7  , 0.6  ],
        sT          = 1.,
        sD47        = 0.01,
        )

T, sT = mycalib.T47(D47 = 0.650)

print(f'T = {T:.1f}')
print(f'sT = {sT:.1f}')