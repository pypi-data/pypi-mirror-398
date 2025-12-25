import json

from src.clients.device_test_client import DeviceTestClient

indent = 4

def cancel_impl(batch_id: str, esn: str, out_file, net_key: str, use_netflix_access: bool):
    device_test_client = DeviceTestClient(net_key, use_netflix_access)
    cancel_plan_run_result = device_test_client.cancel_test_plan_run(batch_id, esn)

    json.dump(cancel_plan_run_result, out_file, indent=indent)
