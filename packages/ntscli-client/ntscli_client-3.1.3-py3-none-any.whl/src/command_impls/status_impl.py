import json

from src.clients.device_test_client import DeviceTestClient

indent = 4

def status_impl(rae: str, esn: str, out_file, net_key: str, use_netflix_access: str):
    device_test_client = DeviceTestClient(net_key, use_netflix_access)
    status = device_test_client.get_status(rae, esn)

    json.dump(status, out_file, indent=indent)
