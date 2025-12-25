from requests import Session, exceptions
from requests_toolbelt.utils import dump
from urllib3.util import Retry
from src.log import logger
from src.exceptions import MissingMetatronException

# This is required to propagate E2E tokens when making Metatron authenticated requests
class E2ETokenClient:

    url = "https://public.nflxe2etokens.prod.netflix.net"
    retries = Retry(total=0, backoff_factor=0.1, status_forcelist=[])

    def __init__(self):
        self.session = Session()
        try:
            from metatron.http import MetatronAdapter
            self.session.mount(E2ETokenClient.url, MetatronAdapter("nflxe2etokens", max_retries=E2ETokenClient.retries))
        except ImportError:
            raise MissingMetatronException()

    def get_e2e_token(self, app_name: str):
        resp = self.session.get(f"{E2ETokenClient.url}/REST/v1/tokens/mint/metatron?targetApp={app_name}")
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            logger.error(f"Failed to fetch e2e token: {e}")
            raise e
        return resp.json()

    def __log_resp(self, resp):
        data = dump.dump_all(resp)
        logger.debug(data.decode('utf-8'))
