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
from __future__ import annotations

import pytest

from gemseo.algos.parameter_space import ParameterSpace
from gemseo.uncertainty.distributions.base_distribution import DistributionSettings
from gemseo.uncertainty.distributions.base_distribution import (
    InterfacedDistributionSettings,
)


@pytest.mark.parametrize(
    ("interface_type", "distribution_name", "settings"),
    [
        ("kwargs", "OTNormalDistribution", {"sigma": 0.05, "mu": 1.0}),
        ("interfaced_distribution", "Normal", (1.0, 0.05)),
        (
            "pydantic_interfaced_distribution",
            "",
            InterfacedDistributionSettings(name="Normal", parameters=(1.0, 0.05)),
        ),
        (
            "pydantic_interfaced_distribution",
            "",
            InterfacedDistributionSettings(
                name="Normal", parameters=(1.0, 0.05), lower_bound=-1.0, upper_bound=1.0
            ),
        ),
        (
            "pydantic_distribution",
            "OTNormalDistribution",
            DistributionSettings(name="Normal", sigma=0.05, mu=1.0),
        ),
        (
            "pydantic_distribution",
            "OTUniformDistribution",
            DistributionSettings(name="Uniform", lower=-1.0, upper=2.0),
        ),
        (
            "pydantic_distribution",
            "OTTriangularDistribution",
            DistributionSettings(name="Triangular", lower=-1.0, upper=1.0, mode=0.0),
        ),
        (
            "pydantic_interfaced_distribution",
            "OTWeibullDistribution",
            InterfacedDistributionSettings(
                name="WeibullMin", parameters=(1.0, 2.0, 0.0)
            ),
        ),
        (
            "pydantic_interfaced_distribution",
            "OTExponentialDistribution",
            InterfacedDistributionSettings(name="Exponential", parameters=(1.0, 0.0)),
        ),
        (
            "pydantic_distribution",
            "OTNormalDistribution",
            DistributionSettings(
                name="Normal", sigma=0.05, mu=1.0, lower_bound=0.9, upper_bound=1.1
            ),
        ),
        (
            "pydantic_distribution",
            "OTUniformDistribution",
            DistributionSettings(
                name="Uniform", lower=0.0, upper=2.0, lower_bound=0.5, upper_bound=1.5
            ),
        ),
        (
            "pydantic_distribution",
            "OTTriangularDistribution",
            DistributionSettings(
                name="Triangular",
                lower=-1.0,
                upper=1.0,
                mode=0.0,
                lower_bound=-0.5,
                upper_bound=0.5,
            ),
        ),
    ],
)
def test_distribution_settings(tmp_wd, interface_type, distribution_name, settings):
    """Check the instantiation of a gemseo OT distribution."""
    parameter_space = ParameterSpace()
    if interface_type == "interfaced_distribution":
        parameter_space.add_random_variable(
            "x1",
            "OTDistribution",
            interfaced_distribution=distribution_name,
            interfaced_distribution_parameters=settings,
        )
    elif interface_type == "kwargs":
        parameter_space.add_random_variable("x1", distribution_name, **settings)
    elif interface_type == "pydantic_interfaced_distribution":
        parameter_space.add_random_variable("x1", "OTDistribution", settings=settings)
    elif interface_type == "pydantic_distribution":
        parameter_space.add_random_variable("x1", distribution_name, settings=settings)

    settings_from_distribution = (
        parameter_space.distributions["x1"].marginals[0].settings
    )
    if (
        interface_type == "pydantic_distribution"
        or interface_type == "pydantic_interfaced_distribution"
    ):
        settings_dict = settings.model_dump()
        for k, v in settings_dict.items():
            assert v == settings_from_distribution[k]
    elif interface_type == "kwargs":
        for k, v in settings.items():
            assert v == settings_from_distribution[k]
    elif interface_type == "interfaced_distribution":
        # Does not seem testable
        assert 1
