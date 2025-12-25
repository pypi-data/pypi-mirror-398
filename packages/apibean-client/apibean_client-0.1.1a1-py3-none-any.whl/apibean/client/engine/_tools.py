import json
import httpx

from ._helpers import Curlify

class Tools:

    def print_json(self, data):
        print(json.dumps(data, indent=2))

    def print_body(self, response):
        self.print_json(response.json())

    def print_response(self, response):
        if response.status_code == httpx.codes.OK:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: { json.dumps(response.json(), indent=2) }")

    def print_curl(self, req_or_resp: httpx.Request|httpx.Response):
        request = req_or_resp
        if isinstance(req_or_resp, httpx.Response):
            request = req_or_resp.request
        print(Curlify(request).to_curl())

    def print_session_item(self, store, item_name):
        item = store[item_name]
        if isinstance(item, dict):
            print(f'store.session["{ item_name }"]:')
            self.print_json(item)
        else:
            print(f'store.session["{ item_name }"]: { item }')
