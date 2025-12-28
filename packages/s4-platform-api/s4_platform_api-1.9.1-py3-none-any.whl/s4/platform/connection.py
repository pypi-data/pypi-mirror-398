import json
import logging
import os
from typing import Optional, Callable, Any
from urllib.parse import urlparse, urlunparse

import requests
from dotenv import load_dotenv
from requests import Response


log = logging.getLogger(__name__)


load_dotenv()
if os.environ.get("DEBUG_REQUESTS") == "True":
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)


class Connection(object):
    def __init__(
        self,
        uri: str,
        access_token: str = None,
        host_namespace: str = None,
        environment_name: str = None,
    ):
        if host_namespace is None:
            host_namespace = os.environ.get("MASTER_HOST_NAMESPACE")

        if access_token is None:
            access_token = os.environ.get("ACCESS_TOKEN")

        if host_namespace is None:
            self._host_namespace = None
            self._host_namespace_parts = None
        else:
            log.info(
                "Host namespace provided. Queries to '%s' will be sent to '%s' instead.",
                host_namespace,
                uri,
            )
            self._host_namespace = host_namespace
            self._host_namespace_parts = urlparse(self._host_namespace)

        self.platform_uri = uri
        self.cached_objects = {}
        self._host_uri_parts = urlparse(self.platform_uri)
        self.session = requests.session()

        self._access_token = access_token
        if self._access_token:
            self.session.headers.update(
                {"Authorization": "Bearer " + self._access_token}
            )

        if environment_name:
            self.session.headers.update(({"X-S4-Env": environment_name}))
            self.environment_name = environment_name

    #
    # Returns a new Connection object for the specified environment
    #
    def get_connection_for_env(self, environment_name: str):
        return Connection(
            self.platform_uri,
            self._access_token,
            self._host_namespace,
            environment_name,
        )

    def delete_resource(self, path: str) -> Optional[dict]:
        r = self.session.delete(
            f"{self.platform_uri}/{path}",
        )

    def fetch_json(self, relative_path: str, params: dict = None) -> Optional[dict]:
        absolute_path = f"{self.platform_uri}/{relative_path}"
        return self.fetch_json_from_absolute_path(absolute_path, params=params)

    def fetch_json_from_absolute_path(self, absolute_path: str, params: dict = None) -> Optional[dict]:
        request_path = self.rewrite_host_namespace_url(absolute_path)
        r = self.session.get(request_path, params=params)
        return self._handle_optional_json_response(r)

    def fetch_json_from_iri(self, iri: str, params: dict = None) -> Optional[dict]:
        rewritten_iri = self.rewrite_host_namespace_url(iri)
        r = self.session.get(rewritten_iri, params=params)
        return self._handle_optional_json_response(r)

    def patch_json(self, path: str, json: dict) -> Optional[dict]:
        r = self.session.patch(
            f"{self.platform_uri}/{path}",
            json=json,
            headers={"Content-Type": "application/json"},
        )
        return self._handle_optional_json_response(r)

    def put_json(self, path: str, json: dict) -> Optional[dict]:
        r = self.session.put(
            f"{self.platform_uri}/{path}",
            json=json,
            headers={"Content-Type": "application/json"},
        )
        return self._handle_optional_json_response(r)

    def post_json(self, path: str, json: Optional[Any]) -> Optional[dict]:
        r = self.session.post(
            f"{self.platform_uri}/{path}",
            json=json,
            headers={"Content-Type": "application/json"},
        )
        return self._handle_optional_json_response(r)

    def post_files(self, path: str, files: dict) -> Optional[dict]:
        r = self.session.post(
            f"{self.platform_uri}/{path}", files=files, headers=self.session.headers
        )
        return self._handle_optional_json_response(r)

    def post_json_array(self, path: str, json: list) -> Optional[dict]:
        r = self.session.post(f"{self.platform_uri}/{path}", json=json,
                              headers={"Content-Type": "application/json"})
        return self._handle_optional_json_response(r)

    def post_multipart(self, path: str, data: dict, files: dict) -> Optional[dict]:
        r = self.session.post(
            f"{self.platform_uri}/{path}", data=data, files=files, headers=self.session.headers
        )
        return self._handle_optional_json_response(r)

    def get_from_iri(self, iri: str, schema_class: Callable) -> Any:
        rewritten_iri = self.rewrite_host_namespace_url(iri)
        model_object = self.cached_objects.get(rewritten_iri)
        if model_object is None:
            json = self.fetch_json_from_absolute_path(rewritten_iri)

            schema = schema_class()
            schema.context["connection"] = self

            model_object = schema.load(json)
            # the iri of the returned object should match the passed in iri
            self.cached_objects[rewritten_iri] = model_object
        return model_object

    @staticmethod
    def _handle_optional_json_response(response: Response) -> Optional[dict]:
        if not response.ok:
            try:
                json_body = response.json()
                log.error(f"Bad response ({response.status_code}). Body as JSON:")
                log.error(json.dumps(json_body, indent=2))
            except Exception as ex:
                log.error(f"Exception parsing response body as JSON: {ex}")
                log.error(f"Bad response ({response.status_code}). Body:")
                log.error(response.text)
            response.raise_for_status()
        if not response.content:
            return None
        return response.json()

    def rewrite_host_namespace_url(self, url: str) -> str:
        if self._host_namespace is None or self._host_namespace == self.platform_uri:
            return url

        url_parts = urlparse(url)

        # If the scheme and host in the URL match the host namespace for this connection, replace those
        # parts of the URL with the configured host URI. This ensures that requests use internal network routes and
        # never transit the internet.
        if (
            url_parts.scheme == self._host_namespace_parts.scheme
            and url_parts.netloc == self._host_namespace_parts.netloc
        ):
            rewritten_uri = urlunparse(
                [
                    self._host_uri_parts.scheme,
                    self._host_uri_parts.netloc,
                    url_parts.path,
                    url_parts.params,
                    url_parts.query,
                    url_parts.fragment,
                ]
            )
            log.debug("Rewrote '%s' as '%s'", url, rewritten_uri)
            return rewritten_uri
        else:
            return url
