# deepomatic-client-python

[Deepomatic](https://www.deepomatic.com) API Client for Python.

This client have been made in order to help you integrating our services within your apps in python.

Tested on python 2.7 & 3.5.

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
import deepomatic

# You should find your app_id and api_key in your account on https://developers.deepomatic.com/dashboard
client = deepomatic.Client(app_id, api_key)
```

### Client methods

All client methods can be found in [deepomatic/client.py](deepomatic/client.py) and detail for each type of resource is located in [deepomatic/resources](deepomatic/resources).

### Examples

You will find examples of usage in [demo.py](demo.py).

# Bugs

Please send bug reports to support@deepomatic.com or open an issue here.
