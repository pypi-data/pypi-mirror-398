<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

## HTTPDiscipline: A Client for the GEMSEO HTTP Web Service

The [HTTPDiscipline][gemseo_http.http_discipline.HTTPDiscipline] is a proxy class that allows you to connect to a remote GEMSEO HTTP service as if it were a local discipline.

### Key Features

- **Automatic Configuration**: The discipline configures itself by querying the remote service's API to discover its input and output grammars.
- **Transparent Execution**: Triggering the `execute()` method on the client sends a request to the remote server.
- **Automatic File Handling**: Any files required for the execution are automatically transferred back and forth between the client and the server, transparently to the user.

### Usage Example

The following example demonstrates how to use the `HTTPDiscipline` to execute a remote discipline that involves file transfers:

```python
import os
from pathlib import Path
from gemseo.api import create_discipline
from gemseo.core.chains.chain import MDOChain
from numpy import array
from gemseo_http.http_discipline import HTTPDiscipline

# In this example, we assume that a GEMSEO HTTP service is running at the following URL.
service_base_url = "https://gaas.pf.irt-saintexupery.com"
port = 443

# Define the local paths for file transfers
DIRPATH = Path(os.path.abspath(__file__)).parent
input_file_path = str(DIRPATH / "data" / "test.pdf")

# Instantiate the HTTPDiscipline
discipline = HTTPDiscipline(
    name="DistantSellar1WithFile",
    class_name="Sellar1File",  # The name of the class on the server side
    url=service_base_url,
    port=port,
    user="username",
    password="password",
    inputs_to_upload=["x_shared_file"],   # Input keys that are files
    outputs_to_download=["y_1_file"],     # Output keys that are files
    file_paths_to_upload=[input_file_path],
    file_paths_to_download=["test.pdf"]
)

# You can integrate the HTTPDiscipline into a MDOChain just like any other discipline
# chain = MDOChain([other_discipline, discipline])
# data = {"x": array([1.0])}
# out = chain.execute(data)
```

Other examples can be found in the [examples](/gemseo-http/generated/examples/remote_discipline) folder.
