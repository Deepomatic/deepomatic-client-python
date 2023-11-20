# deepomatic-client-python

[Deepomatic](https://www.deepomatic.com) API Client for Python.

This client have been made in order to help you integrating our services within your apps in python.

Tested on python 3.8, 3.9, 3.10, 3.11.

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
client = Client(api_key=api_key, user_agent_prefix='my-app/1.0.0')
```
> app_id is now optional but if you don't put it, you have to ensure that the api_key is a named parameter to the function 

### Client methods

All client methods can be found in [deepomatic/api/client.py](deepomatic/api/client.py) and detail for each type of resource is located in [deepomatic/api/resources](deepomatic/api/resources).

### Examples

You will find examples of usage in [demo.py](demo.py).
