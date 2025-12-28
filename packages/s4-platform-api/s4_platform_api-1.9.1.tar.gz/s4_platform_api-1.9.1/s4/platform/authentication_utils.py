import logging

import requests
from requests.exceptions import HTTPError
from typing import Optional


log = logging.getLogger(__name__)


def get_auth_token(
    auth_domain: str, auth_audience: str, client_id: str, client_secret: str,
    token_endpoint: Optional[str] = None
) -> str:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": auth_audience,
    }
    auth_url = token_endpoint or f"https://{auth_domain}/oauth/token"
    response = requests.post(auth_url, data, headers)

    try:
        response.raise_for_status()
    except HTTPError as ex:
        log.error(f"Could not retrieve auth token from {auth_url}")
        raise ex

    auth = response.json()
    return auth["access_token"]


# Retrieves the token endpoint from the openid configuration for the issuer
def get_auth_token_using_metadata(auth_issuer: str, auth_domain: str, auth_audience: str, client_id: str,
                                  client_secret: str
) -> str:
    url = f"{auth_issuer}/.well-known/openid-configuration"
    response = requests.get(url)

    try:
        response.raise_for_status()
        token_endpoint = response.json()["token_endpoint"]
    except HTTPError as ex:
        log.error(f"Could not retrieve openid configuration from {url}")
        raise ex

    return get_auth_token(auth_domain, auth_audience, client_id, client_secret, token_endpoint)
