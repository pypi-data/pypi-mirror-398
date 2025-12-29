# -*- coding: UTF-8 -*-

import matplotlib

from ._graph_ import graph, communities_graph, network_two_types
from ._heat_map_ import heatmap, heatmap_annotation

from ._scatter_ import (
    scatter_base,
    scatter_atac,
    scatter_trait,
    volcano_base,
    manhattan_causal_variant,
    pseudo_time_score
)

from ._violin_ import violin_base, violin_trait
from ._box_ import box_base, box_trait
from ._kde_ import kde
from ._line_ import stability_line
from ._bar_ import bar_trait, class_bar, bar, two_bar, bar_significance
from ._barcode_ import barcode_base, barcode_trait
from ._pie_ import pie_trait, pie_label, base_pie
from ._bubble_ import bubble
from ._radar_ import radar, radar_trait
from ._venn_ import three_venn, two_venn

from ._core_ import (
    trs_plot,
    group_heatmap,
    map_df_plot,
    rate_bar_plot,
    init_score_plot,
    cell_cell_plot,
    data_plot,
    complete_ratio,
    rate_circular_bar_plot
)

matplotlib.set_loglevel("error")

__all__ = [
    "graph",
    "communities_graph",
    "network_two_types",
    "heatmap",
    "volcano_base",
    "heatmap_annotation",
    "scatter_base",
    "scatter_atac",
    "scatter_trait",
    "violin_base",
    "violin_trait",
    "manhattan_causal_variant",
    "pseudo_time_score",
    "barcode_base",
    "barcode_trait",
    "box_base",
    "box_trait",
    "bar_significance",
    "bar",
    "pie_trait",
    "pie_label",
    "two_bar",
    "kde",
    "stability_line",
    "class_bar",
    "bar_trait",
    "bubble",
    "group_heatmap",
    "map_df_plot",
    "rate_bar_plot",
    "trs_plot",
    "init_score_plot",
    "cell_cell_plot",
    "data_plot",
    "complete_ratio",
    "rate_circular_bar_plot",
    "radar",
    "radar_trait",
    "three_venn",
    "two_venn"
]
