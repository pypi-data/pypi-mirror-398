from __future__ import absolute_import
import sys

from . import plotly, dashboard_objs, grid_objs, session, tools
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

# Register figlinq.grid_objs as chart_studio.grid_objs in sys.modules
# so that Plotly's validators recognize our Column objects
sys.modules['chart_studio.grid_objs'] = grid_objs
sys.modules['chart_studio'] = sys.modules[__name__]

__all__ = [
	"plotly",
	"dashboard_objs",
	"grid_objs",
	"session",
	"tools",
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
