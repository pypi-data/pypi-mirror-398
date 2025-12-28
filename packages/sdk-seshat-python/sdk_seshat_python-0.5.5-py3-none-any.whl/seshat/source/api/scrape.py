from typing import Optional, Dict, Any, Callable

import requests
from requests import Response

from seshat.general import configs
from seshat.source.api.base import APIClient, HttpMethods, APISource
from seshat.transformer.merger import Merger


class ScrapFlyClient(APIClient):
    scrapfly_url = "https://api.scrapfly.io/scrape"
    default_query_params = {
        "tags": "player,project:default",
        "asp": True,
        "render_js": True,
    }

    def __init__(self, apikey: str):
        self.apikey = apikey

    def request(self, url, method: HttpMethods, **kwargs) -> Response:
        query_params = {
            **self.default_query_params,
            **kwargs.pop("params", {}),
            "key": self.apikey,
            "url": url,
        }
        response = requests.request(
            method=method,
            url=self.scrapfly_url,
            params=query_params,
            timeout=90,
            **kwargs,
        )
        response.raise_for_status()
        return response


class ScrapFlySource(APISource):
    def __init__(
        self,
        api_url: str,
        api_key: Optional[str],
        api_method: str = "GET",
        api_params: Optional[Dict[str, Any]] = None,
        api_headers: Optional[Dict[str, str]] = None,
        response_processor: Optional[Callable[[requests.Response], Any]] = None,
        schema=None,
        mode=configs.DEFAULT_MODE,
        group_keys=None,
        merge_result=False,
        merger: Merger = Merger,
        *args,
        **kwargs
    ):
        super().__init__(
            api_url,
            api_method,
            api_params,
            api_headers,
            response_processor,
            schema,
            mode,
            group_keys,
            merge_result,
            merger,
            *args,
            **kwargs,
        )
        self.client = ScrapFlyClient(api_key)
