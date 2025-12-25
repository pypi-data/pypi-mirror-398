# Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""Scatter matrix based on plotly."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.express as px
import plotly.figure_factory as ff

from gemseo.post.dataset.plots._plotly.plot import PlotlyPlot

if TYPE_CHECKING:
    from matplotlib.figure import Figure


class ScatterMatrix(PlotlyPlot):
    """Scatter matrix based on plotly."""

    def _create_figure(
        self,
        fig: Figure | None,
        classifier_column: tuple[str, str, int],
        coloring_column: tuple[str, str, int],
    ) -> list[Figure]:
        variable_names = self._specific_settings.variable_names
        coloring_variable = self._specific_settings.coloring_variable
        if len(variable_names) == 0:
            variable_names = self._common_dataset.variable_names

        if (
            coloring_variable
            and len(variable_names) > 0
            and coloring_variable not in variable_names
        ):
            variable_names.append(coloring_variable)

        dataframe = self._common_dataset.get_view(variable_names=variable_names)

        kwargs = {}
        if coloring_variable is not None:
            kwargs["color"] = coloring_variable
            kwargs["color_continuous_scale"] = px.colors.sequential.Rainbow
            df = dataframe.copy()
            df.columns = df.get_columns(as_tuple=False)
            df = df.sort_values(coloring_variable, ascending=True)
        else:
            df = dataframe.copy()
            df.columns = df.get_columns(as_tuple=False)

        dimension_names = list(df.columns.values)
        dimension_names.remove(coloring_variable)
        # fig = px.scatter_matrix(
        #     df,
        #     dimensions=dimension_names,
        #     **kwargs,
        # )

        return ff.create_scatterplotmatrix(
            df,
            diag="histogram",
            index=coloring_variable,
            height=800,
            width=800,
            colormap=px.colors.sequential.Rainbow,
            title=self._common_settings.title,
            text=df[coloring_variable],
        )
        #
        # import plotly.graph_objects as go
        # fig = go.Figure(data=go.Splom(
        #     dimensions=[dict(label=name, values=df[name])
        #     for name in dimension_names],
        #     showupperhalf=False,
        #     text=df[coloring_variable],
        #     marker=dict(
        #         # color=df[coloring_variable],
        #         showscale=True,
        #         line_color="white",
        #         line_width=0.5),
        # ))

        # if self._specific_settings.axis_labels_as_keys:
        #     # get labels of dimensions in splom
        #     labels = [d.label for d in fig.data[0].dimensions]
        #
        #     # replace labels in splom with identifier
        #     fig.update_traces(
        #         dimensions=[
        #             d.update(label=chr(ord("a") + n))
        #             for n, d in enumerate(fig.data[0].dimensions)
        #         ]
        #     )
        #
        #     # add a key for labels
        #     for n, label in enumerate(labels):
        #         fig.add_annotation(
        #             x=(n) / (len(labels) - 1) if len(labels) > 1 else 0,
        #             y=1.02,
        #             xref="paper",
        #             yref="paper",
        #             text=f"{chr(ord('a') + n)}: {label}",
        #             align="center",
        #             showarrow=False,
        #             yanchor="bottom",
        #             textangle=-10,
        #         )
