"""
figlinq
======

This module defines functionality that requires interaction between your
local machine and Figlinq.

"""

from .figlinq import (
    upload,
    download,
    find_file,
    get_plot_template,
    apply_plot_template,
    apply_template,
    Grid,
    Column,
    analysis_ops,
    supported_analysis_tests,
    get_analysis_schema,
    list_analyses,
    create_analysis,
    delete_analysis,
    figure,
)

__all__ = [
    "upload",
    "download",
    "find_file",
    "get_plot_template",
    "apply_plot_template",
    "apply_template",
    "Grid",
    "Column",
    "analysis_ops",
    "supported_analysis_tests",
    "get_analysis_schema",
    "list_analyses",
    "create_analysis",
    "delete_analysis",
    "figure",
]
