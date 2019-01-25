# deepomatic-client-python

[Deepomatic](https://www.deepomatic.com) API Client for Python.

This client have been made in order to help you integrating our services within your apps in python.

Tested on python 2.7, 3.4, 3.5, 3.6.

# API Documentation

https://developers.deepomatic.com/docs/v0.7

# Installation

```bash
pip install deepomatic-api
```

# Client

Initialize a client.
Does not make any call to the server.

```python
from deepomatic.api.client import Client

# You should find your app_id and api_key in your account on https://developers.deepomatic.com/dashboard
client = Client(app_id, api_key)
```

### Client methods

All client methods can be found in [deepomatic/api/client.py](deepomatic/api/client.py) and detail for each type of resource is located in [deepomatic/api/resources](deepomatic/api/resources).

### Examples

You will find examples of usage in [demo.py](demo.py).

# Bugs

Please send bug reports to support@deepomatic.com or open an issue here.
