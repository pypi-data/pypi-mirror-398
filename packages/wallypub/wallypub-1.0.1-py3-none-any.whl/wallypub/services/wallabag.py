import http
import json
import logging
import socket
from abc import ABC

import keyring

from wallypub.conf.app import app_config
from wallypub.conf.constants import (
    SERVICE_NAME,
    WALLABAG_CLIENT_SECRET_KEY,
    WALLABAG_PASS_KEY,
)
from wallypub.services.readitlater import ReadItLater
from http import client


# Wallabag class interacts with Wallabag servers that have their API available
class Wallabag(ReadItLater, ABC):
    def __init__(self):
        self._wallabag_url = app_config.Wallabag.url
        self._client_id = app_config.Wallabag.client_id
        self._wallabag_username = app_config.Wallabag.username
        self._client_secret = keyring.get_password(
            SERVICE_NAME, WALLABAG_CLIENT_SECRET_KEY
        )
        self._wallabag_password = keyring.get_password(SERVICE_NAME, WALLABAG_PASS_KEY)
        self._bearer_token = None  # Initialize bearer_token

    @property
    def client_id(self):
        return self._client_id

    @client_id.setter
    def client_id(self, client_id):
        self._client_id = client_id

    @property
    def client_secret(self):
        return self._client_secret

    @client_secret.setter
    def client_secret(self, client_secret):
        self._client_secret = client_secret

    @property
    def wallabag_username(self):
        return self._wallabag_username

    @wallabag_username.setter
    def wallabag_username(self, username):
        self._wallabag_username = username

    @property
    def wallabag_password(self):
        return self._wallabag_password

    @wallabag_password.setter
    def wallabag_password(self, password):
        self._wallabag_password = password

    @property
    def wallabag_url(self):
        return self._wallabag_url

    @wallabag_url.setter
    def wallabag_url(self, url):
        self._wallabag_url = url

    @property
    # bearer_token is used for hitting the Wallabag API endpoints
    def bearer_token(self):
        return self._bearer_token

    @bearer_token.setter
    def bearer_token(self, value):
        self._bearer_token = value

    def add_entry(self, url, tags: str):
        """
        add_entry performs a POST request against the /api/entries endpoint.
        :return:
        """
        conn = client.HTTPSConnection(self.wallabag_url)

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.bearer_token,
        }

        payload = {
            "url": "{}".format(url),
        }
        if tags is not None:
            payload["tags"] = tags

        payload_json = json.dumps(payload)

        conn.request("POST", "/api/entries", payload_json, headers=headers)
        print(payload_json)
        res = conn.getresponse()
        data = res.read()
        conn.close()
        logging.debug("/api/entries post response: {}".format(data))

    def authenticate(self):
        """authenticate retrieves the access token from the endpoint oauth/v2/token and updates bearer_token with the access_token from the response"""
        conn = client.HTTPSConnection(self.wallabag_url)
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.wallabag_username,
            "password": self.wallabag_password,
        }
        payload_json = json.dumps(payload)

        headers = {"Content-Type": "application/json"}

        conn.request("POST", "/oauth/v2/token", payload_json, headers=headers)

        res = conn.getresponse()
        data = res.read()
        conn.close()
        json_data = json.loads(data.decode("utf-8"))
        self.bearer_token = json_data["access_token"]

    def get_entry(self, entry_id: str):
        """get_entry retrieves an entry from the api/entries/{entry_id} endpoint"""
        conn = client.HTTPSConnection(self.wallabag_url)

        headers = {"accept": "*/*", "Authorization": "Bearer " + self.bearer_token}

        json_data = []

        try:
            conn.request("GET", "/api/entries/" + entry_id, headers=headers)
        except socket.timeout as st:
            logging.error("timeout received: {}".format(st))
            return json_data
        except http.client.HTTPException as e:
            logging.error("request error: {}".format(e))
            return json_data
        else:  # happy path no error occurred
            res = conn.getresponse()
            data = res.read()
            conn.close()
            json_data = json.loads(data.decode("utf-8"))
        finally:
            conn.close()

        return json_data

    def get_entries(self, params):
        """get_entries retrieves an entry from the api/entries endpoint"""
        conn = client.HTTPSConnection(self.wallabag_url)  # make the URL configurable

        headers = {"accept": "*/*", "Authorization": "Bearer " + self.bearer_token}
        str_params = self.append_url_params(params)
        url = "/api/entries" + str_params
        logging.debug("get entries url: {}".format(url))

        json_data = []

        try:
            conn.request("GET", url, headers=headers)
        except socket.timeout as st:
            logging.error("timeout received: {}".format(st))
            return json_data
        except http.client.HTTPException as e:
            logging.error("request error: {}".format(e))
            return json_data
        else:  # happy path no error occurred
            res = conn.getresponse()
            data = res.read()
            conn.close()
            json_data = json.loads(data.decode("utf-8"))
        finally:
            conn.close()

        return json_data

    def patch_entry(self, entry_id, body):
        """patch_entry updates a given entry from the PATCH /api/entries/{entry_id} endpoint
        The documentation is incorrect and PATCH parses values from the body and not the
        query parameters.
        https://github.com/wallabag/wallabag/issues/7746
        """
        conn = client.HTTPSConnection(self.wallabag_url)

        headers = {
            "accept": "*/*",
            "Authorization": "Bearer " + self.bearer_token,
            "content-type": "application/json",
        }

        url = "/api/entries/" + str(entry_id)

        # encode body for http client
        json_body = json.dumps(body)

        conn.request("PATCH", url, body=json_body, headers=headers)

        res = conn.getresponse()

        logging.debug("status: {} reason: {} ".format(res.status, res.reason))
        data = res.read()
        conn.close()
        json_data = json.loads(data.decode("utf-8"))

        return json_data

    @staticmethod
    def append_url_params(params):
        """append_url_params takes in the given json and formats them for the URL"""
        str_params = "?"
        i = 0
        # remove empty params
        filtered_params = {k: v for k, v in params.items() if v}
        for key in filtered_params:
            if filtered_params[key] != "":
                str_params += str(key) + "=" + str(filtered_params[key])
                # append `&` for everything except last parameter
                if i < len(filtered_params) - 1 and filtered_params[key] != "":
                    str_params += "&"
            i += 1
        return str_params
