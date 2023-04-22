import argparse
import json
import os.path
import pathlib
from argparse import Namespace
from distutils.util import strtobool
from mimetypes import MimeTypes

import requests
from botcity.maestro import BotMaestroSDK
from requests_toolbelt import MultipartEncoder

from src.build import Build


class Action:

    def __init__(self):
        self._maestro = None
        self._args = None
        self._filepath = None
        self._headers = None

    @property
    def maestro(self):
        return self._maestro

    @maestro.setter
    def maestro(self, maestro: BotMaestroSDK):
        if not isinstance(maestro, BotMaestroSDK):
            raise ValueError(f"Value is not Maestro SDK.")
        self._maestro = maestro

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, header: BotMaestroSDK):
        if not isinstance(header, dict):
            raise ValueError(f"Value is not a dict")
        self._headers = header

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, args: Namespace):
        if not isinstance(args, Namespace):
            raise ValueError(f"Value is not a Namespace")
        self._args = args

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, filepath: str):
        if not isinstance(filepath, str):
            raise ValueError(f"Value is not a Namespace")

        if not os.path.exists(filepath):
            raise RuntimeError(f"{filepath} is not exists.")
        self._filepath = filepath

    def get(self):
        url = f'{self.maestro.server}/api/v2/bot'

        data = {"organizationLabel": self.maestro.organization, 'botId': self.args.botId}
        params = {'botId': self.args.botId}

        with requests.get(url, json=data, params=params, headers=self.headers, timeout=5) as req:
            if req.status_code != 200:
                raise ValueError(
                    'Error during message. Server returned %d. %s' %
                    (req.status_code, req.json().get('message', ''))
                )
            response = json.loads(req.text)
            if not response or len(response) > 1:
                raise ValueError(f"{self.args.botId} not exist.")
            return response[0]

    def update(self):
        url = f'{self.maestro.server}/api/v2/bot/upload/{self.args.botId}/version/{self.args.version}'
        headers_to_upload = self.headers.copy()
        with open(self.filepath, 'rb') as f:
            mime = MimeTypes()
            mime_type = mime.guess_type(self.filepath)
            data = MultipartEncoder(
                fields={'file': (pathlib.Path(self.filepath).name, f, mime_type[0])}
            )
            headers_to_upload["Content-Type"] = data.content_type
            with requests.post(url, data=data, headers=headers_to_upload, timeout=5) as req:
                if not req.ok:
                    try:
                        message = 'Error during upload bot. Server returned %d. %s' % (
                            req.status_code, req.json().get('message', ''))
                    except ValueError:
                        message = 'Error during upload bot. Server returned %d. %s' % (
                            req.status_code, req.text)
                    raise ValueError(message)

    def deploy(self):
        url = f'{self.maestro.server}/api/v2/bot'
        data = {
            "organization": self.headers.get("organization"),
            "botId": self.args.botId,
            "version": self.args.version,
            "technology": self.args.technology.upper(),
            "command": None,
        }
        with requests.post(url, json=data, headers=self.headers, timeout=5) as req:
            if req.status_code != 200:
                raise ValueError(
                    'Error during message. Server returned %d. %s' %
                    (req.status_code, req.json().get('message', ''))
                )

    def release(self):
        url = f'{self.maestro.server}/api/v2/bot/release'
        data = {
            "botId": self.args.botId,
            "version": self.args.version,
        }
        with requests.post(url, json=data, headers=self.headers, timeout=5) as req:
            if req.status_code != 200:
                raise ValueError(
                    'Error during message. Server returned %d. %s' %
                    (req.status_code, req.json().get('message', ''))
                )

    @staticmethod
    def _get_args() -> argparse.Namespace:
        parser = argparse.ArgumentParser()
        parser.add_argument("-u", "--update", help="Will the update run", dest="update",
                            type=lambda x: bool(strtobool(x)), action="store")
        parser.add_argument("-d", "--deploy", help="Will the deploy", dest='deploy', type=lambda x: bool(strtobool(x)),
                            action="store")
        parser.add_argument("-r", "--release", help="Will the release", dest='release',
                            type=lambda x: bool(strtobool(x)), action="store")
        parser.add_argument("-v", "--version", help="New version to bot", type=str, action="store")
        parser.add_argument("-p", "--path", help="Path to github action repository", type=str, action="store")
        parser.add_argument("-bi", "--botId", help="Bot ID that will be modified.", type=str, action="store")
        parser.add_argument("-t", "--technology", help="technology bot.", type=str, action="store")
        parser.add_argument("-ap", "--actionPath", help="actionPath", type=str, action="store")

        args = parser.parse_args()
        return args

    def _get_secrets(self):
        server = self._validate_secret(key='SERVER')
        login = self._validate_secret(key='LOGIN')
        key = self._validate_secret(key='KEY')

        secrets = {
            'server': server,
            'login': login,
            'key': key,
        }

        return secrets

    @staticmethod
    def _validate_secret(key: str):
        if not key:
            raise Exception(f"{key} is empty or none.")

        value = os.getenv(key=key.upper())

        if value:
            return value

        raise Exception(f"{key} not found in secrets")

    @staticmethod
    def _get_maestro(secrets: dict):
        maestro = BotMaestroSDK(**secrets)
        maestro.login()
        return maestro

    def run(self):
        self.args = self._get_args()

        secrets = self._get_secrets()

        self.maestro = self._get_maestro(secrets=secrets)

        self.headers = {
            "Content-Type": "application/json",
            "token": self.maestro.access_token,
            "organization": self.maestro.organization
        }

        build = Build(args=self.args)

        self.filepath = build.run()

        if self.args.update:
            self.update()

        if self.args.deploy:
            self.deploy()
            self.update()

        if self.args.release:
            self.release()
