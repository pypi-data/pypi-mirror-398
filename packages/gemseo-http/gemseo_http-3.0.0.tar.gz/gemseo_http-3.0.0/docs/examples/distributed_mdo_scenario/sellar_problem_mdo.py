# Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com
#
# This work is licensed under a BSD 0-Clause License.
#
# Permission to use, copy, modify, and/or distribute this software
# for any purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
# FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
# WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
Sellar problem with Sellar2 discipline remote
=============================================

This script defines and solves the Sellar problem, with Sellar2 discipline remote.

The Sellar problem is a well-known benchmark test for optimization algorithms
applied to MDO problems. It consists of three disciplines that are coupled:
1. Sellar1
2. Sellar2
3. SellarSystem

In this example, we demonstrate how one of the disciplines (`Sellar2`) can be managed
remotely using the `HTTPDiscipline` class from the `gemseo_http` package. This enables
remote computation by sending discipline-specific input data to an HTTP-based service,
executing the discipline remotely, and retrieving the results back to the local system.
"""

from __future__ import annotations

import logging

from gemseo import OptimizationProblem
from gemseo import configure_logger
from gemseo import create_design_space
from gemseo import create_discipline
from gemseo import create_scenario
from numpy import array
from numpy import ones

from gemseo_http.http_discipline import HTTPDiscipline

# %%
# Step 1: Create the Sellar disciplines (`Sellar1` and `SellarSystem`) locally.
# These are executed directly in the local environment.
configure_logger()
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

sellar1, sellar_system = create_discipline(["Sellar1", "SellarSystem"])

# %%
# Step 2: Configure the `Sellar2` discipline to be executed remotely.
# The `HTTPDiscipline` acts as a proxy for the remote discipline, handling:
# - Authentication with the remote service through a username and password.
# - Sending input data to the HTTP service endpoint.
# - Receiving output data from the HTTP service.
#
# NOTE: The current configuration uses a mock HTTP service (`url` and `port`).
#       In a real-world scenario, ensure these are correctly set for the actual remote server.
# Key Explanation of HTTPDiscipline:
sellar2 = HTTPDiscipline(
    name="RemoteSellar2",
    class_name="Sellar2",
    url="http://localhost",
    port=8000,
    user="test",
    password="test",
)

# %%
# Step 3: Make a list of all the disciplines into a single list for the MDO process.
# As the sellar2 object is a plain discipline, it can be mixed with the other disciplines.
disciplines = [sellar1, sellar2, sellar_system]

# %%
# Step 4: Define the optimization problem.

design_space = create_design_space()
design_space.add_variable("x_local", lower_bound=0.0, upper_bound=10.0, value=ones(1))
design_space.add_variable(
    "x_shared",
    2,
    lower_bound=(-10, 0.0),
    upper_bound=(10.0, 10.0),
    value=array([4.0, 3.0]),
)
design_space.add_variable("y_1", lower_bound=-100.0, upper_bound=100.0, value=ones(1))
design_space.add_variable("y_2", lower_bound=-100.0, upper_bound=100.0, value=ones(1))

scenario = create_scenario(
    disciplines, formulation="MDF", objective_name="obj", design_space=design_space
)
scenario.add_constraint("c_1", OptimizationProblem.ConstraintType.INEQ)
scenario.add_constraint("c_2", OptimizationProblem.ConstraintType.INEQ)

# %%
# Step 5: Execute the MDO scenario.
scenario.execute(input_data={"max_iter": 100, "algo": "NLOPT_SLSQP"})
