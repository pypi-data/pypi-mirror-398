# 3. Command-line interface

`D47calib` also provides a command-line interface (CLI) for converting between Δ47 and temperature values, computing uncertainties for each computed value (and how these uncertainties are correlated with each other) from different sources (from calibration errors alone, from measurement errors alone, and from both). The computed uncertainties are provided as standard errors, correlation matrix and/or covariance matrix. Input and output files may be comma-separated, tab-separated, or printed out as visually aligned data columns.

## 3.1 Simple examples

Start with the simplest input file possible (here named `input.csv`):

```csv
D47
0.567
```

Then process it:

```txt
D47calib input.csv
```

This prints out:

```txt
  D47      T  T_SE_from_calib  T_correl_from_calib  T_SE_from_input  T_correl_from_input  T_SE_from_both  T_correl_from_both
0.567  34.20             0.38                1.000             0.00                1.000            0.38               1.000
```

* `T` is the temperature corresponding to a `D47` value of 0.567 ‰ according to the default calibration (`OGLS23`).
* `T_SE_from_calib` is the standard error on `T` from the calibration uncertainty
* `T_correl_from_calib` is the correlation matrix for the `T_SE_from_calib` values. Because here there is only one value, this is a 1-by-1 matrix with a single value of one, which is not very exciting.
* `T_SE_from_input` is the standard error on `T` from the measurement uncertainties on `D47`. Because these are not specified here, `T_SE_from_input` is equal to zero.
* `T_correl_from_input` is, predictably, the correlation matrix for the `T_SE_from_input` values. Because here there is only one value, this is a 1-by-1 matrix with a single value of one, you know the drill.
* `T_SE_from_both` is the standard error on `T` obtained by combining the two previously considered sources of uncertainties.
* `T_correl_from_both` is what you expect it to be if you've been reading so far. Can you guess why it is a 1-by-1 matrix with a single value of one?

### 3.1.1 Adding `D47` measurement uncertainties

This can be done by adding a column to `input.csv`:

```csv
D47,D47_SE
0.567,0.008
```

Because this is not very human-friendly, we'll replace the comma separators by whitespace. We'll also add a column listing sample names:

```csv
Sample   D47    D47_SE
FOO-1  0.567   0.008
```

Then process it. We're adding an option (`-i ' '`, or `--delimiter-in ' '`) specifying that we're no longer using commas but whitespaces as delimiters:

```txt
D47calib -i ' ' input.csv
```

This yields:

```txt
Sample   D47  D47_SE      T  T_SE_from_calib  T_correl_from_calib  T_SE_from_input  T_correl_from_input  T_SE_from_both  T_correl_from_both
FOO-1  0.567   0.008  34.20             0.38                1.000             2.91                1.000            2.94               1.000
```

You can see that `T_SE_from_input` is now much larger than `T_SE_from_calib`, and that the combined `T_SE_from_both` is equal to the quadratic sum of `T_SE_from_calib` and `T_SE_from_input`.

### 3.1.2 Converting more than one measurement

Let's add lines to our input file:

```csv
Sample   D47  D47_SE
FOO-1  0.567   0.008
BAR-2  0.575   0.009
BAZ-3  0.582   0.007
```

Which yields:

```txt
Sample   D47  D47_SE      T  T_SE_from_calib  T_correl_from_calib                T_SE_from_input  T_correl_from_input                T_SE_from_both  T_correl_from_both              
FOO-1  0.567   0.008  34.20             0.38                1.000  0.996  0.987             2.91                1.000  0.000  0.000            2.94               1.000  0.015  0.019
BAR-2  0.575   0.009  31.33             0.37                0.996  1.000  0.997             3.18                0.000  1.000  0.000            3.21               0.015  1.000  0.017
BAZ-3  0.582   0.007  28.89             0.36                0.987  0.997  1.000             2.42                0.000  0.000  1.000            2.44               0.019  0.017  1.000
```

A notable change are the 3-by-3 correlation matrices, which tell us how the `T` errors or these three measurements covary. `T_correl_from_calib` shows that the `T_SE_from_calib` errors are strongly correlated, because the three `D47` values are close to each other. `T_correl_from_input` indicates statistically independent `T_SE_from_input` errors. This may be true or not, but it is the expected result because our input file does not include any information on how the `D47_SE` errors may covary (see below how this additional info may be specified). Thus in this case `D47calib` assumes that the `D47` values are statistically independent (gentle reminder: this is often not the case, see below).

Note that because `T_SE_from_input` errors are much larger than `T_SE_from_calib` errors, the combined `T_SE_from_both` errors are only weakly correlated, as seen in `T_correl_from_both`.

### 3.1.3 Accounting for correlations in `D47` errors

Because [Δ47 measurements performed in the same analytical session(s) are not statistically independent](https://doi. org/10.1029/2020GC009588), we may add to `input.csv` a correlation matrix describing how `D47_SE` errors covary.

One simple way to compute this correlation matrix is to use the `save_D47_correl()` method from the `D47crunch` library ([PyPI](https://pypi.org/project/D47crunch), [GitHub](https://github.com/mdaeron/D47crunch), [Zenodo](https://doi.org/10.5281/zenodo.4314550)) described by [Daëron (2021)](https://doi. org/10.1029/2020GC009588).

```csv
Sample   D47  D47_SE   D47_correl
FOO-1  0.567   0.008   1.00  0.25  0.25
BAR-2  0.575   0.009   0.25  1.00  0.25
BAZ-3  0.582   0.007   0.25  0.25  1.00
```

This yields:

```txt
Sample   D47  D47_SE  D47_correl                  T  T_SE_from_calib  T_correl_from_calib                T_SE_from_input  T_correl_from_input                T_SE_from_both  T_correl_from_both              
FOO-1  0.567   0.008        1.00  0.25  0.25  34.20             0.38                1.000  0.996  0.987             2.91                1.000  0.250  0.250            2.94               1.000  0.261  0.264
BAR-2  0.575   0.009        0.25  1.00  0.25  31.33             0.37                0.996  1.000  0.997             3.18                0.250  1.000  0.250            3.21               0.261  1.000  0.263
BAZ-3  0.582   0.007        0.25  0.25  1.00  28.89             0.36                0.987  0.997  1.000             2.42                0.250  0.250  1.000            2.44               0.264  0.263  1.000
```

What changed ? We now have propagated `D47_correl` into `T_correl_from_input`, and this is accounted for in the combined correlation matrix `T_correl_from_both`. Within the framework of our initial assumptions (multivariate Gaussian errors, first-order linear propagation of uncertainties...), this constitutes the “best” (or rather, the most “information-complete”) description of uncertainties constraining our final `T` estimates.

With increasing number of measurements, these correlation matrices become quite large, so that it becomes useless to print them out visually. To facilitate using the output of `D47calib` as an input to another piece of software, one may use the `-j` or `--delimiter-out` option to use machine-readable delimiters such as commas or tabs, and the `'-o'` or `--output-file` option to save the output as a file instead of printing it out:

```txt
D47calib -i ' ' -j ',' -o output.csv input.csv
```

This will create the following `output.csv` file:

```csv
Sample,D47,D47_SE,D47_correl,,,T,T_SE_from_calib,T_correl_from_calib,,,T_SE_from_input,T_correl_from_input,,,T_SE_from_both,T_correl_from_both,,
FOO-1,0.567,0.008,1.00,0.25,0.25,34.20,0.38,1.000,0.996,0.987,2.91,1.000,0.250,0.250,2.94,1.000,0.261,0.264
BAR-2,0.575,0.009,0.25,1.00,0.25,31.33,0.37,0.996,1.000,0.997,3.18,0.250,1.000,0.250,3.21,0.261,1.000,0.263
BAZ-3,0.582,0.007,0.25,0.25,1.00,28.89,0.36,0.987,0.997,1.000,2.42,0.250,0.250,1.000,2.44,0.264,0.263,1.000
```

Hint for Mac users: Quick Look (or “spacebar preview”, i.e. what happens when you select a file in the Finder and press the spacebar once) provides you with a nice view of a csv file when you just want to check the results visually, as long as you use a comma delimiter.

### 3.1.4 Converting from `T` to `D47`

Everything described above works in the other direction as well, without changing anything to the command-line instruction:

```csv
T   T_SE
0    0.5
10   1.0
20   2.0
```

Yields:

```txt
 T  T_SE     D47  D47_SE_from_calib  D47_correl_from_calib                D47_SE_from_input  D47_correl_from_input                D47_SE_from_both  D47_correl_from_both              
 0   0.5  0.6798             0.0016                  1.000  0.969  0.848             0.0020                  1.000  0.000  0.000            0.0025                 1.000  0.210  0.091
10   1.0  0.6424             0.0013                  0.969  1.000  0.952             0.0035                  0.000  1.000  0.000            0.0038                 0.210  1.000  0.056
20   2.0  0.6090             0.0011                  0.848  0.952  1.000             0.0063                  0.000  0.000  1.000            0.0064                 0.091  0.056  1.000
```

## 3.2 Integration with D47crunch

Starting with the following input file `rawdata.csv`:

```csv
.. include:: ../code_examples/cli/fullexample_rawdata.csv
```

The following script will read thart raw data, fully process it, convert the standardized output to temperatures, and save the final results to a file named `output.csv`:

```txt
D47crunch rawdata.csv
D47calib -o output.csv -j '>' output/D47_correl.csv
```

With the contents of `output.csv` being:

```txt
.. include:: ../code_examples/cli/fullexample_output.csv
```

If a simpler output is required, just add the `--ignore-correl` or `-g` option to the second line above, which should yield:

```txt
.. include:: ../code_examples/cli/fullexample_output2.csv
```

## 3.3 Further customizing the CLI

A complete list of options is provided by `D47calib --help`.

### 3.3.1 Using covariance instead of correlation matrix as input

Just provide `D47_covar` (or `T_covar` when converting in the other direction) in the input file instead of `D47_SE` and `D47_correl`.

### 3.3.2 Reporting covariance instead of correlation matrices in the output

Use the `--return-covar` option.

### 3.3.3 Reporting neither covariances nor correlations in the output

If you don't care about all this covariance nonsense, or just wish for an output that does't hurt your eyes, you can use the `--ignore-correl` option. Standard errors will still be reported.

### 3.3.4 Excluding or only including certain lines (samples) from the input

To filter the samples (lines) to process using `--exclude-samples` and `--include-samples`, first add a `Sample` column to the input data, assign a sample name to each line.                                                                                  

Then to exclude some samples, provide the `--exclude-samples` option with the name of a file where each line is one sample to exclude.                                                                                                                 

To exclude all samples except those listed in a file, provide the `--include-samples` option with the name of that file, where each line is one sample to include.                                                                                         
 

### 3.3.5 Changing the numerical precision of the output

This is controlled by the following options:

* `--T-precision` or `-p` (default: 2): All `T` and `T_SE_*` values
* `--D47-precision` or `-q` (default: 4): All `D47` and `D47_SE_*` values
* `--correl-precision` or `-r` (default: 3): All `*_correl_*` values
* `--covar-precision` or `-s` (default: 3): All `*_covar_*` values

### 3.3.6 Using a different Δ47 calibration

You may use a different calibration than the default `OGLS23` using the `--calib` or `-c` option. Any predefeined calibration from the `D47calib` library is a valid option.

You may also specify an arbitrary polynomial function of inverse `T`, by creating a file (e.g., `calib.csv`) with the following format:

```csv
degree    coef        covar
0       0.1741   2.4395e-05  -0.0262821       5.634934
1      -17.889   -0.0262821    32.17712       -7223.86
2        42614     5.634934    -7223.86    1654633.996
```

Then using `-c calib.csv` will use this new calibration.

If you don't know/care about the covariance of the calibration coefficients, just leave out the covar terms:

```csv
degree    coef
0       0.1741
1      -17.889
2        42614
```

In this case, all `*_SE_from_calib` outputs will be equal to zero, but the `*_from_input`  uncertainties will still be valid (and identical to `*_from_both` uncertainties, since we are ignoring calibration uncertainties).