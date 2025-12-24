import csv
from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
import io
import json
from multiprocessing.managers import DictProxy
import signal
import sys
import numpy as np
from pathlib import Path
from xopen import xopen
import polars as pl
from tqdm import tqdm
import statsmodels.formula.api as smf
from statsmodels.genmod.families.family import Gaussian
from sklearn.exceptions import ConvergenceWarning as SklearnConvergenceWarning
from statsmodels.tools.sm_exceptions import (
    ConvergenceWarning,
    PerfectSeparationWarning,
)
from firthmodels import FirthLogisticRegression
from patsy import dmatrices
import multiprocessing as mp
import warnings

from pyphewas.parser import generate_parser
from pyphewas.model_formatters import format_results, format_firth_results, ModelResults

# We want to treat the Runtime warning like a error so that we can catch it because it indicates the perfect separation error
warnings.filterwarnings("error", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("error", category=PerfectSeparationWarning)
# import pandas as pd
# warnings.formatwarning(category=ConvergenceWarning)


@dataclass
class Phecode:
    cases: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)


def read_in_cases_and_exclusions(
    counts_file: Path, min_phecode_count: int
) -> dict[str, Phecode]:

    return_dict = {}

    with xopen(counts_file, "r") as counts:
        _ = next(counts)  # skip header line
        for line in counts:
            person_id, phecode, count = line.strip().split(",")
            if int(count) >= min_phecode_count:
                phecode_obj = return_dict.setdefault(
                    phecode, Phecode()
                )  # We can see if there is already a phecode object create for the phecode
                phecode_obj.cases.append(person_id)
            elif (
                int(count) == 1 and min_phecode_count != 1
            ):  # if the min phecode count is 1 then we want to ignore the exclusion criteria
                phecode_obj = return_dict.setdefault(phecode, Phecode())
                phecode_obj.exclusions.append(person_id)

    print(f"Read in {len(return_dict)} phecodes from the counts file: {counts_file}")
    return return_dict


def generate_model_str(
    covar_list: list[str] | None,
    status_col: str,
    flip_predictor_and_outcome: bool = False,
) -> str:
    # build the model string where the phecode status is the
    # outcome and the predictor is our case control status. When the
    # regression code adds the phecode status to the covariate df, it
    # names it phecode_status so we can assume that is the name of the
    # column in the model
    if not flip_predictor_and_outcome:
        analysis_str = f"phecode_status ~ {status_col}"
    else:
        analysis_str = f"{status_col} ~ phecode_status"

    if covar_list:
        analysis_str = f"{analysis_str} + {' + '.join(covar_list)}"

    print(f"model being used: {analysis_str}")
    return analysis_str


@dataclass
class RegressionResults:
    model_type: str
    result: ModelResults
    firth_used: bool
    err: Exception | None


def run_regression(
    model_eq: str,
    covariates: pl.DataFrame,
    regression_model: str,
    max_iteration_count: int,
) -> RegressionResults:
    covariate_df = covariates.to_pandas()
    try:
        if regression_model == "logistic":
            result = smf.logit(model_eq, data=covariate_df).fit(
                disp=0, maxiter=max_iteration_count
            )
        else:
            # run the linear model
            result = smf.glm(
                formula=model_eq, data=covariate_df, family=Gaussian()
            ).fit(disp=0, maxiter=max_iteration_count)

        result = format_results(result)
        error = None

        # In the case of any exception we are going to just return the error and result will be None
    except Exception as e:
        result = {}
        error = e

    return RegressionResults(
        model_type=regression_model, result=result, err=error, firth_used=False
    )


def check_err(error_obj: Exception) -> int:
    """look at the exception and decide whether the program can continue or if it needs to fail"""
    # If a perfect separation error occurs then we
    if (
        "Singular matrix" in str(error_obj)
        or "Perfect separation" in str(error_obj)
        or "overflow encountered in exp" in str(error_obj)
    ):
        return 0
    else:
        raise error_obj


def run_firth_regression(model_eq: str, data: pl.DataFrame) -> RegressionResults:
    """firth regression model if the program encounters a perfect
    separation error. The function uses patsy to create the inputs
    correctly and then runs the firth regression

    Parameters
    ----------
    model_eq : str
        This is the regression equation that is formed
        generate_model_str function

    data : pl.DataFrame
        This is the covariate file that also has the phecode predictor and the outcome
    """

    data_df = data.to_pandas()

    # dmatrics is from patsy and will automatically generate two
    # matrices for the X and y inputs in the firth regression model
    outcomes, predictors = dmatrices(model_eq, data_df)

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("error", category=SklearnConvergenceWarning)
            firth_model = FirthLogisticRegression(fit_intercept=False).fit(
                predictors, outcomes.ravel()
            )

        feature_names = predictors.design_info.column_names

        result = format_firth_results(firth_model, feature_names)
        error = None
    except SklearnConvergenceWarning as e:
        result = {}
        error = e
    except Exception as e:
        result = {}
        error = e

    return RegressionResults(
        model_type="firth", result=result, err=error, firth_used=True
    )


def run_phewas(
    phecode_info: tuple,
    return_dictionary: DictProxy,
    covariates: pl.DataFrame,
    analysis_str: str,
    sample_colname: str,
    min_case_count: int,
    max_iteration_threshold: int,
    regression_model: str = "logistic",
) -> None:
    """method to run regress for the phenotype of interest
    Parameters
    ----------
    phecode_info : tuple
        tuple that has information for the regression such as what the
        phecode name is and who are the cases/controls/and exclusions

    return_dictionary : DictProxy
        Dictionary that is being shared between the different
        python processes.

    covariates : pl.DataFrame
        polars dataframe containing all of the covariates to use
        in the regression analysis

    analysis_str : str
        string for the model that takes the form 'Y=mx+B'

    sample_colname : str,
        column that has the sample ids for the analysis

    min_case_count : int
        minimum number of cases that a phecode has to have to be
        included in the analysis

    max_iteration_threshold : int
        maximum number of iterations for the model to converge.
        This value can be increased if a large number of the
        regressions don't converge

    regression_mode : str
        string indicating whether we are trying to run a
        linear regression model or a logistic regression model

    save_state_on_error : bool
        boolean argument indicating whether the user wishes to
        save the inputs to the regression when an error is encountered.
        This flag is mainly used for debugging

    """

    phecode_name, phecode_obj = phecode_info[0]

    covariates_df = covariates.filter(
        ~pl.col(sample_colname).is_in(phecode_obj.exclusions)
    ).with_columns(
        pl.when(pl.col(sample_colname).is_in(phecode_obj.cases))
        .then(1)
        .otherwise(0)
        .alias("phecode_status")
    )  # Note that anyone here who was not in the counts file (and therefore is
    # not a case or exclusions) will be a control. This means if the individual
    # has no count for any phecode then they will be considered a control

    # This check ensures that the number of cases is >= to the minimum case count.
    # There is already a check for case count when the case and exclusions are read in,
    # but this check fails if there are people in the counts file that are not in the
    # covariate file (pyphewas uses the covariate file to build the cohort). When there
    # are extract individuals in the counts file then the case count can be higher than
    # it would be in the cohort
    if covariates_df.select(pl.col("phecode_status")).sum().item() < min_case_count:
        return
    # When doing the sex stratified analysis there is a chance that there will be no cases
    # despite how there were originally cases. We need to account for that here.
    if len(covariates_df.select(pl.col("phecode_status").value_counts())) == 1:
        return
    # lets get the counts of cases and controls (This is verbose but adapted from the
    # stackoverflow answer: https://stackoverflow.com/questions/78057705/is-there-a-simple-way-to-access-a-value-in-a-polars-struct)
    case_count = (
        covariates_df.select(pl.col("phecode_status").value_counts())
        .filter(pl.col("phecode_status").struct["phecode_status"] == 1)
        .item()["count"]
    )
    control_count = (
        covariates_df.select(pl.col("phecode_status").value_counts())
        .filter(pl.col("phecode_status").struct["phecode_status"] == 0)
        .item()["count"]
    )

    # We can calculate exclusions by subtracting the final shape from the original shape
    exclusion_count = covariates.shape[0] - covariates_df.shape[0]

    # run the regression
    results = run_regression(
        analysis_str, covariates_df, regression_model, max_iteration_threshold
    )

    if results.err is not None:

        _ = check_err(results.err)
        print(f"Using firth regression for the phecode, {phecode_name}.")

        results = run_firth_regression(analysis_str, covariates_df)

        if results.err is not None:
            print(
                f"Perfect separation encountered for the phecode {phecode_name}. There were {case_count} cases and {control_count} controls for the phecode."
            )

            return

    # Lets add the counts to the results dictionary
    results.result["firth"] = results.firth_used
    results.result["case_count"] = case_count
    results.result["control_count"] = control_count
    results.result["exclusion_count"] = exclusion_count
    return_dictionary[phecode_name] = results.result


def _generate_header(
    status_name: str, covar_list: list[str], predictor_output_flipped: bool
) -> str:

    # if the predictor was split then we want the string to start with
    # predictor_phecode and all the columns with the status_name should
    # just say phecode_*
    if predictor_output_flipped:
        phecode_name_str = "predictor_phecode"
    else:  # otherwise the string starts with phecode and uses the status name we provided
        phecode_name_str = "phecode"

    header_str = f"{phecode_name_str}\tphecode_description\tphecode_category\tcase_count\tcontrol_count\texclusion_count\tconverged\tfirth"

    header_str += f"\t{status_name}_pvalue"
    header_str += f"\t{status_name}_beta"
    header_str += f"\t{status_name}_stderr"

    for covariate in covar_list:
        header_str += f"\t{covariate}_pvalue"
        header_str += f"\t{covariate}_beta"
        header_str += f"\t{covariate}_stderr"

    return header_str


def _write_to_file(
    output_filehandle: io.TextIOWrapper,
    status_name: str,
    phecode_descriptions: dict[str, str],
    covar_list: list[str],
    results: DictProxy,
    predictor_output_flipped: bool = False,
) -> None:

    header = _generate_header(status_name, covar_list, predictor_output_flipped)

    output_filehandle.write(f"{header}\n")

    for phecode_name, phecode_results in results.items():

        phecode_description, category = phecode_descriptions.get(
            phecode_name, ("N/A", "N/A")
        )

        output_str = f"{phecode_name}\t{phecode_description}\t{category}\t{phecode_results.get('case_count', 'N/A')}\t{phecode_results.get('control_count', 'N/A')}\t{phecode_results.get('exclusion_count', 'N/A')}\t{phecode_results.get('converged', 'N/A')}\t{phecode_results.get('firth', 'N/A')}"

        # lets add all the values for the status to the string first

        output_str += f"\t{phecode_results.get(status_name + '_pvalue', 'N/A')}"
        output_str += f"\t{phecode_results.get(status_name + '_beta', 'N/A')}"
        output_str += f"\t{phecode_results.get(status_name + '_stderr', 'N/A')}"

        for covariate in covar_list:
            output_str += f"\t{phecode_results.get(covariate + '_pvalue', 'N/A')}"
            output_str += f"\t{phecode_results.get(covariate + '_beta', 'N/A')}"
            output_str += f"\t{phecode_results.get(covariate + '_stderr', 'N/A')}"

        output_filehandle.write(f"{output_str}\n")


def read_in_phecode_descriptions(descriptions_filepath: Path | None) -> dict[str, str]:
    description_dict = {}

    if descriptions_filepath:
        with xopen(descriptions_filepath, "r") as desc_filehandle:
            reader = csv.reader(desc_filehandle, delimiter=",", quotechar='"')
            _ = next(reader)
            for row in reader:
                phecode, _, _, phecode_str, _, category, *_ = row

                description_dict[phecode] = (phecode_str, category)
    return description_dict


def restrict_covars_to_specific_sex(
    covar_df: pl.DataFrame, sex_option: str, sex_col: str, males_as_one: bool
) -> pl.DataFrame:

    # lets first set the status for male or female
    if males_as_one:
        male_coding = 1
        female_coding = 0
    else:
        male_coding = 0
        female_coding = 1
    # Now we can filter to either male only or female only

    if sex_option.lower() == "female-only":
        output_df = covar_df.filter(pl.col(sex_col) == female_coding)
    else:
        output_df = covar_df.filter(pl.col(sex_col) == male_coding)

    print(
        f"restricting the cohort to {sex_option}, limited the cohort to {output_df.shape[0]} individuals"
    )

    return output_df


def main() -> None:

    parser = generate_parser()

    args = parser.parse_args()

    # We need to make sure that if the "--run-sex-specific" flag was provided that also the "--sex-col" flag was provided
    if args.run_sex_specific and not args.sex_col and not args.male_as_one:
        parser.error(
            f"Detected a provided value of {args.run_sex_specific} for the '--run-sex-specific' flag, but a value was not provided for the '--sex-col' flag or the '--male-as-one' flag. All three flags are required to run a sex specific analysis."
        )

    # we also need to make sure that the sex columns is not
    # in the list of covariates when we are running sex specific.
    if (  # Because args.covariate_list can be none we need to use short circuiting logic. If
        args.covariate_list  # args.covariate_list == None and we try to use the in operator then the code will raise an error
        and args.sex_col
        in args.covariate_list  # to avoid this we check if the covariate list is not none by checking
        and args.run_sex_specific  # for a truth value first
    ):
        parser.error(
            f"detected that the sex or gender column, {args.sex_col}, was also passed as a covariate. If you are trying to run a sex specific analysis please make sure you remove the sex or gender column from the analysis."
        )

    # getting the programs start time
    start_time = datetime.now()
    # we need to determine the correct path for the phecode descriptions.
    # We can store this values in config file
    if not args.phecode_descriptions and args.phecode_version in [
        "phecodeX",
        "phecode1.2",
        "phecodeX_who",
    ]:
        main_filepath = Path(__file__)
        with open(main_filepath.parent / "config.json", "r") as json_file:
            configs = json.load(json_file)
            try:
                phecode_descriptions = (
                    main_filepath.parent / configs[args.phecode_version]
                )
            except KeyError:
                print(
                    f"The provided phecode version, {args.phecode_version} is not allowed. Please provide a value of either 'phecodeX', 'phecode1.2', or 'phecodeX_who' spelled exactly as shown here"
                )
                sys.exit(1)
    # If the phecode version is none then we need to set the
    # phecode_description variable also to none indicating we
    # will not have any phecode descriptions
    elif not args.phecode_descriptions and args.phecode_version == "None":
        phecode_descriptions = None
    else:
        phecode_descriptions = args.phecode_descriptions

    print(f"{35*'~'}  PheWAS  {35*'~'}")
    print(f"Analysis start time: {start_time}")
    print(
        f"Using the following covariates in the analysis: {', '.join(args.covariate_list if args.covariate_list else '')}"
    )
    print(f"Using {args.cpus} cpus")

    if not args.flip_predictor_and_outcome:
        print(f"Variable of interest column name: {args.status_col}")
    else:
        print(
            f"Using the column, {args.status_col}, as the outcome. Every phecode in the provided counts file, {args.counts}, will be used as a predictor"
        )

    print(
        f"Requiring {args.min_phecode_count} occurences of the PheCode to be considered a case"
    )
    print(
        f"Requiring {args.min_case_count} cases for a phecode to be included in the analysis"
    )
    print(
        f"Using a maximum number of {args.max_iterations} iterations for the logistic regression model"
    )
    print(f"{80*'~'}\n")
    print(f"Loading in the phecode descriptions found here: {phecode_descriptions}")

    descriptions = read_in_phecode_descriptions(phecode_descriptions)

    phecode_cases = read_in_cases_and_exclusions(args.counts, args.min_phecode_count)

    covariates_df = pl.read_csv(args.covariate_file)

    if args.run_sex_specific:
        print("Restricting the covariates file to {args.run_sex_specific}")
        covariates_df = restrict_covars_to_specific_sex(
            covariates_df, args.run_sex_specific, args.sex_col, args.male_as_one
        )

    print("initializing multiprocessing" * (min(args.cpus - 1, 1)))

    item_count = len(phecode_cases.keys())

    # generating the analysis string for the model that will
    # be passed to the regression
    model_str = generate_model_str(
        args.covariate_list, args.status_col, args.flip_predictor_and_outcome
    )

    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    with (
        mp.get_context("spawn").Pool(processes=args.cpus) as pool,
        xopen(args.output, "w") as output_file,
        tqdm(total=item_count, desc="phecodes processed") as pbar,
    ):
        signal.signal(signal.SIGINT, original_sigint_handler)
        # We are going to create a manager and a dictionary to use in the regressions
        manager = mp.Manager()
        managed_dict = manager.dict()

        # running the logistic regression for multiple phecodes
        partial_func = partial(
            run_phewas,
            return_dictionary=managed_dict,
            covariates=covariates_df.clone(),
            analysis_str=model_str,
            sample_colname=args.sample_col,
            min_case_count=args.min_case_count,
            max_iteration_threshold=args.max_iterations,
        )
        try:
            for _ in pool.imap(
                partial_func, [(item,) for item in phecode_cases.items()]
            ):
                pbar.update()
        except KeyboardInterrupt:
            print("Detected a keyboard interuption. Ending program now")
            pool.terminate()
            print(f"{30 * '~'}  PheWAS Finished!  {30 * '~'}")
            sys.exit(1)
        else:
            pool.close()
            pool.join()

        # results = run_logit_regression(managed_dict, phecode_cases, covariates_df, args.covariate_list, args.status_col, args.sample_col,args.min_case_count)

        phecodes_tested = len(managed_dict)

        if phecodes_tested == 0:
            print("No phecodes were successfully tested. terminating program")
            sys.exit(1)
        else:
            bonferroni = 0.05 / phecodes_tested
        print(
            f"recommend Bonferroni correction: {bonferroni} or {-np.log10(bonferroni)} on a -log10 scale"
        )

        print(f"Writing the results of the PheWAS to the file: {args.output}")

        # if we are using the phecodes as the predictor then
        # we want out non covariate columns to just be "phecode_*"
        if args.flip_predictor_and_outcome:
            status_col = "phecode"
        # If we are using our case/control file as predictors then we will use
        # the status column of interest that we said
        else:
            status_col = args.status_col

        _write_to_file(
            output_file,
            status_col,
            descriptions,
            args.covariate_list,
            managed_dict,
            args.flip_predictor_and_outcome,
        )

    end_time = datetime.now()
    print(f"program finished at {end_time}")
    print(f"total runtime: {end_time - start_time}")
    print(f"{30 * '~'}  PheWAS Finished!  {30 * '~'}")


if __name__ == "__main__":
    main()
