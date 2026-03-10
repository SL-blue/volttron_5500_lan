# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2023 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}


import random
from math import pi
import json
import sys
from platform_driver.interfaces import BaseInterface, BaseRegister, BasicRevert
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent
import logging
import requests
from requests import get
from .homeassistant_handlers import get_default_handlers
from .homeassistant_handlers.base import BaseHandler

_log = logging.getLogger(__name__)
type_mapping = {"string": str,
                "int": int,
                "integer": int,
                "float": float,
                "bool": bool,
                "boolean": bool}


class HomeAssistantRegister(BaseRegister):
    def __init__(self, read_only, pointName, units, reg_type, attributes, entity_id, entity_point, default_value=None,
                 description=''):
        super(HomeAssistantRegister, self).__init__("byte", read_only, pointName, units, description='')
        self.reg_type = reg_type
        self.attributes = attributes
        self.entity_id = entity_id
        self.value = None
        self.entity_point = entity_point


def _post_method(url, headers, data, operation_description):
    err = None
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            _log.info(f"Success: {operation_description}")
        else:
            err = f"Failed to {operation_description}. Status code: {response.status_code}. " \
                  f"Response: {response.text}"

    except requests.RequestException as e:
        err = f"Error when attempting - {operation_description} : {e}"
    if err:
        _log.error(err)
        raise Exception(err)


class Interface(BasicRevert, BaseInterface):
    def __init__(self, **kwargs):
        super(Interface, self).__init__(**kwargs)
        self.point_name = None
        self.ip_address = None
        self.access_token = None
        self.port = None
        self.units = None
        self._handlers: dict[str, BaseHandler] = {}

    def configure(self, config_dict, registry_config_str):
        self.ip_address = config_dict.get("ip_address", None)
        self.access_token = config_dict.get("access_token", None)
        self.port = config_dict.get("port", None)

        # Check for None values
        if self.ip_address is None:
            _log.error("IP address is not set.")
            raise ValueError("IP address is required.")
        if self.access_token is None:
            _log.error("Access token is not set.")
            raise ValueError("Access token is required.")
        if self.port is None:
            _log.error("Port is not set.")
            raise ValueError("Port is required.")

        self.parse_config(registry_config_str)

        # Create handler instances AFTER config is loaded
        self._handlers = get_default_handlers(self)

    # ---------------------------
    # Shared HTTP helpers
    # ---------------------------
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _base_url(self) -> str:
        return f"http://{self.ip_address}:{self.port}"

    def _call_service(self, domain: str, service: str, payload: dict, op_desc: str = ""):
        """
        Handlers call this. payload should already include entity_id and any extra fields.
        """
        url = f"{self._base_url()}/api/services/{domain}/{service}"
        _post_method(url, self._headers(), payload, op_desc or f"{domain}.{service}")

    # ---------------------------
    # Handler routing (NEW)
    # ---------------------------
    def _domain_from_entity_id(self, entity_id: str) -> str:
        # "lock.front_door" -> "lock"
        if not entity_id or "." not in entity_id:
            return ""
        return entity_id.split(".", 1)[0]

    def _get_handler(self, entity_id: str) -> BaseHandler:
        domain = self._domain_from_entity_id(entity_id)
        handler = self._handlers.get(domain)
        if handler is None:
            raise ValueError(
                f"Unsupported entity domain '{domain}' for entity_id '{entity_id}'. "
                f"No handler registered."
            )
        return handler

    def get_point(self, point_name):
        register = self.get_register_by_name(point_name)
        handler = self._get_handler(register.entity_id)
        value = handler.scrape(register=register)
        register.value = value
        return value

    def _set_point(self, point_name, value):
        register = self.get_register_by_name(point_name)
        if register.read_only:
            raise IOError("Trying to write to a point configured read only: " + point_name)

        # Cast to declared type
        register.value = register.reg_type(value)

        handler = self._get_handler(register.entity_id)
        # Let the handler validate + call HA services
        handler.set_point(register=register, value=register.value)

        return register.value

    def get_entity_data(self, entity_id: str):
        url = f"{self._base_url()}/api/states/{entity_id}"
        response = requests.get(url, headers=self._headers())
        if response.status_code == 200:
            return response.json()
        error_msg = (
            f"Request failed with status code {response.status_code}, entity_id: {entity_id}, "
            f"response: {response.text}"
        )
        _log.error(error_msg)
        raise Exception(error_msg)

    def _scrape_all(self):
        result = {}
        read_registers = self.get_registers_by_type("byte", True)
        write_registers = self.get_registers_by_type("byte", False)

        for register in (read_registers + write_registers):
            try:
                handler = self._get_handler(register.entity_id)
                value = handler.scrape(register=register)
                register.value = value
                result[register.point_name] = value
            except Exception as e:
                _log.error(f"Error scraping {register.entity_id}:{register.entity_point} -> {e}")

        return result

    def parse_config(self, config_dict):

        if config_dict is None:
            return
        for regDef in config_dict:

            if not regDef['Entity ID']:
                continue

            read_only = str(regDef.get('Writable', '')).lower() != 'true'
            entity_id = regDef['Entity ID']
            entity_point = regDef['Entity Point']
            point_name = regDef['Volttron Point Name']
            units = regDef.get('Units')
            description = regDef.get('Notes', '')
            default_value = ("Starting Value")

            type_name = regDef.get("Type", 'string')
            reg_type = type_mapping.get(type_name, str)
            attributes = regDef.get('Attributes', {})

            register = HomeAssistantRegister(
                read_only=read_only,
                pointName=point_name,
                units=units,
                reg_type=reg_type,
                attributes=attributes,
                entity_id=entity_id,
                entity_point=entity_point,
                default_value=default_value,
                description=description
            )

            if default_value is not None:
                self.set_default(point_name, register.value)

            self.insert_register(register)

# Deleted: turn off lights, turn on lights, change thermostat mode, set thermostat temperature, change brightness, set input boolean