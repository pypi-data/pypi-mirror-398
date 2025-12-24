# PyPheWAS package

A python script I use to run PheWAS analyses. Full Documentation can be found here: [online docs](https://pyphewas-package.readthedocs.io/en/latest/)

## Summary

This repository contains a CLI tool implemented in python that can be used to run a PheWAS analysis. This script supports both PheCode 1.2 and PheCode X (read about each [here](https://phewascatalog.org/phewas/#home)). This package is based on the [PheTK](https://github.com/nhgritctran/PheTK) package but offers flexibility in the model that I wanted and has a more verbose output by reporting the betas and standard errors for all predictors.

## Installation

This code is hosted on PYPI and can be install using a package manager such as conda or pip. If using Pip it is recommend to first make a virtualenv using venv and then installing the program into the virtual environment. Use the following commands to install the program.

```bash Pip installation
python3 -m venv pyphewas-venv

source pyphewas-venv/bin/activate

pip install pyphewas-package
```

```bash Conda installation
conda create -n pyphewas_env python=3.13 -y

conda activate pyphewas_env

pip install pyphewas-package
```

If you would like to install the PyPheWAS Package from source it is avaliable on [Github](https://github.com/jtb324/PyPheWAS). It is recommended to use [PDM](https://pdm-project.org/latest/) to install the project. To install the PyPheWAS package from source using PDM, run the following command:

```bash PDM installation
pdm install
```

If you want to install the program from source code without PDM then you must first install the necessary dependencies from the pyproject.toml file using pip. Then you can call the source file which is located at './src/pyphewas/run_PheWAS.py'

## Required Inputs

* **--counts**: filepath to a comma separated file where each row has a ID, a phecode id, and the number of times that individual has that phecode in their medical record.

* **--covariate-file**: filepath to a comma separated file that list the covariates and predictor for each individual. The individuals listed in the covariate file will be the individuals in the cohort. *Note* If the 'flip-predictor-and-outcome' flag is used then the predictor variable is assumed to be the outcome in the model.

* **--covariate-list**: Space separated list of covariates to use in the model. All of these covariates must be present in the covariate file and must be spelled exactly the same otherwise the code will crash.

* **--phecode-version**: String telling which version of phecodes to use. This argument helps with mapping the PheCode ID to a description. The allowed values are "phecodeX", "phecode1.2", and "phecodeX_who". Most users will only need to use either the PhecodeX or Phecode1.2 option.

## Optional Inputs

Although these arguments are not required for runtime, some combination of them will general be used to make the analysis either more rigorous, more robust, or more fine tuned for the exact question being asked.

* **--min-phecode-count**: Minimum number of phecodes an individual is required to have in order to be considered a case for a phecode. Default value is 2. Under default settings, all individuals with 1 occurence of the phecode are excluded from the regression. If this value is set to 1 then there are no excluded individuals.

* **--min-case-count**: Minimum number of cases a phecode has to have to be included in the analysis. The default value is 20. There is no rigorous testing behind this value, only convention. For more rigorous results, a more conservative value of 100 may be ideal.

* **--status-col**: column name for the column in the covariate file that has the predictor case/control status. Default value is "status"

* **--sample-col**: column name for the column in the covariates file that has the individual ids. Default value is "person_id"

* **--output**: filename to write the output to. The output will be written as a tab separated file. If the suffix of the file ends in gz then the file will be gzipped otherwise the file will be uncompressed. Default value is test_output.txt

* **--phecode-descriptions**: filepath to a comma separated file that list the phecode ID and the corresponding phecode name. There are default description files stored in the './src/phecode_maps/' folder if you wish to see example files that are currently used in the code. The phecode ID is expected to be the first column while the phecode description is expected to be the 4th column.

* **--cpus**: Number of cpus to use during the analysis. Default value is 1.

* **--max-iterations**: Number of iterations for the regression to try to converge. If the model doesn't converge after reaching the max iteration threshold then a ConvergenceWarning will be thrown. If you run this code and find that many PheCodes are not converging then it is recommended to increase this value to attempt to get more phecodes to converge. Default value is 200

* **--flip-predictor-and-outcome**: Depending on the analysis, you may want the status column in the covariate file to be a predictor or to be the outcome. If you want the status to be the outcome then you can supply this flag as '--flip-predictor-and-outcome'. When the status is the outcome, then the case/control status for the individual phecodes will become the predictor.

* **--run-sex-specific**: Depending on the analysis, you may also want to restrict the analysis to a sex stratified cohort. This command is one of three flags that have to be used in tandem that allow you to stratify the analysis. Allowed values are 'male-only' and 'female-only'.

* **--male-as-one**: If the '--run-sex-specific' flag is used then this flag also has to be passed indicating if males were coded as 1 and females as 0 or vice verse. You could pass this flag as '--male-as-one' to indicate that males were coded as 1. The default value is True although this flag will be ignored if the '--run-sex-specific' flag is not provided.

* **--sex-col**: Column name of the column in the covariate fiel containing Sex or Gender information. This flag is required if the '--run-sex-specific' flag was used.

* **--phecode-descriptions**: comma separated file

# Example Command

**Non sex stratified with parallelization**:

```bash
pyphewas \
    --counts counts.csv \
    --covariate-file covariates.csv \
    --min-phecode-count 2 \
    --status-col status \
    --sample-col person_id \
    --covariate-list EHR_GENDER age unique_phecode_count \
    --min-case-count 100 \
    --cpus 25 \
    --output output.txt.gz \
    --phecode-version phecodeX
```

**Sex Stratified with parallelization**:

```bash
pyphewas \
    --counts counts.csv \
    --covariate-file covariates.csv \
    --min-phecode-count 2 \
    --status-col status \
    --sample-col person_id \
    --covariate-list age unique_phecode_count \
    --min-case-count 100 \
    --cpus 25 \
    --output output.txt.gz \
    --phecode-version phecodeX \
    --flip-predictor-and-outcome \
    --run-sex-specific female-only \
    --male-as-one True \
    --sex-col EHR_GENDER
```
