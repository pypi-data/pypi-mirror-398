#!/usr/bin/env python3
#  Copyright (c) 2025 Netflix.
#  All rights reserved.
#
import click
import json
import sys

from src import __version__

# Logger
import click_log
import logging
from src.clients.hardware_manager_client import HardwareManagerClient
from src.log import logger
click_log.basic_config(logger)

# Exceptions
from src.exceptions import MissingMetatronException, UnauthorizedException, ForbiddenException, UnclaimedDeviceException, DeviceAlreadyReservedException

# Command implementations
from src.command_impls.cancel_impl import cancel_impl
from src.command_impls.get_plan_impl import get_plan_impl
from src.command_impls.run_impl import run_impl
from src.command_impls.status_impl import status_impl
from src.command_impls.run_eyepatch_calibration_impl import run_eyepatch_calibration_impl
from src.command_impls.run_eleven_calibration_impl import run_eleven_calibration_impl
from src.command_impls.get_run_plan_summary_impl import get_run_plan_summary_impl

# CLI parameter help strings
RAE_HELP_STR = "The Netflix RAE device serial to connect to, such as r3010203. Defaults to environment variable 'RAE'."
ESN_HELP_STR = "The ESN of the target device. Defaults to environment variable 'ESN'"
BATCH_ID_HELP_STR = "UUID of a currently running test batch"
PLAN_TYPE_HELP_STR = "Type of plan to target, defaults to FULL"
PLAYLIST_ID_HELP_STR = "UUID of a playlist from https://nts.prod.netflixpartners.com/#playlist"
DYNAMIC_FILTER_ID_HELP_STR = "UUID of a dynamic filter from https://nts.prod.netflixpartners.com/#testing"
SDK_OR_APK_HELP_STR = "SDK or APK version to load all tests from a dynamic filter, ignoring device capabilities"
OUT_FILE_HELP_STR = "Saves output to the specified file"
RUN_WAIT_HELP_STR = "Waits until tests have finished executing, ensuring the command output reflects the final result"
PLAN_FILE_HELP_STR = "Test plan output file that will be used as input for executing tests"
NET_KEY_HELP_STR = "Netflix Edge Token used to provide authenticated external partners access. Defaults to environment variable 'NET_KEY'"
USE_NETFLIX_ACCESS_HELP_STR = "Flag to enable Netflix identity service for authenticated access. Defaults to environment variable 'USE_NETFLIX_ACCESS'"
VERBOSITY_HELP_STR = "[INTERNAL ONLY] Either CRITICAL, ERROR, WARNING, INFO or DEBUG"
OVERRIDE_HELP_STR = "Apply test plan override values as key=value pairs. Example: --override foo=bar --override baz=qux"
TESTCASE_AUTOMATION_FILTER_HELP_STR = "Comma-separated list of automation values to filter test cases. Allowed values: AUTOMATED, MANUAL, PERIPHERAL. Defaults to AUTOMATED,PERIPHERAL"
TESTCASE_STATE_FILTER_HELP_STR = "Comma-separated list of state values to filter test cases. Allowed values: ENABLED, MAINTENANCE. Defaults to ENABLED"
TESTCASE_NAME_FILTER_HELP_STR = "Filter tests returned in test plan based on regular expression wildcard * (e.g., SYNC*, PLAY*)"
TESTCASE_TAG_FILTER_HELP_STR = "Comma-separated list of tag values to filter test cases returned in a test plan."
TESTCASE_CATEGORY_FILTER_HELP_STR = "Comma-separated list of category values to filter test cases returned in a test plan."

# CLI choice options
SET_TOP_BOX = "set-top-box"
SMART_TV = "smart-tv"
ALLOWED_TESTCASE_AUTOMATIONS = {"AUTOMATED", "MANUAL", "PERIPHERAL"}
ALLOWED_TESTCASE_STATES = {"ENABLED", "MAINTENANCE"}

# CLI command precondition strings
PLAN_FILE_PARSE_FAILURE_STR = "Unable to open plan file"
PLAN_FILE_SIZE_FAILURE_STR = "The max test_case_guid size in your test plan file to execute is 2000"
REQUIRES_NET_KEY_OR_NETFLIX_ACCESS_STR = "At least one of --net-key or --use-netflix-access is required to authenticate requests"
REQUIRES_RAE_OR_ESN_STR = "At least one of --rae or --esn must be specified."
REQUIRES_PLAYLIST_ID_STR = "Must specify --playlist-id"
REQUIRES_DYNAMIC_FILTER_ID_STR = "Must specify --dynamic-filter-id"
REQUIRES_SMART_TV_TOPOLOGY_STR = f"Must specify --smart-tv-topology if --form-factor is {SMART_TV}"
REQUIRES_STB_TOPOLOGY_STR = f"Must specify --stb-topology if --form-factor is {SET_TOP_BOX}"

def validateUserAuthentication(net_key: str, use_netflix_access: bool):
    if net_key is None and not use_netflix_access:
        raise click.UsageError(REQUIRES_NET_KEY_OR_NETFLIX_ACCESS_STR)

def validateAutomationFilter(ctx, param, value):
    if value is None:
        return None
    choices = [v.strip().upper() for v in value.split(",") if v.strip()]
    invalid = [v for v in choices if v not in ALLOWED_TESTCASE_AUTOMATIONS]
    if invalid:
        raise click.BadParameter(f"Invalid values: {', '.join(invalid)}. Allowed values are: {', '.join(ALLOWED_TESTCASE_AUTOMATIONS)}")
    return value

def validateStateFilter(ctx, param, value):
    if value is None:
        return None
    choices = [v.strip().upper() for v in value.split(",") if v.strip()]
    invalid = [v for v in choices if v not in ALLOWED_TESTCASE_STATES]
    if invalid:
        raise click.BadParameter(f"Invalid values: {', '.join(invalid)}. Allowed values are: {', '.join(ALLOWED_TESTCASE_STATES)}")
    return value

def handle_exceptions(func):
    """Decorator to handle exceptions for Click commands."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (MissingMetatronException, UnauthorizedException, ForbiddenException, UnclaimedDeviceException, DeviceAlreadyReservedException) as e:
            raise click.ClickException(e)
        except Exception as e:
            click.echo(f"An error occurred: {e}", err=True)
    return wrapper

@click.group(name="default")
@click.version_option(
    __version__.__version__,
    message="%(prog)s, build %(version)s",
    prog_name="NTS-CLI"
)
@click_log.simple_verbosity_option(logger, help=VERBOSITY_HELP_STR)
def default():
    """
    NTS CLI

    Each command has its own --help option to show its usage.
    """
    try:
        from metatron.http import MetatronAdapter
    except ImportError:
        # Disable logs for users without internal extras installed
        logger.setLevel(logging.CRITICAL)
    pass

@default.command(name="cancel-running-plan", short_help="Cancel a running test plan")
@click.option(
    "--batch-id", "batch_id",
    type=str,
    required=True,
    help=BATCH_ID_HELP_STR)
@click.option(
    "--esn", "esn",
    type=str,
    required=True,
    help=ESN_HELP_STR,
)
@click.option(
    "-o", "out_file",
    type=click.File("w", encoding="utf-8"),
    help=OUT_FILE_HELP_STR,
    default=sys.stdout)
@click.option(
    "--net-key", "net_key",
    type=str,
    help=NET_KEY_HELP_STR,
    envvar="NET_KEY")
@click.option(
    "--use-netflix-access", "use_netflix_access",
    type=bool,
    is_flag=True,
    help=USE_NETFLIX_ACCESS_HELP_STR,
    envvar="USE_NETFLIX_ACCESS")
@handle_exceptions
def cancel(batch_id, esn, out_file, net_key: str, use_netflix_access: bool):
    """
    Cancel any test runs for a device.
    """
    validateUserAuthentication(net_key=net_key, use_netflix_access=use_netflix_access)
    cancel_impl(batch_id=batch_id, esn=esn, out_file=out_file, net_key=net_key, use_netflix_access=use_netflix_access)

@default.command(name="get-plan", short_help="Get a test plan")
@click.option(
    "--esn", "esn",
    type=str,
    required=True,
    help=ESN_HELP_STR,
    envvar="ESN")
@click.option(
    "--plan-type", "plan_type",
    type=click.Choice(["FULL", "PLAYLIST", "DYNAMIC_FILTER"]),
    required=True,
    help=PLAN_TYPE_HELP_STR)
@click.option(
    "--testcase-automation-filter", "testcase_automation_filter",
    type=str,
    callback=validateAutomationFilter,
    help=TESTCASE_AUTOMATION_FILTER_HELP_STR
)
@click.option(
    "--testcase-state-filter", "testcase_state_filter",
    type=str,
    callback=validateStateFilter,
    help=TESTCASE_STATE_FILTER_HELP_STR
)
@click.option(
    "--testcase-name-filter", "testcase_name_filter",
    type=str,
    help=TESTCASE_NAME_FILTER_HELP_STR
)
@click.option(
    "--testcase-tag-filter", "testcase_tag_filter",
    type=str,
    help=TESTCASE_TAG_FILTER_HELP_STR)
@click.option(
    "--testcase-category-filter", "testcase_category_filter",
    type=str,
    help=TESTCASE_CATEGORY_FILTER_HELP_STR)
@click.option(
    "--playlist-id", "playlist_id",
    type=str,
    help=PLAYLIST_ID_HELP_STR)
@click.option(
    "--dynamic-filter-id", "dynamic_filter_id",
    type=str,
    help=DYNAMIC_FILTER_ID_HELP_STR)
@click.option(
    "--sdk-or-apk", "sdk_or_apk",
    type=str,
    help=SDK_OR_APK_HELP_STR)
@click.option(
    "-o", "out_file",
    type=click.File("w", encoding="utf-8"),
    help=OUT_FILE_HELP_STR,
    default=sys.stdout)
@click.option(
    "--net-key", "net_key",
    type=str,
    help=NET_KEY_HELP_STR,
    envvar="NET_KEY")
@click.option(
    "--use-netflix-access", "use_netflix_access",
    type=bool,
    is_flag=True,
    help=USE_NETFLIX_ACCESS_HELP_STR,
    envvar="USE_NETFLIX_ACCESS")
@handle_exceptions
def get_plan_from_device(
    esn: str,
    plan_type: str,
    testcase_automation_filter: str,
    testcase_state_filter: str,
    testcase_name_filter: str,
    testcase_tag_filter: str,
    testcase_category_filter: str,
    playlist_id: str,
    dynamic_filter_id: str,
    sdk_or_apk: str,
    out_file,
    net_key: str,
    use_netflix_access: bool
):
    """
    Command to get test plans of various types for a device
    """
    validateUserAuthentication(net_key=net_key, use_netflix_access=use_netflix_access)
    match plan_type:
        case "PLAYLIST":
            if playlist_id is None: raise click.UsageError(REQUIRES_PLAYLIST_ID_STR)
        case "DYNAMIC_FILTER":
            if dynamic_filter_id is None: raise click.UsageError(REQUIRES_DYNAMIC_FILTER_ID_STR)

    get_plan_impl(
        esn=esn,
        plan_type=plan_type,
        testcase_automation_filter=testcase_automation_filter,
        testcase_state_filter=testcase_state_filter,
        testcase_name_filter=testcase_name_filter,
        testcase_tag_filter=testcase_tag_filter,
        testcase_category_filter=testcase_category_filter,
        playlist_id=playlist_id,
        dynamic_filter_id=dynamic_filter_id,
        sdk_or_apk=sdk_or_apk,
        out_file=out_file,
        net_key=net_key,
        use_netflix_access=use_netflix_access
    )

@default.command(name="run-plan", short_help="Run a test plan")
@click.option(
    "--plan-file", "plan_file",
    type=click.File("r", encoding="utf-8"),
    required=True,
    help=PLAN_FILE_HELP_STR)
@click.option(
    "--override",
    multiple=True,
    help=OVERRIDE_HELP_STR)
@click.option(
    "--wait",
    type=bool,
    is_flag=True,
    help=RUN_WAIT_HELP_STR)
@click.option(
    "-o", "out_file",
    type=click.File("w", encoding="utf-8"),
    help=OUT_FILE_HELP_STR,
    default=sys.stdout)
@click.option(
    "--net-key", "net_key",
    type=str,
    help=NET_KEY_HELP_STR,
    envvar="NET_KEY")
@click.option(
    "--use-netflix-access", "use_netflix_access",
    type=bool,
    is_flag=True,
    help=USE_NETFLIX_ACCESS_HELP_STR,
    envvar="USE_NETFLIX_ACCESS")
@handle_exceptions
def run(plan_file, override, wait, out_file, net_key: str, use_netflix_access: bool):
    """
    Command to run an input test plan file
    """
    validateUserAuthentication(net_key=net_key, use_netflix_access=use_netflix_access)
    overrides = dict(item.split("=", 1) for item in override)
    try:
        plan = json.load(plan_file)
    except Exception as e:
        logger.error(f"Failed to open plan file {e}")
        raise click.UsageError(PLAN_FILE_PARSE_FAILURE_STR)
    if len(plan["test_case_guids"]) > 2000:
        raise click.UsageError(PLAN_FILE_SIZE_FAILURE_STR)

    # Set overrides in the plan
    plan["test_overrides"] = overrides

    run_impl(plan=plan, wait=wait, out_file=out_file, net_key=net_key, use_netflix_access=use_netflix_access)

@default.command(
    name="get-device-status",
    short_help="Get device status"
)
@click.option(
    "--rae",
    type=str,
    help=RAE_HELP_STR,
    envvar="RAE"
)
@click.option(
    "--esn", "esn",
    type=str,
    help=ESN_HELP_STR,
    envvar="ESN")
@click.option(
    "-o", "out_file",
    type=click.File("w", encoding="utf-8"),
    help=OUT_FILE_HELP_STR,
    default=sys.stdout)
@click.option(
    "--net-key", "net_key",
    type=str,
    help=NET_KEY_HELP_STR,
    envvar="NET_KEY")
@click.option(
    "--use-netflix-access", "use_netflix_access",
    type=bool,
    is_flag=True,
    help=USE_NETFLIX_ACCESS_HELP_STR,
    envvar="USE_NETFLIX_ACCESS")
@handle_exceptions
def status(rae: str, esn: str, out_file, net_key: str, use_netflix_access: bool):
    """
    Command to get device metadata.
    This includes information about the state of any test plans being run for the device.
    """
    validateUserAuthentication(net_key=net_key, use_netflix_access=use_netflix_access)
    if not any([rae, esn]):
        raise click.UsageError(REQUIRES_RAE_OR_ESN_STR)
    status_impl(rae=rae, esn=esn, out_file=out_file, net_key=net_key, use_netflix_access=use_netflix_access)

@default.command(name="run-eyepatch-calibration-plan", short_help="Get the eyepatch calibration plan for a device and run it")
@click.option(
    "--esn", "esn",
    type=str,
    required=True,
    help=ESN_HELP_STR,
    envvar="ESN")
@click.option(
    "--form-factor", "form_factor",
    required=False,
    type=click.Choice([SET_TOP_BOX, SMART_TV]),
    help="[DEPRECATED] This option is no longer used and will be removed in future versions."
)
@click.option(
    "--smart-tv-topology", "smart_tv_topology",
    type=click.Choice(["TV", "TV->AVR"]),
    help="[DEPRECATED] This option is no longer used and will be removed in future versions."
)
@click.option(
    "--stb-topology", "stb_topology",
    type=click.Choice(["STB->TV", "STB->AVR->TV"]),
    help="[DEPRECATED] This option is no longer used and will be removed in future versions."
)
@click.option(
    "--audio-source", "audio_source",
    required=True,
    type=click.Choice(["line-in", "contact-mic", "magnetic-mic", "spdif", "arc", "earc"]),
    help="Audio transport to capture & analyze audio"
)
@click.option(
    "--audio-mode", "audio_mode",
    required=False,
    type=click.Choice(["PASSTHROUGH", "ATMOS", "DDP51", "PCM", "DOLBYMAT"]),
    help="[DEPRECATED] This option is no longer used and will be removed in future versions.",
)
@click.option(
    "--eyepatch-serial", "eyepatch_serial",
    type=str,
    help="The serial number of the eyepatch to be used."
)
@click.option(
    "-o", "out_file",
    type=click.File("w", encoding="utf-8"),
    help=OUT_FILE_HELP_STR,
    default=sys.stdout)
@click.option(
    "--net-key", "net_key",
    type=str,
    help=NET_KEY_HELP_STR,
    envvar="NET_KEY")
@click.option(
    "--use-netflix-access", "use_netflix_access",
    type=bool,
    is_flag=True,
    help=USE_NETFLIX_ACCESS_HELP_STR,
    envvar="USE_NETFLIX_ACCESS")
@handle_exceptions
def run_eyepatch_calibration_plan(esn: str, form_factor: str, smart_tv_topology: str, stb_topology: str, audio_source: str, audio_mode: str, eyepatch_serial: str, out_file, net_key: str, use_netflix_access: bool):
    """
    Command to get the eyepatch calibration test plan for a device and run it
    """
    validateUserAuthentication(net_key=net_key, use_netflix_access=use_netflix_access)
    if form_factor is not None:
        click.echo("Warning: --form-factor is deprecated and will be ignored.", err=True)
    if smart_tv_topology is not None:
        click.echo("Warning: --smart-tv-topology is deprecated and will be ignored.", err=True)
    if stb_topology is not None:
        click.echo("Warning: --stb-topology is deprecated and will be ignored.", err=True)
    if audio_mode is not None:
        click.echo("Warning: --audio-mode is deprecated and will be ignored.", err=True)

    run_eyepatch_calibration_impl(esn=esn, audio_source=audio_source, eyepatch_serial=eyepatch_serial, out_file=out_file, net_key=net_key, use_netflix_access=use_netflix_access)

@default.command(name="run-eleven-calibration-plan", short_help="Get the eleven calibration plan for a device and run it")
@click.option(
    "--esn", "esn",
    type=str,
    required=True,
    help=ESN_HELP_STR,
    envvar="ESN")
@click.option(
    "-o", "out_file",
    type=click.File("w", encoding="utf-8"),
    help=OUT_FILE_HELP_STR,
    default=sys.stdout)
@click.option(
    "--net-key", "net_key",
    type=str,
    help=NET_KEY_HELP_STR,
    envvar="NET_KEY")
@click.option(
    "--use-netflix-access", "use_netflix_access",
    type=bool,
    is_flag=True,
    help=USE_NETFLIX_ACCESS_HELP_STR,
    envvar="USE_NETFLIX_ACCESS")
@handle_exceptions
def run_eleven_calibration_plan(esn: str, out_file, net_key: str, use_netflix_access: bool):
    """
    Command to get the eleven calibration test plan for a device and run it
    """
    validateUserAuthentication(net_key=net_key, use_netflix_access=use_netflix_access)
    run_eleven_calibration_impl(esn=esn, out_file=out_file, net_key=net_key, use_netflix_access=use_netflix_access)

@default.command(name="get-run-plan-summary", short_help="Get a summary for a test plan you have run")
@click.option(
    "--batch-id", "batch_id",
    type=str,
    required=True,
    help=BATCH_ID_HELP_STR,
    envvar="ESN")
@click.option(
    "--include-attachments", "include_attachments",
    type=bool,
    is_flag=True,
    help="Include attachment URLs in the test result details")
@click.option(
    "-o", "out_file",
    type=click.File("w", encoding="utf-8"),
    help=OUT_FILE_HELP_STR,
    default=sys.stdout)
@click.option(
    "--net-key", "net_key",
    type=str,
    help=NET_KEY_HELP_STR,
    envvar="NET_KEY")
@click.option(
    "--use-netflix-access", "use_netflix_access",
    type=bool,
    is_flag=True,
    help=USE_NETFLIX_ACCESS_HELP_STR,
    envvar="USE_NETFLIX_ACCESS")
@handle_exceptions
def get_run_plan_summary(batch_id: str, include_attachments: bool, out_file, net_key: str, use_netflix_access: bool):
    """
    Command to get a summary for a test plan you have run
    """
    validateUserAuthentication(net_key=net_key, use_netflix_access=use_netflix_access)
    get_run_plan_summary_impl(batch_id=batch_id, include_attachments=include_attachments, out_file=out_file, net_key=net_key, use_netflix_access=use_netflix_access)

@default.command(
    name="get-host-devices",
    short_help="Get the available devices for a host"
)
@click.option(
    "--rae",
    type=str,
    help=RAE_HELP_STR,
    envvar="RAE",
    required=True
)
@click.option(
    "--net-key", "net_key",
    type=str,
    help=NET_KEY_HELP_STR,
    envvar="NET_KEY")
@click.option(
    "--use-netflix-access", "use_netflix_access",
    type=bool,
    is_flag=True,
    help=USE_NETFLIX_ACCESS_HELP_STR,
    envvar="USE_NETFLIX_ACCESS")
@handle_exceptions
def get_host_devices(rae: str, net_key: str, use_netflix_access: bool):
    """
    Command to get devices behind a host
    """
    validateUserAuthentication(net_key=net_key, use_netflix_access=use_netflix_access)
    hwm_client = HardwareManagerClient(net_key, use_netflix_access)
    devices = hwm_client.get_devices_for_host(rae)
    print(json.dumps(devices, indent=4))

@default.command(
    name="set-device-ui",
    short_help="set the UI mode for a device"
)
@click.option(
    "--rae",
    type=str,
    help=RAE_HELP_STR,
    envvar="RAE",
    required=True
)
@click.option(
    "--ip",
    type=str,
    help="IP address of the device to set the UI mode for",
    envvar="IP",
    required=True
)
@click.option(
    "--env",
    # type=str,
    help="UI environment to set for the device, such as 'test' or 'prod'",
    type=click.Choice(["test", "prod"]),
    envvar="DEVICE_ENV",
    required=True
)
@click.option(
    "--net-key", "net_key",
    type=str,
    help=NET_KEY_HELP_STR,
    envvar="NET_KEY")
@click.option(
    "--use-netflix-access", "use_netflix_access",
    type=bool,
    is_flag=True,
    help=USE_NETFLIX_ACCESS_HELP_STR,
    envvar="USE_NETFLIX_ACCESS")
@handle_exceptions
def set_device_ui(rae: str, ip: str, env: str, net_key: str, use_netflix_access: bool):
    """
    Command to set the device UI mode for a device behind a host.
    """
    validateUserAuthentication(net_key=net_key, use_netflix_access=use_netflix_access)
    hwm_client = HardwareManagerClient(net_key, use_netflix_access)
    devices = hwm_client.set_device_ui(rae, ip, env)
    print(json.dumps(devices, indent=4))

@default.command(
    name="get-nts-cli-dockerfile",
    short_help="Generates a Dockerfile for creating a Docker image with the NTS CLI client."
)
@click.option(
    "-o", "out_file",
    type=click.File("w", encoding="utf-8"),
    help=OUT_FILE_HELP_STR,
    default=sys.stdout)
@handle_exceptions
def get_nts_cli_dockerfile(out_file):
    """
    Command to get a NTS CLI Dockerfile
    """
    dockerfile_content = """\
FROM python:3.10-slim-bullseye

RUN apt-get update && \\
    apt-get upgrade -y && \\
    apt-get install -y bash && \\
    rm -rf /var/lib/apt/lists/*

RUN pip3 install 'ntscli-client>=3.0.0,<4.0.0'

WORKDIR /ntscli

CMD ["/bin/sh"]
"""
    out_file.write(dockerfile_content)

if __name__ == "__main__":
    default()
