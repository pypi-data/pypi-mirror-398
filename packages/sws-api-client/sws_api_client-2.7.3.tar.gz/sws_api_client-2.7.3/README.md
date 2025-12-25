# SWS API Client

This library provides the user with a set of useful tools to easily interact with the FAO SWS (Statistical Working System) REST APIs.

## Installation

The module is available on Pypi:

```bash
python -m pip install sws_api_client
```

The library requires Python 3.9+.

## Usage

To use the package the user needs to create an instance of the SwsApiClient class, provide it with the necessary parameters and execute the methods to query the specific endpoints.  

### Instantiate the client locally

There are three methods to instantiate the client:

#### 1. Pass the `sws_endpoint` and the `access_token` to the constructor

```python
from sws_api_client import SwsApiClient

sws_client = SwsApiClient(sws_endpoint="<sws_endpoint>", access_token="<access_token>")
```

#### 2. Pass to `sws_endpoint` and the `access_token` as named arguments

We need to execute the script from command line passing `--sws_endpoint` and `--access_token` as arguments:

```bash
python script.py --sws_endpoint <endpoint> --access_token <test_access_token>
```

And instantiate the client in our script with the class method `from_args`:

```python
from sws_api_client import SwsApiClient

sws_client = SwsApiClient.from_args()
```

#### 3. Create a conf file where to store the arguments

We need to create a conf file (default name: `"conf_sws_api_client.json"`) with the following structure:

```json
{
    "sws_endpoint": "https://sws.dev.fao.org",
    "sws_token": "XXX",
    "current_task_id": "XXX",
    "current_execution_id": "XXX",
    "authclient": {
        "clientId": "XXX",
        "clientSecret": "XXX",
        "tokenEndpoint": "https://fao-dev.auth.eu-west-1.amazoncognito.com/oauth2/token",
        "scope": "sws/user"
    }
}
```


And instantiate the client in our script with the class method `auto`:

```python
from sws_api_client import SwsApiClient

sws_client = SwsApiClient.auto()
```


Behind the scene it will automatically detect the fact that you are in debug mode and it will instanciate the client using the `from_conf` method

### Instantiate the client in a SWS plugin

When working withing a SWS plugin instantiate the client as:

```python
from sws_api_client import SwsApiClient

sws_client = SwsApiClient.auto()
```

Behind the scene it will automatically detect the fact that you are in a SWS plugin and it will instanciate the client using the `from_env` method

### Instantiate the client using env variables

You can also instantiate the client using the following environment variables:

```bash
export SWS_ENDPOINT=https://sws.fao.org
export SWS_TOKEN=XXX
export SWS_USER_CREDENTIALS_SECRET_NAME=dev/sws/user_client
```

If you have no access to the `SWS_USER_CREDENTIALS_SECRET_NAME` you can use the following environment variables:

```bash
export SWS_AUTH_CLIENTID=XXX
export SWS_AUTH_CLIENTSECRET=XXX
export SWS_AUTH_TOKENENDPOINT=XXX
export SWS_AUTH_SCOPE=XXX
```

And instantiate the client in our script with the class method `from_env`:

```python
from sws_api_client import SwsApiClient

sws_client = SwsApiClient.from_env()
```

### Access different API Services

The library provides a set of classes to interact with the different services available in the SWS API. The available classes are:
- `Tags` to interact with the SWS Tags API
- `Datasets` to interact with the Datasets API provided by both the legacy SWS IS Api and the new Session API
- `Tasks` to interact with the SWS TaskManager API
- `Datatable` to interact with the SWS Datatable API
- `Plugins` to interact with the SWS Plugins API

### Perform requests

To perform requests you just need to call the available methods using the SwsApiClient object, as an example:

```python
datasets = Datasets(sws_client)
dataset = datasets.get_dataset_info('aproduction')
logger.info(f"Dataset info: {dataset}")
```

or to get the list of tags:

```python
tags = Tags(sws_client)
tags_list = tags.get_tags()
logger.info(f"Tags: {tags_list}")
```

more complete examples can be found in the `example` folder:

```bash
cp example/conf_sws_api_client.json.example example/conf_sws_api_client.json
# edit the file with your credentials
python3 -m venv example/.venv
source example/.venv/bin/activate
pip install -r example/requirements
python example/dataset_example.py
```

If you need to perform a test request not in debug mode, you can use the following command:
    
```bash
AWS_PROFILE=fao-dev DEBUG_MODE=FALSE SWS_USER_CREDENTIALS_SECRET_NAME=dev/sws/user_client SWS_TOKEN=YOUR_TOKEN SWS_ENDPOINT=https://sws.dev.fao.org python3 dataset_example.py
```

## Development

**Please follow the semantic release commit message format.**

### Branches

#### develop
The `develop` branhces is the main branch for development. All feature branches should be created from this branch any commit to the development branch will create an `alpha` version.

#### feature/*
The `feature/*` branches are the branches for new features. Any commit to a feature branch will create a `beta` version.

#### main
The `main` branch is the production branch. Any commit to the main branch will create a `release` version.

### Release
Migrated to github test 6