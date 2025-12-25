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

from numpy import array

from gemseo_http.http_discipline import HTTPDiscipline

# %%
# Instantiate the `HTTPDiscipline` class for the remote discipline.
# The `user` and `password` arguments are used for authentication.
# The `linearize_after_execution` argument is used to linearize the discipline after execution.
# It enables to cache the jacobian
remote_sellar_system_disc = HTTPDiscipline(
    name="RemoteSellarSystem",
    class_name="SellarSystem",
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
input_data = {"x_local": 1.0, "x_shared": array([1.0, 2.0]), "y_1": 2.0, "y_2": 3.0}
output = remote_sellar_system_disc.execute(input_data)
print(output)

# %%
# Linearize the discipline after execution.
# In this specific case, the jacobian has been computed during the execution
# and is cached.
# Then, the linearization of the discipline will lead to a cache hit on the local discipline.
jac = remote_sellar_system_disc.linearize(input_data, compute_all_jacobians=True)
print(jac)
