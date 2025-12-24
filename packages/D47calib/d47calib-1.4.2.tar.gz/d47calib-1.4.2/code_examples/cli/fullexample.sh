#! /usr/bin/env zsh

uv run python prepare_fullexample.py
uv run D47crunch fullexample_rawdata.csv
mv output/D47_correl.csv ./fullexample_D47.csv
rm -r output
uv run D47calib -o fullexample_output.csv -j '>' fullexample_D47.csv
uv run D47calib -o fullexample_output2.csv -j '>' -g fullexample_D47.csv