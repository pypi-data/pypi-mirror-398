from typing import Any
from statsmodels.discrete.discrete_model import BinaryResultsWrapper
from statsmodels.genmod.generalized_linear_model import GLMResultsWrapper
from firthmodels import FirthLogisticRegression

ModelResults = dict[str, Any]


def format_results(
    results: BinaryResultsWrapper | GLMResultsWrapper,
) -> ModelResults:
    result_dictionary = {}
    # We need to first get the convered status
    result_dictionary["converged"] = str(results.converged)

    for key, pvalue in results.pvalues.items():

        # # We don't need to report the values for the intercept
        if key == "Intercept":
            continue
        elif (
            key == "phecode_status"
        ):  # if the phecode is being used as a predictor then we need to ultimately
            key = key.split("_")[0]

        result_dictionary[f"{key}_pvalue"] = pvalue
    for key, beta in results.params.items():
        # # We don't need to report the values for the intercept
        if key == "Intercept":
            continue
        elif key == "phecode_status":
            key = key.split("_")[0]

        result_dictionary[f"{key}_beta"] = beta
    for key, se in results.bse.items():
        # # We don't need to report the values for the intercept
        if key == "Intercept":
            continue
        elif key == "phecode_status":
            key = key.split("_")[0]

        result_dictionary[f"{key}_stderr"] = se

    return result_dictionary


def format_firth_results(
    results: FirthLogisticRegression,
    feature_names: list[str],
) -> ModelResults:
    result_dictionary = {}
    # We need to first get the convered status
    result_dictionary["converged"] = str(results.converged_)

    for index, key in enumerate(feature_names):

        # # We don't need to report the values for the intercept
        if key == "Intercept":
            continue
        elif (
            key == "phecode_status"
        ):  # if the phecode is being used as a predictor then we need to ultimately
            key = key.split("_")[0]

        result_dictionary[f"{key}_pvalue"] = results.pvalues_[index]
        result_dictionary[f"{key}_beta"] = results.coef_[index]
        result_dictionary[f"{key}_stderr"] = results.bse_[index]

    return result_dictionary
