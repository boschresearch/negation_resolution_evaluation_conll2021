# Instance-based Evaluation

This folder contains code for our proposed instance-based evaluation of negation resolution.

## Running the Code
**_Usage_**:

	python run_evaluation.py [-h] [-t] gold_file system_files [system_files ...]

	positional arguments:
		  gold_file         path to gold corpus file
		  system_files      path(s) to system file(s)

	optional arguments:
		  -h, --help        show this help message and exit
		  -t, --token-eval  Evaluate scopes on a per-token basis (i.e., do not
                                                    normalize scope lengths)

**Note:**
- Gold and system files must be in *SEM format.
- The script returns scores for our NIS<sub>tok</sub> metric by default. Specifying the `-t` option disables
  scope length normalization, meaning the resulting numbers will correspond to *SEM's "scope tokens" metric.
