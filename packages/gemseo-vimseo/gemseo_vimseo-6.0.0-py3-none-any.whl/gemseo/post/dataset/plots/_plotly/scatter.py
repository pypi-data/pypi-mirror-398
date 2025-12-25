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
"""Scatter based on plotly."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Callable

import plotly.express as px
from numpy import array

from gemseo.post.dataset._trend import TREND_FUNCTIONS
from gemseo.post.dataset._trend import Trend
from gemseo.post.dataset.plots._plotly.plot import PlotlyPlot

if TYPE_CHECKING:
    from numpy.typing import ArrayLike
    from plotly.graph_objects import Figure


class Scatter(PlotlyPlot):
    """A scatter plot based on plotly."""

    def _create_figure(
        self,
        fig: Figure | None,
        x_values: ArrayLike,
        y_values: ArrayLike,
        x_name: str,
        y_name: str,
    ) -> Figure:
        """
        Args:
            x_values: The values on the x-axis.
            y_values: The values of the points on the y-axis.
        """  # noqa: D205 D212 D415
        coloring_variable = self._specific_settings.coloring_variable
        dataframe = self._common_dataset.copy()
        dataframe.columns = dataframe.get_columns(as_tuple=False)

        kwargs = {}
        kwargs["color"] = coloring_variable
        kwargs["color_continuous_scale"] = px.colors.sequential.Rainbow

        # TODO maybe it is less invasive to use numpy.squeeze instead of ravel (if we
        #  have vector elements, ravel will flatten the array of vectors.
        #  I am not sure it is what we want.
        fig = px.scatter(
            dataframe,
            x=x_name,
            y=y_name,
            **kwargs,
        )
        # fig.add_trace(
        #     Scatter(
        #         x=x_values.ravel(),
        #         y=y_values.ravel(),
        #         mode="markers",
        #         showlegend=True,
        #         name=self._specific_settings[1][0],
        #         marker=dict(
        #             color=
        #             self._common_dataset.get_view(variable_names=coloring_variable),
        #             colorscale = px.colors.sequential.Rainbow,
        #             showscale=True,
        #             colorbar_x=-0.15,
        #         )
        #     )
        # )
        # TODO colorize markers according to a variable.
        # TODO add trend line.
        # scatter.set_zorder(3)
        trend_function_creator = self._specific_settings.trend
        if trend_function_creator == Trend.IDENTITY:
            identity_cov = 0.1
            x_identity = array([min(x_values.ravel()), max(x_values.ravel())])

            fig.add_scatter(
                x=x_identity,
                y=x_identity,
                name="Identity_line",
                mode="lines",
                line={"color": "grey", "dash": "dash", "width": 2},
                showlegend=False,
            )

            fig.add_scatter(
                x=x_identity,
                y=x_identity * (1 + identity_cov),
                name=f"+{identity_cov * 100}% error",
                mode="lines",
                line={"color": "grey", "dash": "dot", "width": 2},
                showlegend=False,
            )

            fig.add_scatter(
                x=x_identity,
                y=x_identity * (1 - identity_cov),
                name=f"-{identity_cov * 100}% error",
                mode="lines",
                line={"color": "grey", "dash": "dot", "width": 2},
                showlegend=False,
            )

            fig.add_annotation(
                text=f"+{100 * identity_cov}%",
                x=max(x_identity) + 0.02 * abs(max(x_identity)),
                y=max(x_identity * (1 + identity_cov)),
                showarrow=False,
                font_size=12,
                xanchor="left",
            )

            fig.add_annotation(
                text=f"-{100 * identity_cov}%",
                x=max(x_identity) + 0.02 * abs(max(x_identity)),
                y=max(x_identity * (1 - identity_cov)),
                showarrow=False,
                font_size=12,
                xanchor="left",
            )
        elif trend_function_creator != Trend.NONE:
            if not isinstance(trend_function_creator, Callable):
                trend_function_creator = TREND_FUNCTIONS[trend_function_creator]

            trend_function = trend_function_creator(x_values[:, 0], y_values[:, 0])
            fig.add_scatter(
                x_values,
                trend_function(x_values),
                showlegend=False,
                line={
                    "dash": "dash",
                    "color": "gray",
                    "width": 2,
                },
            )

        fig.update_layout(
            title=self._common_settings.title,
            xaxis_title=self._common_settings.xlabel,
            yaxis_title=self._common_settings.ylabel,
        )
        return fig
