from rich_argparse import RichHelpFormatter
import numpy as np
import argparse
from pathlib import Path
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass


@dataclass
class FormattedDf:
    dataframe: pl.DataFrame
    infinity_threshold: float


def determine_color_palatte(category_count: int) -> list[tuple]:
    """return the color palette based off of how many different phecode
    categories there are

    Parameters
    ----------
    category_count : int
        number of unique phecode categories in the provided dataframe file

    Returns
    -------
    list[tuple]
        returns a list different colors to represent each phecodee category"""
    if category_count <= 10:
        distinct_palette = sns.color_palette("tab10", n_colors=category_count)
    else:
        distinct_palette = sns.color_palette("tab20", n_colors=category_count)

    return distinct_palette


def format_df(df: pl.DataFrame, pval_colname: str, beta_colname: str) -> FormattedDf:
    """format the provided data in the following ways: 1) only keep converged
    values, 2) replace pvalues that were too significant and rounded to zero
    to be 1.02 * the most significant pvalue,3) create a column that indicates
    where the beta was negative or positive, 4) sort by phecode_category and
    phecode_description columns, 5) and a row index column that will be used to
    plot things on the x axis

    Parameters
    ----------
    df : pl.DataFrame
        dataframe that has the results from running the phewas.

    pval_colname : str
        name of the column that has the pvalue of interest

    beta_colname : str
        name of the column that has the beta for the vafriable of interest. We
        will use this column to create another column of whether the betas are
        negative or not

    Returns
    -------
    pl.DataFrame
        returns the dataframe frame with the aforementioned transformations
    """
    # Ensure that the provided df has the correct values
    check_df_columns(df, pval_colname, beta_colname)

    df = df.filter(pl.col("converged")).with_columns(
        -np.log10(pl.col(pval_colname)).alias("neg_log10_p")
    )

    max_finite_val = (
        df.filter(pl.col("neg_log10_p").is_finite())
        .select(pl.col("neg_log10_p").max())
        .item()
        * 1.02
    )

    print(f"replacing infinite values in the dataframe with {max_finite_val}")

    df = (
        df.with_columns(
            pl.when(~pl.col("neg_log10_p").is_finite())
            .then(max_finite_val)
            .otherwise(pl.col("neg_log10_p"))
        )
        .with_columns(
            pl.when(pl.col(beta_colname) > 0)
            .then(pl.lit("Positive"))
            .otherwise(pl.lit("Negative"))
            .alias("direction")
        )
        .sort(["phecode_category", "phecode_description"])
        .with_row_index(name="index")
    )

    return FormattedDf(df, max_finite_val)


def generate_manhatten(
    formatted_results: FormattedDf,
    output_filename: Path | str,
    significance_threshold: float,
    dpi: int = 300,
    color_palette: list[tuple] | None = None,
) -> None:

    df = formatted_results.dataframe

    plt.figure(figsize=(16, 9))

    if color_palette is None:
        color_palette = determine_color_palatte(len(df["phecode_category"].unique()))

    # We need to format the dataframe
    markers = {"Positive": "^", "Negative": "v"}

    plot_data = df.to_pandas()

    sns.scatterplot(
        data=plot_data,
        x="index",
        y="neg_log10_p",
        hue="phecode_category",
        palette=color_palette,
        style="direction",
        markers=markers,
        s=80,
        alpha=1.0,  # Set alpha to 1.0 for maximum color saturation
        edgecolor="black",  # Black edge helps separate the colors further
        linewidth=0.5,
    )

    # Threshold lines
    plt.axhline(
        y=significance_threshold,
        color="#ff0000",
        linestyle="--",
        linewidth=1.5,
        label="Bonferroni",
    )

    plt.axhline(
        y=formatted_results.infinity_threshold,
        color="#1e90ff",
        linestyle="--",
        linewidth=1.5,
        label="infinity_threshold",
    )

    # generate the differnt category labels so everything aligns correctly on the x-axis
    label_df = (
        df.group_by("phecode_category")
        .agg(pl.col("index").median().alias("pos"))
        .sort("pos")
    )
    plt.xticks(
        label_df["pos"].to_list(),
        label_df["phecode_category"].to_list(),
        rotation=45,
        ha="right",
        fontsize=10,
    )

    plt.xlabel("Phecode Categories", fontsize=14)
    plt.ylabel(r"$-\log_{10}(P)$", fontsize=14)
    plt.title("PheWAS Results", fontsize=14)
    plt.legend(
        bbox_to_anchor=(1.01, 1),
        loc="upper left",
        borderaxespad=0,
        title="Category / Direction",
    )
    plt.tight_layout()
    plt.savefig(output_filename, dpi=dpi, bbox_inches="tight")


def check_df_columns(df: pl.DataFrame, pval_col: str, beta_col: str) -> None:
    """check if the expected columns are in the dataframe. If the expected columns
    are not then then we need to terminate the program

    Parameters
    ----------
    df : pl.DataFrame
        dataframe that has the results from the phewas.

    pval_col : str
        column that has the pvalues for the variable of interest

    beta_col : str
        column that has the betas for the variable of interest

    Raises
    ------
    ValueError
        if any of the expected columns are not found then we will raise a value error
        telling the user what the expected columns are
    """
    cols_to_search_for = [
        "phecode_category",
        "phecode_description",
        "converged",
        pval_col,
        beta_col,
    ]

    cols_present = [col not in df.columns for col in cols_to_search_for]

    if any(cols_present):
        err_msg = (
            "Did not find all the expected columns within the provided dataframe. Please make sure the following columns are in the dataframe: "
            + ", ".join(cols_present)
        )
        raise ValueError(err_msg)


def main() -> None:

    parser = argparse.ArgumentParser(
        description="CLI too to generate the manhattan plot after running the PheWAS",
        formatter_class=RichHelpFormatter,
        epilog="""
    Minimal Examples:
        %(prog)s  --input-file phewas_results.txt 
    """,
    )

    parser.add_argument(
        "--input-file",
        "-i",
        help="input file with the reusults from the PheWAS. This file should be tab separated and have the columns 'phecode_category', 'phecode_description', 'coverged'.",
    )

    parser.add_argument(
        "--output-file",
        "-o",
        type=Path,
        help="filepath to output the manhattan plot to. (default: %(default)s)",
        default=Path("test.png"),
    )

    parser.add_argument(
        "--pval-col",
        type=str,
        help="name of the column that has the pvalues for the variable of interest. (default: %(default)s)",
        default="pval",
    )

    parser.add_argument(
        "--beta-col",
        type=str,
        help="name of the column that has betas for the variables of interest. (default: %(default)s)",
        default="beta",
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="quality of the image to output. (default: %(default)s)",
    )

    args = parser.parse_args()

    # read in the dataframe
    df = pl.read_csv(args.input_file, separator="\t")

    significance_threshold = 0.05 / df.shape[0]
    formatted_df_results = format_df(df, args.pval_col, args.beta_col)

    generate_manhatten(
        formatted_df_results, args.output_file, significance_threshold, dpi=args.dpi
    )


if __name__ == "__main__":
    main()
