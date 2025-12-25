#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# This file is part of Mentat system (https://mentat.cesnet.cz/).
#
# Copyright (C) since 2011 CESNET, z.s.p.o (http://www.ces.net/)
# Use of this source is governed by the MIT license, see LICENSE file.
# -------------------------------------------------------------------------------


"""
Implementation of internal **SNER** service connector.
"""

__author__ = "Jakub Judiny <Jakub.Judiny@cesnet.cz>"
__credits__ = "Pavel Kácha <pavel.kacha@cesnet.cz>, Andrea Kropáčová <andrea.kropacova@cesnet.cz>"


import copy
import ipaddress
import json
import urllib.parse
from typing import Optional

import requests
from requests.exceptions import HTTPError

from mentat.const import CKEY_CORE_SERVICES, CKEY_CORE_SERVICES_SNER

_MANAGER: Optional["SNERServiceManager"] = None


def is_valid_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


class SNERConfigException(ValueError):
    pass


class SNERRuntimeException(RuntimeError):
    pass


class SNERService:
    """
    Implementation of internal **SNER** access service.
    """

    def __init__(self, base_url: str, base_api_url: str, api_key: str) -> None:
        """
        Initialize geolocation service with paths to desired database files.
        """
        self.base_url = base_url
        self.base_api_url = base_api_url
        self.api_key = api_key

        # Check presence and validity of config.
        if not self.base_url:
            raise SNERConfigException("SNER service is used but base URL is not configured")
        if not (self.base_url.startswith("https://") or self.base_url.startswith("http://")):
            raise SNERConfigException("Invalid SNER service base URL")
        if not self.base_api_url:
            raise SNERConfigException("SNER service is used but base API URL is not configured")
        if not (self.base_api_url.startswith("https://") or self.base_api_url.startswith("http://")):
            raise SNERConfigException("Invalid SNER service base API URL")
        if not self.api_key:
            raise SNERConfigException("SNER service is used but api_key is not configured")

        # Ensure both base_url and base_api_url end with slash.
        if not self.base_url.endswith("/"):
            self.base_url += "/"
        if not self.base_api_url.endswith("/"):
            self.base_api_url += "/"

    def status(self) -> dict[str, str]:
        """
        Display status of the service.
        """
        return {
            "base_url": self.base_url,
            "base_api_url": self.base_api_url,
        }

    @staticmethod
    def get_jsonfilter_payload(value: str, is_ip: bool) -> dict:
        """
        Get filter dictionary for looking up given IP or hostname in SNER service.
        Jsonfilter is not used for API, only for web.
        """
        return {
            "combinator": "and",
            "rules": [
                {
                    "field": "Host.address" if is_ip else "Host.hostname",
                    "operator": "==",
                    "valueSource": "value",
                    "value": value,
                }
            ],
        }

    def get_web_url(self, value: str, is_ip: bool) -> str:
        """
        Get URL for looking up given IP or hostname in SNER service.
        """
        return (
            f"{self.base_url}lens/service/list?jsonfilter="
            f"{urllib.parse.quote(json.dumps(self.get_jsonfilter_payload(value, is_ip)))}"
        )

    def get_api_url(self) -> str:
        """
        Get API URL for looking up given IP or hostname in SNER service.
        """
        return f"{self.base_api_url}public/storage/servicelist"

    @staticmethod
    def get_api_post_params(value: str, is_ip: bool) -> dict:
        """
        Get API POST parameters for looking up given IP or hostname in SNER service.
        """
        return {
            "filter": f'{"Host.address" if is_ip else "Host.hostname"} == "{value}"',
        }

    def lookup_ip_or_hostname(self, search: str) -> tuple[dict, bool] | None:
        """
        Lookup given input in SNER service.
        If the input is not a valid IP, it will try to find given input as a hostname.
        Returns the result and also if it is an IP (True) or not (False).
        """
        is_ip = is_valid_ip(search)

        headers = {
            "Accept": "application/json",
            "X-API-KEY": self.api_key,
        }
        try:
            resp = requests.post(
                self.get_api_url(),
                json=self.get_api_post_params(search, is_ip),
                headers=headers,
                timeout=300,
            )
        except Exception as exc:
            raise SNERRuntimeException(f"Can't get data from SNER service for search: '{search}'.") from exc

        if resp.status_code == requests.codes.not_found:
            return None

        resp_json = resp.json()
        try:
            resp.raise_for_status()
        except HTTPError as error:
            if "message" in resp_json:
                raise HTTPError(resp_json["message"]) from error
            raise error

        return (resp_json, is_ip)


class SNERServiceManager:
    """
    Class representing a custom SNERServiceManager capable of understanding and
    parsing Mentat system core configurations and enabling easy way of unified
    bootstrapping of :py:class:`mentat.services.sner.SNER.SNERService` service.
    """

    def __init__(self, core_config: dict, updates: Optional[dict] = None) -> None:
        """
        Initialize SNERServiceManager object with full core configuration tree structure.

        :param core_config: Mentat core configuration structure.
        :param updates: Optional configuration updates (same structure as ``core_config``).
        """
        self._snerconfig: dict = {}

        self._service: Optional[SNERService] = None

        self._configure_sner(core_config, updates)

    def _configure_sner(self, core_config: dict, updates: Optional[dict]) -> None:
        """
        Internal sub-initialization helper: Configure database structure parameters
        and optionally merge them with additional updates.

        :param core_config: Mentat core configuration structure.
        :param updates: Optional configuration updates (same structure as ``core_config``).
        """
        self._snerconfig = copy.deepcopy(core_config[CKEY_CORE_SERVICES][CKEY_CORE_SERVICES_SNER])

        if updates and CKEY_CORE_SERVICES in updates and CKEY_CORE_SERVICES_SNER in updates[CKEY_CORE_SERVICES]:
            self._snerconfig.update(updates[CKEY_CORE_SERVICES][CKEY_CORE_SERVICES_SNER])

    def service(self) -> SNERService:
        """
        Return handle to SNER service according to internal configurations.
        """
        if not self._service:
            self._service = SNERService(**self._snerconfig)
        return self._service


# -------------------------------------------------------------------------------


def init(core_config: dict, updates: Optional[dict] = None) -> None:
    """
    (Re-)Initialize :py:class:`SNERServiceManager` instance at module level and
    store the reference within module.
    """
    global _MANAGER
    _MANAGER = SNERServiceManager(core_config, updates)


def manager() -> Optional[SNERServiceManager]:
    """
    Obtain reference to :py:class:`SNERServiceManager` instance stored at module
    level.
    """
    return _MANAGER


def service() -> Optional[SNERService]:
    """
    Obtain reference to :py:class:`SNERService` instance from module level manager.
    """
    manager_ref = manager()
    if not manager_ref:
        return None
    return manager_ref.service()
