fsl-qa
======

QA scripts for FSL analysis

Right now the features are:
- load featdir and check for presence of design.fsf
- checks for presence of stats, reg, and reg_standard subduers
- loads fsf info and design matrix (using mvpa functions)
- loads all of the evs into a dictionary
- loads all of the contrasts into a dictionary
- checks for deleted volumes at beginning of scan
- checks for whether mcflirt, or bet were turned on in preprocessing
- checks whether pre whitening was turned on
- computes variance inflation factors for each ev in the model
- checks for proper HRF settings (3 for real evs, 0 for motion evs)
- checks for presence of zstat and pe files for each ev and saves min/max values from each file
- load mask file and check number of nonzero voxels
- load report_log.html and note any occurrences of warnings, errors, or exceptions
