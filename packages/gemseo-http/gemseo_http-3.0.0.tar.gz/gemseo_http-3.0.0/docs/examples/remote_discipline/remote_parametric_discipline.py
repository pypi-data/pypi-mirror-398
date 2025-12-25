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
Remote discipline execution
===========================

This example demonstrates how to execute a remote discipline using the
`HTTPDiscipline` class from the `gemseo_http` package.

"""

from __future__ import annotations

from gemseo import configure_logger
from numpy import array

from gemseo_http.http_discipline import HTTPDiscipline

# %%
# Configure the logger for the http_discipline module.
configure_logger(logger_name="gemseo_http.disciplines.http_discipline", level="DEBUG")

# %%
# Instantiate the `HTTPDiscipline` class for the remote discipline.
# Use options to pass to the remote discipline constructor
expressions = {"expressions": {"y_1": "2*x**2", "y_2": "4*x**2+5+z**3"}}
remote_disc = HTTPDiscipline(
    name="RemoteAnalytic",
    class_name="AnalyticDiscipline",
    discipline_options=expressions,
    url="http://localhost",
    port=8000,
    user="test",
    password="test",
    linearize_after_execution=True,
    linearize_options={"compute_all_jacobians": True},
    is_asynchronous=True,
)


# %%
# Execute the remote discipline with default input data.
data = {"x": array([1.0]), "z": array([2.0])}
remote_disc.execute(data)
print(data)

# %%
# Linearize the discipline after execution.
# In this specific case, the jacobian has been computed during the execution,
# and is cached.
# Then, the linearization of the discipline will lead to a cache hit on the local discipline.
jac = remote_disc.linearize(data, compute_all_jacobians=True)
print(jac)
