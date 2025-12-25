# fountain_life_service_clients

Auto-generated fully-typed Python API clients for the Fountain Life ecosystem.

## Installation

```shell
pip install fountain-life-service-clients
```

## Usage

`fountain_life_service_clients` supports calling a service's API directly via
the service Lambda function.

```py
import json
from fountain_life_service_clients.file_service import FileServiceClient

# A well-typed service client that already knows which Lambda and
# path to call. Custom Alpha options can optionally be supplied as well.
file_service = FileServiceClient(
    headers={
        "LifeOmic-Account": "fountainlife",
        "LifeOmic-Policy": json.dumps(
            {"rules": {"readData": True}}
        ),
    }
)
res = await file_service.list_files({})
print(res.status_code)
# `res.body` is well-typed.
items = res.body["items"]
```

## Migration Guide
