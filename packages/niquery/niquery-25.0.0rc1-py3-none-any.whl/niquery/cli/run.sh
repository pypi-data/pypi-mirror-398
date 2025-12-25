#!/bin/bash

source `which virtualenvwrapper.sh`

data_dir_rootname="/mnt/data/nipreps/nifreeze/openneuro_niquery/"

workon niquery

###################################
out_fname="${data_dir_rootname}/openneuro_datasets.tsv"

niquery query ${out_fname}

###################################
in_fname="${data_dir_rootname}/openneuro_datasets.tsv"
out_dirname="${data_dir_rootname}/dataset_files"

niquery collect ${in_fname} ${out_dirname}

###################################
in_dirname="${data_dir_rootname}/dataset_files"
out_dirname="${data_dir_rootname}/dataset_features"

niquery characterize ${in_dirname} ${out_dirname}

###################################
in_dirname="${data_dir_rootname}/dataset_features"
out_fname="${data_dir_rootname}/selected_openneuro_datasets.tsv"

niquery select ${in_dirname} ${out_fname} 1234 --total-runs 4000 --contr-fraction 0.05 --min-timepoints 300 --max-timepoints 1200
