# deepomatic-client-python

[Deepomatic](https://www.deepomatic.com) API Client for Python.

This client have been made in order to help you integrating our services within your apps in python.

Tested on python 2.7, 3.4, 3.5, 3.6.

# API Documentation

https://docs.deepomatic.com/deepomatic-api-v0-7

# Installation

```bash
pip install deepomatic-api
```

# Client

Initialize a client.
Does not make any call to the server.

```python
from deepomatic.api.client import Client

# If you don't have your credentials, contact us at support@deepomatic.com
client = Client(app_id, api_key, user_agent_prefix='my-app/1.0.0')
```

### Client methods

All client methods can be found in [deepomatic/api/client.py](deepomatic/api/client.py) and detail for each type of resource is located in [deepomatic/api/resources](deepomatic/api/resources).

### Examples

You will find examples of usage in [demo.py](demo.py).

# Bugs

Please send bug reports to support@deepomatic.com or open an issue here.
