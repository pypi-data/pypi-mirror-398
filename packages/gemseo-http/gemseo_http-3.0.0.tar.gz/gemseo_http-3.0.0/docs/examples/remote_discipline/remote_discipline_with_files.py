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
Remote discipline execution with file transfers
===============================================

This example demonstrates how to execute a remote discipline using the
`HTTPDiscipline` class from the `gemseo_http` package.
"""

from __future__ import annotations

from numpy import array

from gemseo_http.http_discipline import HTTPDiscipline

# %%
# We instantiate the `HTTPDiscipline` class for the remote discipline.
# We assume that the distant discipline has a long lead-time,
# and thus we ask for an asynchronous execution.
# We use the long polling mechanism to wait for the discipline to finish its execution,
# with a long-polling wait time of 10 seconds.
# The `inputs_to_upload` and `outputs_to_download` arguments are used to specify
# the input variables that contain file paths to be transferred from the client
# to the server, and vice versa.

remote_disc = HTTPDiscipline(
    name="RemoteSellar1WithFile",
    class_name="Sellar1",
    url="http://localhost",
    port=8000,
    user="test",
    password="test",
    is_asynchronous=True,
    file_paths_to_upload=["data/test.pdf"],
    file_paths_to_download=["test.pdf"],
)

data = {"x_shared": array([1.0, 2.0]), "x_local": 0.0, "y_2": 0.0}
out = remote_disc.execute(data)
