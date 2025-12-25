import json

from src.clients.device_test_client import DeviceTestClient

indent = 4

def run_impl(plan, wait, out_file, net_key: str, use_netflix_access: bool):
    device_test_client = DeviceTestClient(net_key, use_netflix_access)
    run_summary = device_test_client.run_test_plan(plan, wait)

    json.dump(run_summary, out_file, indent=indent)
