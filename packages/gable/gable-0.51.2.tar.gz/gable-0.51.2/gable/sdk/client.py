import json
import os
from typing import Union

from gable.api.client import GableAPIClient

from .contract import GableContract
from .data_asset import GableDataAsset


class GableClient:
    def __init__(
        self,
        api_endpoint: Union[str, None] = None,
        api_key: Union[str, None] = None,
        api_headers: Union[dict, None] = None,
    ) -> None:
        if api_endpoint is None:
            self.api_endpoint = os.getenv("GABLE_API_ENDPOINT", "")
        else:
            self.api_endpoint = api_endpoint

        if api_key is None:
            self.api_key = os.getenv("GABLE_API_KEY", "")
        else:
            self.api_key = api_key

        if api_headers is None:
            headers: Union[str, None] = os.getenv("GABLE_API_HEADERS", "")
            if headers:
                try:
                    self.api_headers = json.loads(headers)
                except json.JSONDecodeError:
                    raise ValueError(
                        "GABLE_API_HEADERS environment variable is not valid JSON"
                    )
            else:
                self.api_headers = {}
        else:
            self.api_headers = api_headers

        gable_api_client = GableAPIClient(
            endpoint=self.api_endpoint,
            api_key=self.api_key,
            api_headers=self.api_headers,
        )
        self.contracts = GableContract(gable_api_client)
        self.data_assets = GableDataAsset(gable_api_client)
