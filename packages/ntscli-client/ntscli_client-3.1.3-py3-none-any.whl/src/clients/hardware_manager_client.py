from typing import Union
from requests import Session, exceptions
from requests_toolbelt.utils import dump
from src.clients.e2e_token_client import E2ETokenClient
from urllib3.util import Retry
from src.log import logger
from src.exceptions import MissingMetatronException

class HardwareManagerClient:

    retries = Retry(total=0, backoff_factor=0.1, status_forcelist=[])

    target_app_name = "wall_e"

    def __init__(self, net_key=None, use_netflix_access=False):
        self.url = "https://hardwaremanager.netflixpartners.com"
        self.port = 443
        self.session = Session()
        if net_key is not None:
            self.auth_header = "Authorization"
            self.auth_value = f"Bearer {net_key}"
        elif use_netflix_access:
            # leverage Metatron
            self.url = "https://hardwaremanager.netflixpartners.com"
            self.port = 7004
            try:
                from metatron.http import MetatronAdapter
                self.auth_header = "X-Forwarded-Authentication"
                self.auth_value = E2ETokenClient().get_e2e_token(HardwareManagerClient.target_app_name)['token']
                self.session.mount(self.__get_url_with_port(), MetatronAdapter(HardwareManagerClient.target_app_name, max_retries=HardwareManagerClient.retries))
            except ImportError:
                raise MissingMetatronException()
        else:
            raise Exception("User is not authenticated")

    def _call_host_command(self, host: str, command: str, params=None):
        url = f"{self.__get_url_with_port()}/api/host/{host}/command/{command}"
        resp = self.session.post(url, headers=self.__get_headers(), json=params)
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            logger.debug(f"Failed to call host command {command} for host {host}: {e}")
            raise Exception(f"Failed to call host command {command} for host {host}: {e}")
        return resp.json()

    def get_devices_for_host(self, host: str):
        return self._call_host_command(host, "host.devices.list")

    def set_device_ui(self, host: str, ip: str, env: Union["test", "prod"]):
        res = self._call_host_command(host, f"device.deviceui?ip={ip}", {"ui": env})
        return {
            "deviceUI": res.get("deviceUI", ""),
        }

    def __get_url_with_port(self):
        return f"{self.url}:{self.port}"

    def __get_headers(self):
        return { self.auth_header: self.auth_value, "Content-Type": "application/json", "x-netflix.client.appid": "nts-cli" }

    def __log_resp(self, resp):
        data = dump.dump_all(resp)
        logger.debug(data.decode('utf-8'))

