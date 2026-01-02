"""Shared statistical analysis schemas used by Figlinq clients and services."""

from __future__ import annotations

from typing import Any, Dict

ANALYSIS_SCHEMA_LIBRARY: Dict[str, Dict[str, Any]] = {
    "anova_oneway": {
        "default_spec": {
            "family": "parametric",
            "test": "anova_oneway",
            "mode": "unpaired",
            "data_mode": "tidy",
            "spec_version": "1.0",
            "params": {
                "alpha": 0.05,
                "nan_policy": "omit",
                "post_hoc": "bonferroni_t",
                "effect_size": "eta_omega",
            },
            "columns": {
                "value_col": None,
                "group_col": None,
            },
            "groups": {},
            "row_filter": {},
            "show_annotations": True,
        },
        "schema_md": None,
    },
    "t_test": {
        "default_spec": {
            "family": "parametric",
            "test": "t_test",
            "mode": "unpaired",
            "data_mode": "tidy",
            "spec_version": "1.0",
            "params": {
                "alpha": 0.05,
                "nan_policy": "omit",
                "alternative": "two-sided",
                "equal_var": True,
                "effect_size": "cohen_d",
            },
            "columns": {
                "value_col": None,
                "group_col": None,
                "x_col": None,
                "y_col": None,
                "value_col_a": None,
                "group_col_a": None,
                "value_col_b": None,
                "group_col_b": None,
            },
            "groups": {"a": None, "b": None},
            "row_filter": {},
            "show_annotations": False,
        },
        "schema_md": None,
    },
    "mann_whitney": {
        "default_spec": {
            "family": "nonparametric",
            "test": "mann_whitney",
            "mode": "unpaired",
            "data_mode": "tidy",
            "spec_version": "1.0",
            "params": {
                "alpha": 0.05,
                "nan_policy": "omit",
                "alternative": "two-sided",
            },
            "columns": {
                "value_col": None,
                "group_col": None,
                "x_col": None,
                "y_col": None,
                "value_col_a": None,
                "group_col_a": None,
                "value_col_b": None,
                "group_col_b": None,
            },
            "groups": {"a": None, "b": None},
            "row_filter": {},
            "show_annotations": False,
        },
        "schema_md": None,
    },
    "wilcoxon_signed_rank": {
        "default_spec": {
            "family": "nonparametric",
            "test": "wilcoxon_signed_rank",
            "mode": "paired",
            "data_mode": "two_columns",
            "spec_version": "1.0",
            "params": {
                "alpha": 0.05,
                "nan_policy": "omit",
                "zero_method": "wilcox",
                "mode": "auto",  # computation mode: auto|exact|approx
                "continuity_correction": False,
                "effect_size": "rank_biserial",
                "hl_estimator": True,
                "alternative": "two-sided",
            },
            "columns": {
                "value_col": None,
                "group_col": None,
                "x_col": None,
                "y_col": None,
                "value_col_a": None,
                "group_col_a": None,
                "value_col_b": None,
                "group_col_b": None,
            },
            "groups": {"a": None, "b": None},
            "row_filter": {},
            "show_annotations": True,
        },
        "schema_md": None,
    },
    "kruskal_wallis": {
        "default_spec": {
            "family": "non_parametric",
            "test": "kruskal_wallis",
            "mode": "unpaired",
            "data_mode": "tidy",
            "spec_version": "1.0",
            "params": {
                "alpha": 0.05,
                "nan_policy": "omit",
                "post_hoc": None,
                "p_adjust": "bonferroni",
                "effect_size": "epsilon2",
            },
            "columns": {
                "value_col": None,
                "group_col": None,
            },
            "groups": None,
            "row_filter": {},
            "show_annotations": True,
        },
        "schema_md": None,
    },
}

COMMON_DATA_SCHEMA_MD = (
    "data_mode: data layout mode; options: tidy, two_columns; default: tidy\n"
    "x_col / y_col: ID of two data columns to compare when using data_mode=two_columns\n"
    "value_col_a / value_col_b: ID of columns with values for sample A/B when using data_mode=tidy\n"
    "group_col_a / group_col_b: ID of columns with group labels for sample A/B when using data_mode=tidy\n"
    "group_a / group_b: label identifying the groups to compare for sample A/B when using data_mode=tidy\n"
)

COMMON_NOTE_MD = (
    "Important: All column IDs must be provided in the format 'username:integer:uuid'."
)

ANOVA_ONEWAY_SCHEMA_MD = (
    "# Parameters for creating one-way ANOVA statistics on figlinq grid columns\n"
    "test: test type; options: anova_oneway; default: anova_oneway\n"
    "mode: test mode; options: paired, unpaired; default: unpaired\n"
    "value_col: ID of column with values; required: \n"
    "group_col: ID of column with group labels; required: \n"
    "alpha: significance level; default: 0.05\n"
    "nan_policy: NaN handling policy; options: omit, raise; default: omit\n"
    "post_hoc: post-hoc correction; options: None, tukey, bonferroni_t; default: bonferroni_t\n"
    "effect_size: effect size metric; options: None, eta_omega; default: eta_omega\n"
    f"{COMMON_NOTE_MD}"
)


T_TEST_SCHEMA_MD = (
    "# Parameters for running two-sample t-tests on figlinq grid columns\n"
    "test: test type; options: t_test; default: t_test\n"
    "mode: analysis mode; options: paired, unpaired; default: unpaired\n"
    "alpha: significance level; default: 0.05\n"
    "alternative: hypothesis direction; options: two-sided, less, greater; default: two-sided\n"
    "equal_var: assume equal variances for unpaired mode; options: true, false; default: true\n"
    "nan_policy: NaN handling policy; options: omit, raise; default: omit\n"
    "effect_size: effect size metric; options: None, cohen_d; default: cohen_d\n"
    f"{COMMON_DATA_SCHEMA_MD}"
    f"{COMMON_NOTE_MD}"
)


MANN_WHITNEY_SCHEMA_MD = (
    "# Parameters for running Mann-Whitney U tests on figlinq grid columns\n"
    "test: test type; options: mann_whitney; default: mann_whitney\n"
    "mode: analysis mode; fixed to unpaired\n"
    "alpha: significance level; default: 0.05\n"
    "alternative: hypothesis direction; options: two-sided, less, greater; default: two-sided\n"
    "nan_policy: NaN handling policy; options: omit, raise; default: omit\n"
    f"{COMMON_DATA_SCHEMA_MD}"
    f"{COMMON_NOTE_MD}"
)

WILCOXON_SIGNED_RANK_SCHEMA_MD = (
    "# Parameters for running Wilcoxon signed-rank tests on figlinq grid columns\n"
    "test: test type; options: wilcoxon_signed_rank; default: wilcoxon_signed_rank\n"
    "mode: analysis mode; fixed to paired\n"
    "alpha: significance level; default: 0.05\n"
    "alternative: hypothesis direction; options: two-sided, less, greater; default: two-sided\n"
    "nan_policy: NaN handling policy; options: omit, raise; default: omit\n"
    "zero_method: handling of zero differences; options: wilcox, pratt, zsplit; default: wilcox\n"
    "computation_mode: exact p-value when possible vs normal approximation; options: auto, exact, approx; default: auto\n"
    "continuity_correction: apply continuity correction in normal approximation; options: true, false; default: false\n"
    "effect_size: effect size metric; options: None, rank_biserial, r; default: rank_biserial\n"
    "hl_estimator: compute Hodges-Lehmann location shift estimate; options: true, false; default: true\n"
    "\n"
    "Data input modes:\n"
    "* two_columns: provide paired numeric columns x_col and y_col. Pairs are matched by row order after filtering.\n"
    "* paired_tidy: provide a single value_col and a group_col, and set group_a/group_b names for the paired conditions.\n"
    f"{COMMON_NOTE_MD}"
)

KRUSKAL_WALLIS_SCHEMA_MD = (
    "# Parameters for running Kruskal-Wallis H tests on figlinq grid columns\n"
    "test: test type; options: kruskal_wallis; default: kruskal_wallis\n"
    "mode: analysis mode; fixed to unpaired\n"
    "alpha: significance level; default: 0.05\n"
    "nan_policy: NaN handling policy; options: omit, raise; default: omit\n"
    "post_hoc: pairwise follow-up test; options: None, pairwise_mwu; default: None\n"
    "p_adjust: adjustment for post-hoc p-values when post_hoc=pairwise_mwu; options: bonferroni, holm, holm-sidak, bh; default: bonferroni\n"
    "effect_size: effect size metric selection; options: none, epsilon2, eta2H, both; default: epsilon2\n"
    "value_col: ID of numeric column with observations; required\n"
    "group_col: ID of categorical column identifying groups; required\n"
    "data_mode: data layout mode; fixed to tidy\n"
    f"{COMMON_NOTE_MD}"
)


ANALYSIS_SCHEMA_LIBRARY["anova_oneway"]["schema_md"] = ANOVA_ONEWAY_SCHEMA_MD
ANALYSIS_SCHEMA_LIBRARY["t_test"]["schema_md"] = T_TEST_SCHEMA_MD
ANALYSIS_SCHEMA_LIBRARY["mann_whitney"]["schema_md"] = MANN_WHITNEY_SCHEMA_MD
ANALYSIS_SCHEMA_LIBRARY["wilcoxon_signed_rank"]["schema_md"] = WILCOXON_SIGNED_RANK_SCHEMA_MD
ANALYSIS_SCHEMA_LIBRARY["kruskal_wallis"]["schema_md"] = KRUSKAL_WALLIS_SCHEMA_MD


SUPPORTED_TESTS = tuple(sorted(ANALYSIS_SCHEMA_LIBRARY.keys()))


def get_analysis_schema_markdown(analysis_type: str) -> str:
    key = (analysis_type or "").strip()
    if not key:
        raise KeyError("analysis_type")
    schema = ANALYSIS_SCHEMA_LIBRARY.get(key)
    if schema is None:
        raise KeyError(key)
    schema_md = schema.get("schema_md")
    if not schema_md:
        raise KeyError(f"schema_md:{key}")
    return schema_md
