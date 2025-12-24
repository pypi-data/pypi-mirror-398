import sys
import subprocess
from pathlib import Path

# Define paths to input files
TESTS_DIR = Path(__file__).parent
INPUTS_DIR = TESTS_DIR / "inputs"

LOGISTIC_COUNTS = (
    INPUTS_DIR / "phecodes_file_10000_samples_binary_predictor_30_phecodes.txt"
)
LOGISTIC_COVARIATES = (
    INPUTS_DIR / "covariates_file_10000_samples_binary_predictor_30_phecodes.txt"
)

LINEAR_COUNTS = (
    INPUTS_DIR / "phecodes_file_10000_samples_dosage_predictor_30_phecodes.txt"
)
LINEAR_COVARIATES = (
    INPUTS_DIR / "covariates_file_10000_samples_dosage_predictor_30_phecodes.txt"
)

PERFECT_SEP_COUNTS = (
    INPUTS_DIR
    / "phecodes_file_10000_samples_binary_predictor_30_phecodes_perfect_sep.txt"
)

PERFECT_SEP_COVARIATES = (
    INPUTS_DIR
    / "covariates_file_10000_samples_binary_predictor_30_phecodes_perfect_sep.txt"
)

# Path to the main script
SCRIPT_PATH = Path("src/pyphewas/run_PheWAS.py")


def test_logistic_regression(tmp_path):
    output_file = tmp_path / "logistic_output.txt"

    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--counts",
        str(LOGISTIC_COUNTS),
        "--covariate-file",
        str(LOGISTIC_COVARIATES),
        "--min-phecode-count",
        "2",
        "--min-case-count",
        "20",
        "--covariate-list",
        "age",
        "sex",
        "--status-col",
        "predictor",
        "--sample-col",
        "id",
        "--phecode-version",
        "None",
        "--model",
        "logistic",
        "--output",
        str(output_file),
        "--cpus",
        "2",
    ]

    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Check that the command ran successfully
    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

    # Check that the output file was created
    assert output_file.exists()

    assert output_file.stat().st_size > 0


def test_linear_regression(tmp_path):
    output_file = tmp_path / "linear_output.txt"

    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--counts",
        str(LINEAR_COUNTS),
        "--covariate-file",
        str(LINEAR_COVARIATES),
        "--min-phecode-count",
        "2",
        "--min-case-count",
        "20",
        "--covariate-list",
        "age",
        "sex",
        "--status-col",
        "predictor",
        "--sample-col",
        "id",
        "--phecode-version",
        "None",
        "--model",
        "linear",
        "--output",
        str(output_file),
        "--cpus",
        "2",
    ]

    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Check that the command ran successfully
    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

    # Check that the output file was created
    assert output_file.exists()

    assert output_file.stat().st_size > 0


def test_firth_regression(tmp_path) -> None:
    output_file = tmp_path / "perfect_separation_test.txt"

    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--counts",
        str(PERFECT_SEP_COUNTS),
        "--covariate-file",
        str(PERFECT_SEP_COVARIATES),
        "--min-phecode-count",
        "2",
        "--min-case-count",
        "20",
        "--covariate-list",
        "age",
        "sex",
        "--status-col",
        "predictor",
        "--sample-col",
        "id",
        "--phecode-version",
        "None",
        "--model",
        "logistic",
        "--output",
        str(output_file),
        "--cpus",
        "2",
    ]

    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Check that the command ran successfully
    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

    # Check that the output file was created
    assert output_file.exists()

    assert output_file.stat().st_size > 0
