import json

from src.clients.device_test_client import DeviceTestClient

indent = 4

def get_run_plan_summary_impl(batch_id: str, include_attachments: bool, out_file, net_key: str, use_netflix_access: bool):
    device_test_client = DeviceTestClient(net_key, use_netflix_access)
    run_plan_summary = device_test_client.get_run_plan_summary(batch_id, wait=False, include_attachments=include_attachments)

    json.dump(run_plan_summary, out_file, indent=indent)
