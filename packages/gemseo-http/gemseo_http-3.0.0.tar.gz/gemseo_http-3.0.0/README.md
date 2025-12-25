<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

# gemseo-http

[![PyPI - License](https://img.shields.io/pypi/l/gemseo-http)](https://www.gnu.org/licenses/lgpl-3.0.en.html)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gemseo-http)](https://pypi.org/project/gemseo-http/)
[![PyPI](https://img.shields.io/pypi/v/gemseo-http)](https://pypi.org/project/gemseo-http/)
[![Codecov branch](https://img.shields.io/codecov/c/gitlab/gemseo:dev/gemseo-http/develop)](https://app.codecov.io/gl/gemseo:dev/gemseo-http)

## Overview

`gemseo-http` is a [GEMSEO](https://gemseo.readthedocs.io/en/stable/) plugin that exposes GEMSEO disciplines as RESTful web services. It bridges the gap between local MDO processes and remote computing resources by providing a seamless client-server interface.

### Main Capabilities

1.  **Expose GEMSEO Disciplines as Web Services:**
    *   Make existing GEMSEO disciplines into accessible HTTP endpoints.
    *   Execute and linearize disciplines remotely with support for both synchronous and asynchronous modes.
2.  **Use Remote Disciplines Locally:**
    *   Use the `HTTPDiscipline` class as a local proxy for remote services.
    *   Automatic configuration via service discovery (the proxy queries the remote service for its grammars).

## Installation

### Client Installation

The `HTTPDiscipline` acts as a remote discipline proxy, allowing you to connect to a GEMSEO HTTP service.

To install the latest stable version of the client:

```bash
pip install gemseo-http
```

### Server Installation

If you intend to host GEMSEO disciplines as services, you need to install the server-side dependencies:

```bash
pip install gemseo-http[server]
```

## Key Features

*   **Secure Authentication:** Built-in support for OAuth2 with JWT (JSON Web Tokens) to ensure secure access.
*   **Interactive API Documentation:** Automatically generated Swagger UI (available at `/docs`) for exploring and testing the API.
*   **Automated File Handling:** Transparent management of file transfers between client and server during discipline execution.
*   **Scalable Asynchronous Execution:** Integration with [Huey](https://huey.readthedocs.io/en/latest/) for background job processing, allowing for long-running tasks without blocking the web service.
*   **Efficient Data Retrieval:** Support for long-polling to retrieve results from asynchronous executions.

## Documentation

For detailed installation instructions, user guides, and API reference, please visit the [official documentation](https://gemseo.gitlab.io/gemseo-http).


## Bugs and questions

Please use the [gitlab issue tracker](https://gitlab.com/gemseo/dev/gemseo-http/-/issues)
to submit bugs or questions.

## Contributing

See the [contributing section of GEMSEO](https://gemseo.readthedocs.io/en/stable/software/developing.html#dev).

## Contributors

- Jean-Christophe Giret
- Antoine Dechaume
