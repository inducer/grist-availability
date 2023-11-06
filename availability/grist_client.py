from typing import Any, List, Mapping, Optional, Sequence
import json

import requests


class HTTPError(RuntimeError):
    pass


# {{{ grist client

class GristClient:
    """Grist API client"""

    def __init__(self, root_url, api_key, doc_id, timeout=None):
        self.root_url = root_url
        self.api_key = api_key
        self.doc_id = doc_id
        self.timeout = timeout

    def _request(self,
                 method, path, query_params: Optional[Mapping[str, str]]
                 ) -> requests.Response:
        headers = {
            "Accept": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.api_key}",
        }
        response = requests.request(
                method, self.root_url + "/api" + path,  params=query_params,
                headers=headers)
        if not response.ok:
            raise HTTPError(f"Status {response.status_code}: {response.text}")

        return response

    def _get_json(self, path, query_params):
        return self._request("GET", path, query_params).json()

    def get_records(self, table_id: str | int,
                    filter: Optional[Mapping[str, List[Any]]] = None
                    ) -> Sequence[Mapping]:
        query_params = {}

        if filter:
            query_params["filter"] = json.dumps(filter)

        return self._get_json(
                f"/docs/{self.doc_id}/tables/{table_id}/records",
                query_params=query_params)["records"]

# }}}

# vim: foldmethod=marker
