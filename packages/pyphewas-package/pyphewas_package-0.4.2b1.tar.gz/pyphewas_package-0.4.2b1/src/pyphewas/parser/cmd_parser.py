import argparse
from rich_argparse import RichHelpFormatter
from importlib.metadata import version
from pathlib import Path


def generate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI tool used to run a PheWAS.",
        formatter_class=RichHelpFormatter,
        epilog="""
    Minimal Examples:
        %(prog)s  --counts counts.csv --covariate-file covariates.csv --min-phecode-count 2 --covariate-list COVAR_1 COVAR_2 COVAR_3 --status-col status_colname --sample-col sample_colname --min-case-count 100
    """,
    )

    parser.add_argument(
        "--counts", type=Path, help="counts of each phecode that someone has"
    )

    parser.add_argument(
        "--covariate-file",
        type=Path,
        help="comma separated file that has the covariates for each individual in the cohort. There should be a column for the individual ids, the variable of interest, and then covariates. Even if you are running this without covariates then there should still be the individual ids and variable of interest columns.",
    )

    parser.add_argument(
        "--min-phecode-count",
        type=int,
        default=2,
        help="minumum number of times the person needs the PheCode for them to count as a case. Default %(default)s",
    )

    parser.add_argument(
        "--min-case-count",
        type=int,
        default=20,
        help="minumum number of cases for a phecode to have to be included in the analysis. Default %(default)s",
    )

    parser.add_argument(
        "--covariate-list",
        nargs="*",
        help="list of covariates to use in the analysis. These variables have to be spelled exactly like how they are in the covariates file. If there is a sex or gender column in the file, it is assuming that the values in the column are either 0 or 1",
    )

    parser.add_argument(
        "--status-col",
        type=str,
        default="status",
        help="column that has the variable of interest. Default: %(default)s",
    )

    parser.add_argument(
        "--sample-col",
        type=str,
        default="person_id",
        help="Column name for the column in the covariates file that has the individual ids. Default: %(default)s",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("test_output.txt"),
        help="output_file that the results for the phewas will be written to. If the filename ends in .gz then the file will be gzipped. Otherwise it will just be a tab separated text file. Default: %(default)s",
    )

    parser.add_argument(
        "--phecode-descriptions",
        type=Path,
        help="Comma separate file that list the phecode and the phecode description. The phecode is expected to be the first colummn while the phecode description is expected to be the fourth column.",
    )

    parser.add_argument(
        "--cpus",
        type=int,
        default=1,
        help="number of cpu processes to use in the program. This will be passed to the multiprocess.Pool. Default: %(default)s",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=200,
        help="Maximum number of iterations for the model to go through before it converges. If the model doesn't converge after this value then a ConvergenceWarning will be thrown. Default: %(default)s",
    )

    parser.add_argument(
        "--phecode-version",
        type=str,
        default="None",
        choices=["phecodeX", "phecode1.2", "phecodeX_who", "None"],
        help="What version of phecodes to use for the analysis. The options have to be spelled the same as they are here. Allowed choices: '%(choices)s'",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="logistic",
        required=False,
        choices=["linear", "logistic"],
        help="Whether to run a linear model or a logistic model for the regression. (default: %(default)s)",
    )

    parser.add_argument(
        "--flip-predictor-and-outcome",
        default=False,
        help="Optional flag to control the behavior of what is the predictor and what is the outcome. By default, our model assumes the outcome is the phecode status and the predictor is or provided case/control status. If this flag is provided then the outcome becomes our case/control status and the predictor will be the phecode status %(default)s",
        action="store_true",
    )

    parser.add_argument(
        "--run-sex-specific",
        type=str,
        choices=["male-only", "female-only"],
        help="Flag that allows the user to run the analysis sex specific. By default the PheWAS will be sex agonistic, allowing the user to adjust for sex using covariates. If the user provides a value then the program will filter to either males or females based on the value provided. %(choices)s",
    )

    parser.add_argument(
        "--male-as-one",
        default=True,
        type=bool,
        help="Flag indicating whether males are labeled as 1 and females are labeled as 0 or vice versa. %(default)s",
    )

    parser.add_argument(
        "--sex-col",
        type=str,
        help="Column name of the column in the covariates file that contains information about sex for each individual. This argument only needs to be provided if the user is using the '--run-sex-specific' flag. If this argument is passed and the '--run-sex-specific' flag is not provided then the program will ignore this flag. If there are people with missing sex values in the covariates file then they will be implicited filtered out of the analysis",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s: {version('pyphewas-package')}",
    )

    parser.add_argument(
        "--record-perfect-separation",
        action="store_true",
        default=False,
        help="Whether or not to store the state of the program when a perfect separation error is encountered. This flag is mainly used for debugging and will save the inputs being passed to the regression when the perfect separation is encountered",
    )

    return parser
