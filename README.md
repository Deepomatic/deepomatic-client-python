# deepomatic-client-python

Deepomatic API Client for Python.

This client have been made in order to help you integrating our services within your apps in python.

Tested on python 2.7 & 3.6.

<br/>

# API Documentation

https://api.deepomatic.com/
<br/>

# Requirements

```
sudo pip install -r requirements.txt
```
<br/>

# Client

Initialize a client.
Does not make any call to the server.
```python
import deepomatic

# You should find your app_id and api_key in your account on developpers.deepomatic.com
client = deepomatic.Client(app_id, api_key)
```

### Client methods

All client methods can be found in [deepomatic/core/client.py](/deepomatic/core/client.py) and detail for each type of resource is located in [deepomatic/resources](/deepomatic/resources)

### Examples

You will find examples of usage in [demo.py](/demo.py)

# Bugs

### support@deepomatic.com
