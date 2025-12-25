# AxeProfiler is a program designed to make saving/switching configurations for
# bitcoin miner devices simpler and more efficient.

# Copyright (C) 2025 [DC] Celshade <ggcelshade@gmail.com>

# This file is part of AxeProfiler.

# AxeProfiler is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# AxeProfiler is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with
# AxeProfiler. If not, see <https://www.gnu.org/licenses/>.
# ---
# The full API spec can be found at:
# https://github.com/bitaxeorg/ESP-Miner/blob/master/main/http_server/openapi.yaml

import requests

HTTP = "http://"
API = {
    # NOTE: Valid route, but not yet used by this program
    "scan": {  # scan for available networks (not axes)
        "type": "GET",
        "url": "/api/system/wifi/scan"
    },
    "info": {
        "type": "GET",
        "url": "/api/system/info"
    },
    # NOTE: Valid route, but not yet used by this program
    # NOTE: As of 2025-11-01, this works for supra/gamma, but nerdQ++ json fails
    "asic": {
        "type": "GET",
        "url": "/api/system/asic"
    },
    "statistics": {
        "type": "GET",
        "url": "/api/system/statistics"
    },
    # NOTE: Valid route, but not yet used by this program
    "dashboard": {
        "type": "GET",
        "url": "/api/system/statistics/dashboard"
    },
    "restart": {
        "type": "POST",
        "url": "/api/system/restart"
    },
    "system": {  # NOTE: requestBody change system settings
        "type": "PATCH",
        "url": "/api/system"
    },
    # NOTE: Valid route, but not yet used by this program
    "firmware": {  # NOTE: [requestBody] update firmware
        "type": "POST",
        "url": "/api/system/OTA"
    },
    # NOTE: Valid route, but not yet used by this program
    "website": {  # NOTE: [requestBody] update website firmware
        "type": "POST",
        "url": "/api/system/OTAWWW"
    }
}


def request(
        ip: str,
        endpoint: str,
        body: dict[str, str | int] | None = None) -> requests.Response | None:
    """Make and return the proper request for the given IP addr and endpoint.

    See `./api.py` for the supported API routes and a link to the source
    for the Bitaxe API.

    Args:
        ip: The IP of the [axe] device.
        endpoint: The desired AxeOS endpoint to hit.
        body: The body data to send with PATCH/POST requests (default=None).

    Returns:
        A response object else `None`
    Raises:
        ValueError: if an invalid HTTP method is specified for the endpoint.
        requests.HTTPError: if an invalid path for the API is requested.
        requests.ConnectionError: if the request takes too long or fails.
        Exception: for any other request issues.
    """

    try:
        method, url = API[endpoint]["type"], f"{HTTP}{ip}{API[endpoint]['url']}"

        if method == "GET" and endpoint == "info":
            res = requests.get(url, timeout=5)

            if res.status_code != 200:
                raise requests.HTTPError(f"Status code: {res.status_code}")
            return res
        elif method == "POST" and endpoint == "restart":
            res = requests.post(url, timeout=5)

            if res.status_code != 200:
                raise requests.HTTPError(f"Status code: {res.status_code}")
            return res
        elif method == "PATCH" and endpoint == "system":
            res = requests.patch(url, json=body, timeout=5)

            if res.status_code != 200:
                raise requests.HTTPError(f"Status code: {res.status_code}")
            return res
        else:
            raise ValueError("Not a valid HTTP method for this API.")
    except ValueError as ve:
        # print(f"{ve} for {method} {url}")
        raise ve
    except requests.HTTPError as httpe:
        # print(f"HTTP error: {httpe} for {method} {url}")
        raise httpe
    except requests.ConnectTimeout as conne:
        # print(f"Timeout Error: {conne} for {method} {url}")
        raise conne
    except Exception as e:
        # print(f"Request error: {e} for {method} {url}")
        raise e
