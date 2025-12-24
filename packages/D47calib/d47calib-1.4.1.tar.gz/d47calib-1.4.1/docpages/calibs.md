# 2. Calibrations included

`D47calib` provides the following pre-built calibrations. All code and raw data used to compute these calibrations can be found in the `build_calibs` directory.

##### **`breitenbach_2018`:**
Cave pearls analyzed by [Breitenbach et al. (2018)](https://doi.org/10.1016/j.gca.2018.03.010).

Raw data were obtained from the original study’s supplementary information. The original publication processed data according to two sessions, each 4-5 months long, separated by 2 months. After reprocessing the original raw data using D47crunch, visual inspection of the standardization residuals defined revealed the presence of substantial drifts in both sessions. We thus assigned modified session boundaries defining four continuous measurement periods separated by 21 to 52 days, with new session lengths ranging from 24 to 80 days. The original data was not modified in any other way. Formation temperatures are from table 1 of the original study. We assigned arbitrary 95 % uncertainties of ±1 °C, which seem reasonable for cave environments.

##### **`peral_2018`:**
Planktic foraminifera analyzed by [Peral et al. (2018)](https://doi.org/10.1016/j.gca.2018.07.016), reprocessed by [Daëron & Gray (2023)](https://doi.org/10.1029/2023PA004660).

Peral et al. [2018] reported Δ47 values of foraminifera from core-tops, both planktic and benthic, whose calcification temperature estimates were recently reassessed by [Daëron & Gray (2023)](https://doi.org/10.1029/2023PA004660). Here we only consider Peral et al.’s planktic data, excluding two benthic samples (cf Daëron & Gray for reasons why we only consider planktic samples for now). In our reprocessing, as in the original study, “samples” are defined by default as a unique combination of core site, species, and size fraction. Δ47 values are then standardized in the usual way, before using [`D47crunch.combine_samples()`](https://mdaeron.github.io/D47crunch/#D4xdata.combine_samples) to combine all size fractions with the same core and species, except for G. inflata samples (cf [Daëron & Gray](https://doi.org/10.1029/2023PA004660) and accompanying GitHub [repository](https://github.com/mdaeron/isoForam)). By properly accounting for analytical error covariance between the Δ47 values to combine, this two-step approach avoids underestimating the final standardization errors.


##### **`jautzy_2020`:**
Synthetic calcites analyzed by [Jautzy et al. (2020)](https://doi.org/10.7185/geochemlet.2021).

Jautzy et al. reported data from a continuous period spanning 10 months, and used a moving-window approach to standardize their measurements. We assigned sessions defined, whenever possible, as periods of one or more complete weeks enclosing one of more unknown sample analyses. The resulting Δ47 residuals, on the order of 40 ppm (1SD), do not display evidence of instrumental drift. Formation temperatures are from table S2 of the original study. We assigned arbitrary 95 % uncertainties of ±1 °C, which seem reasonable for laboratory experiments.

##### **`anderson_2021_mit`:**
Various natural and synthetic carbonates analyzed at MIT by [Anderson et al. (2021)](https://doi.org/10.1029/2020gl092069).

Raw IRMS data and temperature constraints were obtained from the original study’s supple- mentary information (tables S01 and S02). When reprocesseded the IRMS data we made no changes to the session defintions, but we excluded sessions 5 and 25 because they did not include any unknown sample analyses.

##### **`anderson_2021_lsce`:**
Slow-growing mammillary calcite from Devils Hole and Laghetto Basso analyzed at LSCE by [Anderson et al. (2021)](https://doi.org/10.1029/2020gl092069).

Raw IRMS data is from the original study’s supplementary information (SI-S02). Temperature contraints are from table 1 in [Daëron et al. (2019)](http://dx.doi.org/10.1038/s41467-019-08336-5).

##### **`fiebig_2021`:**
Inorganic calcites analyzed by [Fiebig et al. (2021)](https://doi.org/10.1016/j.gca.2021.07.012).

Temperature contraints are duplicated from the earlier publications where the corresponding samples were first described [Daëron et al., 2019; Jautzy et al., 2020; Anderson et al., 2021]. Raw IRMS data and were obtained from the original study’s supplementary information, and processed as described by Fiebig et al. [2021], jointly using (a) heated and 25 °C-equilibrated CO2 to constrain the scrambling effect and compositional nonlinearity associated with each session, and (b) ETH-1 and ETH-2 reference materials to anchor unknown samples to the I-CDES scale.

##### **`huyghe_2022`:**
Marine calcitic bivalves analyzed by [Huyghe et al. (2022)](https://doi.org/10.1016/j.gca.2021.09.019).

[Huyghe et al.](https://doi.org/10.1016/j.gca.2021.09.019) reported Δ47 values of modern calcitic bivalves collected from localities with good environmental constraints. As was done in the original publication, different bivalve individuals were initially treated as distinct analytical samples. In some sites with strong seasonality, individuals were sub-sampled into winter-calcified a summer-calcified fractions. Δ47 values were then standardized in the usual way, before using [`D47crunch.combine_samples()`](https://mdaeron.github.io/D47crunch/#D4xdata.combine_samples) method to combine all samples from the same locality. Calcification temperature estimates are from the original study.


##### **`devils_laghetto_2023`:**
Combined data set of slow-growing mammillary calcite from Devils Hole and Laghetto Basso, analyzed both at LSCE by [Anderson et al. (2021)](https://doi.org/10.1029/2020gl092069) and at GU by [Fiebig et al. (2021)](https://doi.org/10.1016/j.gca.2021.07.012). 

##### **`OGLS23`:**
Combined data set including all of the above. For a detailed discussion of goodness-of-fit and regression uncertainties, see [*Daëron & Vermeesch* (2024)](https://doi.org/10.1016/j.chemgeo.2023.121881). Also aliased as `ogls_2023` for backward-compatibility.
