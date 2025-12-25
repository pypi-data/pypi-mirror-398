import json
import os
import urllib.parse
import time
from src import __version__
from requests import Session, exceptions
from requests_toolbelt.utils import dump
from src.clients.e2e_token_client import E2ETokenClient
from urllib3.util import Retry
from src.log import logger
from typing import List
from src.exceptions import MissingMetatronException, UnauthorizedException, ForbiddenException, UnclaimedDeviceException, DeviceAlreadyReservedException, DeviceIsUnavailableException

class DeviceTestClient:

    retries = Retry(total=0, backoff_factor=0.1, status_forcelist=[])

    target_app_name = "wall_e"

    def __init__(self, net_key=None, use_netflix_access=False):
        self.url = "https://third-party-gateway.dta.netflix.net"
        self.port = 443
        self.session = Session()
        self._exec_details_cache = {}  # Cache for execution details by markerSetId
        if net_key is not None:
            self.auth_header = "Authorization"
            self.auth_value = f"Bearer {net_key}"
        elif use_netflix_access:
            # leverage Metatron
            self.url = "https://third-party-gateway-mtls.dta.netflix.net"
            try:
                from metatron.http import MetatronAdapter
                self.auth_header = "X-Forwarded-Authentication"
                self.auth_value = E2ETokenClient().get_e2e_token(DeviceTestClient.target_app_name)["token"]
                self.session.mount(self.__get_url_with_port(), MetatronAdapter(DeviceTestClient.target_app_name, max_retries=DeviceTestClient.retries))
            except ImportError:
                raise MissingMetatronException()
        else:
            raise Exception("User is not authenticated")

    def get_test_plan(self, esn: str, testcase_automation_filter: str = None, testcase_state_filter: str = None, testcase_name_filter: str = None, testcase_tag_filter: str = None, testcase_category_filter: str = None):
        # Base query params
        params = {"format": "marathonlite"}

        # Add filters if provided
        if testcase_automation_filter:
            params["testcaseAutomationFilter"] = testcase_automation_filter
        if testcase_state_filter:
            params["testcaseStateFilter"] = testcase_state_filter
        if testcase_name_filter:
            params["testcaseNameFilter"] = testcase_name_filter
        if testcase_tag_filter:
            params["testcaseTagFilter"] = testcase_tag_filter
        if testcase_category_filter:
            params["testcaseCategoryFilter"] = testcase_category_filter

        # Build the full URL with query string
        base_url = f"{self.__get_url_with_port()}/test-plan/esn/{esn}"
        query_string = urllib.parse.urlencode(params)
        full_url = f"{base_url}?{query_string}"

        resp = self.session.get(full_url, headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            self._raise_cli_exception("Failed to get test plan", e)
        return resp.json()

    def get_playlist_test_plan(self, playlist_id: str, esn: str):
        resp = self.session.get(f"{self.__get_url_with_port()}/playlist/id/{playlist_id}/esn/{esn}?format=marathonlite", headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            self._raise_cli_exception("Failed to get playlist test plan", e)
        return resp.json()

    def get_dynamic_filter_test_plan(self, dynamic_filter_id: str, esn: str, sdk_or_apk: str):
        sdk_or_apk_query_param = f"&singleNamespaceFilter={sdk_or_apk}" if sdk_or_apk else ""
        resp = self.session.get(f"{self.__get_url_with_port()}/dynamic-filter/id/{dynamic_filter_id}/esn/{esn}?format=marathonlite{sdk_or_apk_query_param}", headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            self._raise_cli_exception("Failed to get dynamic filter test plan", e)
        return resp.json()

    def get_status(self, rae: str, esn: str):
        query_params = f"rae={rae}" if rae is not None else f"esn={esn}"
        resp = self.session.get(f"{self.__get_url_with_port()}/device-status?{query_params}", headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            self._raise_cli_exception("Failed to get status", e)

        # Curate list of device attributes we expose to clients
        curated_fields = [
            "esn",
            "rae",
            "host",
            "status",
            "batchId"
        ]
        curated_devices = []
        for device in resp.json():
            if esn and device["esn"] != esn:
                continue  # Skip if not matching ESN

            # hydrate device with batchId


            device["batchId"] = None if device.get("status") == "idle" else self.__get_latest_running_batch_id(device['esn'])

            # Reduce to curated fields
            curated_device = {field: device.get(field) for field in curated_fields}
            curated_devices.append(curated_device)

        return curated_devices

    def __get_latest_running_batch_id(self, esn: str):
        batches = self.__get_all_batch_summaries(esn)
        if not batches:
            return None
        latest_batch = batches[0]
        # Return batchId if 'ended' key is missing (implying still running)
        return latest_batch["batchId"] if "ended" not in latest_batch else None

    def __get_all_batch_summaries(self, esn: str):
        resp = self.session.get(f"{self.__get_url_with_port()}/batch/summary/all?esn={esn}", headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            self._raise_cli_exception(f"Failed to get all batch summaries for esn: {esn}", e)
        return resp.json()

    def get_eleven_calibration_plan(self, esn: str):
        resp = self.session.get(f"{self.__get_url_with_port()}/eleven/calibration/esn/{esn}?format=marathonlite", headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            self._raise_cli_exception("Failed to get eleven calibration plan", e)
        return resp.json()

    def get_eyepatch_calibration_plan(self, esn: str, audio_source: str, eyepatch_serial: str):
        resp = self.session.get(f"{self.__get_url_with_port()}/eyepatch/calibration/esn/{esn}?format=marathonlite", headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            self._raise_cli_exception("Failed to get eyepatch calibration plan", e)
        plan = resp.json()
        plan["test_overrides"] = self.__get_eyepatch_calibration_plan_overrides(audio_source, eyepatch_serial)
        return plan

    def run_test_plan(self, plan, wait):
        overrides = { "test_log_level": "warning" }
        plan_overrides = plan.get("test_overrides", {})

        overrides.update(plan_overrides)
        #TODO: determine whether we should make these user configurable parameters
        plan["target_profiles"] = [ { "esn": plan["esn"] } ]
        plan["test_overrides"] = overrides
        plan["stress_count"] = 0
        plan["retry_count"] = 0

        resp = self.session.post(f"{self.__get_url_with_port()}/testruns/launch/nts/batch", json=plan, headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            self._raise_cli_exception("Failed to run test plan", e)

        batch_id = resp.json()["batch_id"]

        return self.get_run_plan_summary(batch_id, wait, True)

    def cancel_test_plan_run(self, batch_id: str, esn: str):
        json = { "esn" : esn }
        resp = self.session.post(f"{self.__get_url_with_port()}/testruns/cancel/batch/{batch_id}", json=json, headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            self._raise_cli_exception("Failed to cancel test plan run", e)
        return {
            "batchId": resp.json()["batch_id"],
            "details": resp.json()["details"]
        }

    def get_run_plan_summary(self, batch_id: str, wait: bool = False, include_attachments: bool = False):
        poll_interval = 20  # seconds
        inprogress_file = f"inprogress_test_plan_result_{batch_id}.json"

        while True:
            summary = self._get_run_plan_summary(batch_id, include_attachments)

            if not wait or summary["executionFinished"]:
                 # Delete inprogress file if it exists
                if os.path.exists(inprogress_file):
                    os.remove(inprogress_file)
                return summary

            # Write inprogress result to file
            with open(inprogress_file, "w") as f:
                json.dump(summary, f, indent=4)
            time.sleep(poll_interval)

    def get_testcases(self, esn: str, testcase_guids: List[str]):
        if not esn or not testcase_guids:
            return []

        testcase_request = {
            "esn": esn,
            "testcase_guids": testcase_guids
        }
        resp = self.session.post(f"{self.__get_url_with_port()}/testcase", json=testcase_request, headers=self.__get_headers())

        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            # Failing to fetch testcase metadata should not stop us from returning results
            logger.error(f"Failed to get testcase metadata : {e}")
            return []
        return resp.json()["data"]["testcases"]

    def get_test_execution_details(self, msid: str):
        # Check cache first
        if msid in self._exec_details_cache:
            logger.debug(f"Using cached execution details for markerSetId {msid}")
            return self._exec_details_cache[msid]
        resp = self.session.get(f"{self.__get_url_with_port()}/results/execDetails/markerSetId/{msid}", headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            self._raise_cli_exception(f"Failed to get execution details for markerSetId {msid}", e)

        result = resp.json()
        # Cache the result
        self._exec_details_cache[msid] = result
        return result

    # Returns the overall batch run summary
    def _get_run_plan_summary(self, batch_id: str, include_attachments: bool):
        resp = self.session.get(f"{self.__get_url_with_port()}/batch/results/batchId/{batch_id}", headers=self.__get_headers())
        self.__log_resp(resp)
        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            if resp.status_code == 404:
                logger.debug(f"Test plan run summary is not yet available for batchId {batch_id}")
                return { "batchId": batch_id, "executionFinished": False }
            else:
                self._raise_cli_exception(f"Failed to get test plan run summary for batchId {batch_id}", e)
        return self.__extract_cli_summary(resp.json(), include_attachments)

    # Raises appropriate NTS-CLI exception for HTTP error status code received from 3PG
    def _raise_cli_exception(self, error_message: str, http_error: exceptions.HTTPError):
        status_code = getattr(http_error.response, 'status_code', None)
        response_text = getattr(http_error.response, 'text', "")

        logger.error(f"{error_message} : {http_error}")

        unclaimed_device_msg = "Device must be claimed"
        reserved_device_msg = "Device has already been reserved"
        device_is_unavailable_msg = "Device is unavailable"

        if reserved_device_msg in response_text:
            raise DeviceAlreadyReservedException(error_message)
        elif unclaimed_device_msg in response_text:
            raise UnclaimedDeviceException(error_message)
        elif device_is_unavailable_msg in response_text:
            raise DeviceIsUnavailableException(error_message)
        elif status_code == 401:
            raise UnauthorizedException(error_message)
        elif status_code == 403:
            raise ForbiddenException(error_message)
        else:
            raise Exception(error_message)

    # Returns a collection of test results for an executed batch
    def _get_run_plan_results(self, batch_id: str, include_attachments: bool):
        next_token = None
        page_size = 100
        results = []
        total_items = None

        while True:
            payload = { "batchId": batch_id, "pageSize": page_size }
            if next_token is not None:
                payload["nextToken"] = next_token

            resp = self.session.post(f"{self.__get_url_with_port()}/results/summary/all", headers=self.__get_headers(), json=payload)
            self.__log_resp(resp)
            try:
                resp.raise_for_status()
            except exceptions.HTTPError as e:
                self._raise_cli_exception(f"Failed to get test plan run results for batchId {batch_id}", e)
            resp_json = resp.json()
            if total_items is None:
                total_items = resp_json.get("totalItems")
            results.extend(resp_json.get("data", []))
            next_token = resp_json.get("nextToken", None)
            if not next_token:
                break

        # Safety check
        if total_items is not None and len(results) != total_items:
            logger.warning(f"Expected {total_items} items, but got {len(results)}.")

        return self.__extract_cli_results(results, include_attachments)

    def __as_testcase_guid(self, version: str, name: str):
        return f"testcase/cloud/{version}/{name}.JavaScript"

    def __get_eyepatch_calibration_plan_overrides(self, audio_source, eyepatch_serial):
        overrides = {
            "promptChoice_audioSource": "positive",
            "promptInput_audioSource": audio_source.lower(),
            "skipPrompt": "true"
        }

        # Optional overrides
        if eyepatch_serial is not None:
            overrides["promptChoice_epchoice"] = "positive"
            overrides["promptInput_epchoice"] = eyepatch_serial

        return overrides

    def __get_url_with_port(self):
        return f"{self.url}:{self.port}"

    def __get_headers(self):
        return {
            self.auth_header: self.auth_value,
            "Content-Type": "application/json",
            # Wall-E overrides client.appId but not the user agent.
            "x-netflix.client.appid": "nts-cli",
            "User-Agent": f"nts-cli/{__version__.__version__}"
        }

    def __log_resp(self, resp):
        data = dump.dump_all(resp)
        logger.debug(data.decode("utf-8"))

    def __extract_cli_summary(self, results, include_attachments: bool):
        summary = results["summary"]
        batch_id = summary.get("batchId")
        finished = summary.get("pending") == 0 and summary.get("running") == 0
        test_results = self._get_run_plan_results(batch_id, include_attachments)

        return {
            "batchId": batch_id,
            # "resultUrl": f"https://nts.prod.netflixpartners.com/#batchhistory?{urllib.parse.urlencode({'runId': batch_id})}",
            "passed": summary.get("passed"),
            "failed": summary.get("failed"),
            "timedout": summary.get("timedout"),
            "canceled": summary.get("canceled"),
            "invalid": summary.get("invalid"),
            "running": summary.get("running"),
            "review": summary.get("review"),
            "pending": summary.get("pending"),
            "total": summary.get("total"),
            "executionFinished": finished,
            "testResultDetails": test_results
        }

    def __extract_cli_results(self, results, include_attachments: bool):
        esn = results[0]["esn"] if results else None
        testcase_guids = [
            self.__as_testcase_guid(
                entry["runtimeVersion"] if entry.get("runtimeVersion") else entry.get("sdkVersion"),
                entry["testCase"]
            )
            for entry in results
        ]

        testcases = self.get_testcases(esn, testcase_guids)
        testcases_map = {obj['name']: obj for obj in testcases}

        cli_results = []
        for item in results:
            result_dict = {
                "name": item["testCase"],
                "result": item["result"],
                "resultUrl": f"https://nts.prod.netflixpartners.com/#testhistory?{urllib.parse.urlencode({'markerSetId': item['markerSetId']})}",
                "failures": [] if item["result"] == "passed" else [item["result_message"]],
                "tags": testcases_map.get(item["testCase"], {}).get("tags", []),
                "category": testcases_map.get(item["testCase"], {}).get("category", None)
            }

            # Only fetch attachment details if requested
            if include_attachments:
                exec_details = self.get_test_execution_details(item['markerSetId'])
                attachments = exec_details.get("data", {}).get("attachments", [])

                # Find the ntscli.zip attachment URL
                attachments_url = None
                for attachment in attachments:
                    if attachment.get("key", "").endswith("_ntscli.zip"):
                        attachments_url = attachment.get("url")
                        break
                result_dict["attachmentsUrl"] = attachments_url

            cli_results.append(result_dict)

        return cli_results
